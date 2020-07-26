from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, create_engine
from flask_sqlalchemy import SQLAlchemy
import json
import os

database_path = os.environ['DATABASE_URL']

db = SQLAlchemy()

def setup_db(app, database_path=database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()

class DatabaseCRUD(db.Model):
    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

class Movie(DatabaseCRUD):
    __tablename__ = 'Movie'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    movie_category_id = Column(Integer)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, name, description, movie_category_id):
        self.name = name
        self.description = description
        self.movie_category_id = movie_category_id

    def format(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'movie_category_id': self.movie_category_id
        }

class Actor(DatabaseCRUD):
    __tablename__ = 'Actor'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def format(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age
        }

class MovieCategory(DatabaseCRUD):
    __tablename__ = 'Movie_Category'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, name):
        self.name = name

    def format(self):
        return {
            'id': self.id,
            'name': self.name
        }

class MovieActorAssign(DatabaseCRUD):
    __tablename__ = 'Movie_Actor_Assign'

    id = Column(Integer, primary_key=True)
    movie_id = db.Column(Integer, ForeignKey('Movie.id', ondelete="CASCADE"))
    actor_id = db.Column(Integer, ForeignKey('Actor.id', ondelete='CASCADE'))
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, movie_id, actor_id):
        self.movie_id = movie_id
        self.actor_id = actor_id

    def format(self):
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'actor_id': self.actor_id
        }