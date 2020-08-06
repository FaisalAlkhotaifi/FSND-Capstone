import os
import sys
from datetime import datetime
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from database.models import db_drop_and_create_all, setup_db, Movie, Actor, MovieCategory, MovieActorAssign
from auth.auth import AuthError, requires_auth

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers',
                          'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods',
                          'GET,PATCH,POST,DELETE,OPTIONS')
    return response

  '''
  @TODO uncomment the following line to initialize the datbase
  !! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
  !! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
  '''
  #db_drop_and_create_all()

  @app.route('/')
  def hello():
    return "Welcome to Casting Agency API!"

  # Movie Endpoints

  @app.route('/movie')
  def getMovies():
    movies = Movie.query.order_by(Movie.date_updated).all()
    movies_formatted = []

    if movies is not None and len(movies) != 0:
      for movie in movies:
        category = MovieCategory.query.filter_by(id=movie.movie_category_id).one_or_none()
        category_formatted = {}

        if category is not None:
          category_formatted = category.format()

        single_movie = {
          'movie_details': movie.format(),
          'movie_category': category_formatted
        }
        movie_actors_assign = MovieActorAssign.query.filter_by(movie_id=movie.id).all()

        if movie_actors_assign is not None and len(movie_actors_assign) != 0:
          actors_id = [movie_actor_assign.actor_id for movie_actor_assign in movie_actors_assign]

          actors = Actor.query.filter(Actor.id.in_(actors_id)).order_by(Actor.date_updated).all()
          single_movie['actors'] = [actor.format() for actor in actors]
        
        movies_formatted.append(single_movie)

    return jsonify({
      'success': True,
      'movies': movies_formatted
    })

  @app.route('/movie', methods=['POST'])
  def addMovie():
    body = request.get_json()

    try:
      name = body.get('name', None)
      desc = body.get('description', None)
      movie_category_id = body.get('movie_category_id', None)

      # Check of any missing parameter.
      if name is None or desc is None or movie_category_id is None:
        abort(400)

      movie = Movie(
        name=name, 
        description=desc, 
        movie_category_id=movie_category_id
      )
      movie.insert()

      # it is a list of actors id that is assigned to the added movie
      actors_id = body.get('actors_id', None)

      if actors_id is not None and type(actors_id) is list:
        # adding each actor to MovieActorAssign table
        for actor_id in actors_id:
          movie_actor_assign = MovieActorAssign(
            movie_id=movie.id, 
            actor_id=actor_id
          )
          movie_actor_assign.insert()

      return jsonify({
        'success': True,
        'movie_added': movie.format()
      })
    except Exception as e:
      abort(422)

  @app.route('/movie/<movie_id>', methods=['PATCH'])
  def updateMovie(movie_id):
    movie = Movie.query.filter_by(id=movie_id).one_or_none()
    if movie is None:
      abort(404)

    body = request.get_json()
    name = body.get('name', None)
    description = body.get('description', None)
    movie_category_id = body.get('movie_category_id', None)
    actors_id = body.get('actors_id', None)

    movie_update = {}

    # Check that at least there is one parameter to be updated
    if name is None \
      and description is None \
      and movie_category_ids is None \
      and actors_id is None:
        abort(400)

    try:
      # only update the provided parameter
      if name is not None:
        movie.name = name
      if description is not None:
        movie.description = description
      if movie_category_id is not None:
        movie.movie_category_id = movie_category_id

      movie.update()

      movie_update['movie_details'] = movie.format()

      if actors_id is not None \
         and type(actors_id) is list:
            MovieActorAssign.query.filter_by(
              movie_id=movie.id
            ).delete()

        # delete the previous record of actors that assigned to 
        # the update movie and then added the new ones
        for actor_id in actors_id:
          movie_actor_assign = MovieActorAssign(
            movie_id=movie.id, 
            actor_id=actor_id
          )
          movie_actor_assign.insert()

        actors = Actor.query.filter(Actor.id.in_(actors_id)).order_by(Actor.date_updated).all()
        movie_update['actors'] = [actor.format() for actor in actors]

      return jsonify({
        'success': True,
        'movie_update': movie_update
      })
    except Exception as e:
      print(sys.exc_info())
      abort(422)

  @app.route('/movie/<movie_id>', methods=['DELETE'])
  def deleteMovie(movie_id):
    movie = Movie.query \
            .filter_by(id=movie_id) \
            .one_or_none()

    if movie is None:
        abort(404)

    try:
      movie.delete()
      
      # deleting actors that assign to movie along with deleting the movie record
      movie_actors_assign = MovieActorAssign.query.filter_by(
        movie_id=movie_id
      ).all()
      if movie_actors_assign is not None:
        for actor_assign in movie_actors_assign:
          actor_assign.delete()

      return jsonify({
          "success": True,
          "delete": movie_id
      })
    except Exception as e:
      abort(422)
  
  # Actor Endpoints

  @app.route('/actor')
  def getActor():
    actors = Actor.query.order_by(Actor.date_updated).all()
    actors_formatted = [actor.format() for actor in actors]

    return jsonify({
      'success': True,
      'actors': actors_formatted
    })

  @app.route('/actor', methods=['POST'])
  def addActor():
    body = request.get_json()

    try:
      name = body.get('name', None)
      age = body.get('age', None)

      # Check of any missing parameter.
      if name is None or age is None:
        abort(400)
      
      actor = Actor(name=name, age=age)
      actor.insert()

      return jsonify({
        'success': True,
        'actor_added': actor.format()
      })
    except Exception as e:
      abort(422)

  @app.route('/actor/<actor_id>', methods=['PATCH'])
  def updateActor(actor_id):
    actor = Actor.query.filter_by(id=actor_id).one_or_none()
    if actor is None:
      abort(404)

    body = request.get_json()
    name = body.get('name', None)
    age = body.get('age', None)

    # Check that at least there is one parameter to be updated
    if name is None and age is None:
      abort(400)

    try:
      # only update the provided parameter
      if name is not None:
        actor.name = name
      if age is not None:
        actor.age = age
      actor.update()

      return jsonify({
        'success': True,
        'actor_update': actor.format()
      })
    except Exception as e:
      abort(422)
  
  @app.route('/actor/<actor_id>', methods=['DELETE'])
  def deleteActor(actor_id):
    actor = Actor.query \
            .filter_by(id=actor_id) \
            .one_or_none()

    if actor is None:
        abort(404)

    try:
        actor.delete()

        return jsonify({
            "success": True,
            "delete": actor_id
        })
    except Exception as e:
        abort(422)

  # Movie Category Endpoints

  @app.route('/movieCategory')
  def getMovieCategory():
    movie_categories = MovieCategory.query.order_by(MovieCategory.date_updated).all()
    movie_categories_formatted = [movie_category.format() for movie_category in movie_categories]

    return jsonify({
      'success': True,
      'movie_categories': movie_categories_formatted
    })

  @app.route('/movieCategory', methods=['POST'])
  def addMovieCategory():
    body = request.get_json()

    try:
      name = body.get('name', None)

      # Check of any missing parameter.
      if name is None:
        abort(400)
      
      movie_category = MovieCategory(name=name)
      movie_category.insert()

      return jsonify({
        'success': True,
        'movie_category_added': movie_category.format()
      })
    except Exception as e:
      abort(422)

  @app.route('/movieCategory/<movie_category_id>', methods=['PATCH'])
  def updateMovieCategory(movie_category_id):
    movie_category = MovieCategory.query.filter_by(id=movie_category_id).one_or_none()
    if movie_category is None:
      abort(404)

    body = request.get_json()
    name = body.get('name', None)

    # Check of missing name
    if name is None:
      abort(400)

    try:
      movie_category.name = name
      movie_category.update()

      return jsonify({
        'success': True,
        'movie_category_update': movie_category.format()
      })
    except Exception as e:
      abort(422)

  @app.route('/movieCategory/<movie_category_id>', methods=['DELETE'])
  def deleteMovieCategory(movie_category_id):
    movie_category = MovieCategory.query \
            .filter_by(id=movie_category_id) \
            .one_or_none()

    if movie_category is None:
        abort(404)

    try:
        movie_category.delete()

        return jsonify({
            "success": True,
            "delete": movie_category_id
        })
    except Exception as e:
        abort(422)

  # Error Handling

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
          "success": False,
          "error": 422,
          "message": "unprocessable"
      }), 422

  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          "success": False,
          "error": 404,
          "message": "resource not found"
      }), 404

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          "success": False,
          "error": 400,
          "message": "bad request"
      }), 400

  @app.errorhandler(401)
  def not_authorize(error):
      return jsonify({
          "success": False,
          "error": 401,
          "message": "unathurize user"
      }), 401

  @app.errorhandler(403)
  def insufficient_permission(error):
      return jsonify({
          "success": False,
          "error": 403,
          "message": "insufficient permission"
      }), 403

  return app

APP = create_app()

if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=8080, debug=True)