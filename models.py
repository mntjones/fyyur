from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))

  genres = db.Column(db.ARRAY(db.String(120)))

  facebook_link = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  website = db.Column(db.String(500))
    
  seeking_talent = db.Column(db.Boolean(), default=True)
  seeking_description = db.Column(db.String(500))

  shows = db.relationship('Show', backref='Venue', lazy=True)

  def __repr__(self):
    return f'<Venue {self.id} name: {self.name}>'
    

class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))

  genres = db.Column(db.ARRAY(db.String(120)))

  facebook_link = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  website = db.Column(db.String(500))
    
  seeking_venue = db.Column(db.Boolean(), default=True)
  seeking_description = db.Column(db.String(120))

  shows = db.relationship('Show', backref='Artist', lazy=True)

  def __repr__(self):
    return f'<Artist {self.id} name: {self.name}>'

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime(timezone=True), nullable=False)

with app.app_context():
  db.create_all()
