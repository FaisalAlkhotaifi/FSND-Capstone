import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'falkhotaifi.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'caffeaShopService'

# AuthError Exception

'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

# Getting Bearer token from request header
def get_token_auth_header():
    headers = request.headers
    auth_key_header = 'Authorization'
    auth_type = 'bearer'

    if auth_key_header not in headers:
        abort(401)

    header_auth = headers[auth_key_header]
    auth_parts = header_auth.split(' ')

    if len(auth_parts) != 2:
        abort(401)
    elif auth_parts[0].lower() != auth_type:
        abort(401)

    return auth_parts[1]

'''
Validate user permission obtain from payload
that meets endpoint permission
'''


def check_permissions(permission, payload):
    permission_key = 'permissions'

    if permission_key not in payload:
        abort(400)

    if permission not in payload[permission_key]:
        abort(401)

    return True


# To extract payload from JWT token
def verify_decode_jwt(token):
    # CREDIT to udacity FULL STACK COURSE tutorial
    jsonUrl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonUrl.read())

    unverified_header = jwt.get_unverified_header(token)

    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            print("error: Token expired.")
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            print(
                "error: Incorrect claims. ",
                "Please, check the audience and issuer."
            )

            error_desc = 'Incorrect claims.'
            error_suggestion = 'Please, check the audience and issuer.'

            raise AuthError({
                'code': 'invalid_claims',
                'description': f'{error_desc} {error_suggestion}'
            }, 401)
        except Exception:
            print("error: Unable to parse authentication token.")
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    print("error: Unable to find the appropriate key.")
    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)

    raise Exception('Not Implemented')


def get_payload(token):
    try:
        return verify_decode_jwt(token)
    except:
        abort(401)


# Check auth decorator for end points
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = get_payload(token)
            check_permissions(permission, payload)

            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator
