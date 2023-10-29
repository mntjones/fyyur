#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import collections
import collections.abc
import datetime

from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form

import logging
from logging import Formatter, FileHandler
from forms import *
from datetime import datetime

import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)


migrate = Migrate(app,db)
collections.Callable = collections.abc.Callable

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
  website_link = db.Column(db.String(500))

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
  website_link = db.Column(db.String(500))

  seeking_venues = db.Column(db.Boolean(), default=True)
  seeking_description = db.Column(db.String(120))

  shows = db.relationship('Show', backref='Artist', lazy=True)

  def __repr__(self):
    return f'<Artist {self.id} name: {self.name}>'

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer(), db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer(), db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime(timezone=True), nullable=False)

with app.app_context():
  db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  cities = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  venue_data=[]
  current_time = datetime.now()

  for city in cities:
    # for each city, state - filtering the venues in that city
    venues = db.session.query(Venue.id, Venue.name).filter(Venue.city == city[0]).filter(Venue.state == city[1]).all()
    for venue in venues:
      # shows filtered using current time to determine upcoming shows
      num_upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()       
      # add venue data
      venue_data.append({
        "city": venue.city,
        "state": venue.state,
        "venues": [{
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(num_upcoming_shows)}]
          })

  return render_template('pages/venues.html', areas=venue_data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # get search term from form
  search_term = request.form.get('search_term', '')
  #searching for search term in db
  venues = db.session.query(Venue).filter(Venue.name.ilike('%' + search_term + '%')).all()
  matching_venues = []

  for venue in venues:
    num_upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
    
    matching_venues.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows
      })

  response = {
    "count": len(venues),
    "matching_venues": matching_venues
  }
    
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
  #list of shows for venue that matches passed venue_id
  shows = db.session.query(Show).filter(Show.venue_id ==venue_id)

  past_shows = []
  upcoming_shows = []
  current_time = datetime.now()

  # get show data and either add to past show data or upcoming show data based on sow time
  for show in shows:
    show_data = {
      "artist_id": show.artist_id,
      "artist_name": show.artist_name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    }

    if show.start_time <= current_time:
      past_shows.append(show_data)
    else:
      upcoming_shows.append(show_data)

  if venue:
    venue_data = {
      "id": venue_id,
      "name": venue.name,
      "genres": [genre.name for genre in venue.genres],
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website_link,
      "facebook": venue.facebook_link,
      "seeking talent?": venue.seeking_talent,
      "seeking description": venue.seeking_description,
      "image link": venue.image_link,
      "past shows": past_shows,
      "past show count": len(past_shows),
      "upcoming shows": upcoming_shows,
      "upcoming show count": len(upcoming_shows)
    }

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  #getting data from form
  form = VenueForm(request.form)

  #creating a new venue to add to db
  venue = Venue(
    name = form.name.data,
    genres = form.genres.data,
    address = form.address.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    website = form.website.data,
    facebook_link = form.facebook_link.data,
    seeking_talent = form.seeking_talent.data,
    seeking_description = form.seeking_description.data,
    image_link = form.image_link.data
  )

  try:
    db.session.add(venue)
    db.session.commit()

    # if add successful, flash message
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:

    db.session.query(Venue).filter(Venue.id == venue_id).delete()
    db.session.commit()
    flash('Venue ID: ' + venue_id + ' was successfully deleted!')

  except:
    flash('An error occurred. Venue ID: ' + venue_id + ' could not be deleted.')

  finally:
    db.session.close()

  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = db.session.query(Artist.id, Artist.name)
  artist_data = []

  for artist in artists:
    artist_data.append({
      "id": artist.id,
      "name": artist.name
    })

  return render_template('pages/artists.html', artists=artist_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search = request.form.get('search_term', '')
  # formatting to get case insensitive search
  search_term = "%{}%".format(search.lower())
  artists = db.session.query(Artist).filter(Artist.name.ilike(search_term)).all()

  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

# shows the artist page with the given artist_id
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  # get data for artist
  artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
  current_time = datetime.now()
  artist_data = {}
  upcoming_shows = []
  past_shows = []

  #get show info for artist
  for info in artist:
    upcoming_shows = info.shows.filter(Show.start_time > current_time).all()
    past_shows = info.shows.filter(Show.start_time <= current_time).all()


  artist_data = {
    "id": artist_id,
    "name": artist.name,
    "genres": [genre.name for genre in artist.genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  form.name.data = artist.name
  form.genres.data = [genre.name for genre in artist.genres]
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  form = ArtistForm(request.form)
  artist = db.session.query(Artist).filter(Artist.id == artist_id).one()

 # update fields of artist using form fields
  try:
    artist.name: form.name.data,
    artist.genres: ', '.join(form.data.getlist('genres'))
    artist.address: form.address.data,
    artist.city: form.city.data,
    artist.state: form.state.data,
    artist.phone: form.phone.data,
    artist.website_link: form.website.data,
    artist.facebook_link: form.facebook_link.data,
    artist.seeking_venue: form.seeking_venue.data,
    artist.seeking_description: form.seeking_description.data,
    artist.image_link: form.image_link.data

    db.session.update(artist)
    db.session.commit()

    flash('Artist ID: ' + artist_id + ' successfully updated.')

  except:
    db.session.rollback()
    flash('An error occurred. Artist ID: ' + artist_id + ' could not be updated.')

  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_info = db.session.query(Venue).filter(Venue.id==venue_id).one()

  venue={
    "id": venue_info.id,
    "name": venue_info.name,
    "genres": venue_info.genres.split(", "),
    "address": venue_info.address,
    "city": venue_info.city,
    "state": venue_info.state,
    "phone": venue_info.phone,
    "website": venue_info.website_link,
    "facebook_link": venue_info.facebook_link,
    "seeking_talent": venue_info.seeking_talent,
    "seeking_description": venue_info.seeking_description,
    "image_link": venue_info.image_link
  }

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  try:
    venue = Venue.query.get(venue_id)

    venue.name = request.form.get('name')
    venue.genres = ', '.join(request.form.getlist('genres'))
    venue.address = request.form.get('address')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.phone = request.form.get('phone')
    venue.facebook_link = request.form.get('facebook_link')
    venue.image_link = request.form.get('image_link')
    venue.website = request.form.get('website_link')
    venue.seeking_talent = request.form.get('seeking_talent')
    venue.seeking_description = request.form.get('seeking_description')

    db.session.add(venue)
    db.session.commit()

  except:
    db.session.rollback()
    flash('An error occurred. Venue ID: ' + venue_id + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm(request.form)
  try:
    artist = Artist()
    artist.name = form.name.data
    artist.genres = ', '.join(form.getlist('genres'))
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.website_link = form.website.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data
    
    db.session.add(artist)
    db.session.commit()

    flash('Artist: ' + request.form['name'] + ' was successfully created.')

  except:
    db.session.rollback()
    flash('Artist: ' + request.form['name'] + ' was not created - ERROR')

  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''


# Troubleshooting

'''
Error:
ImportError: cannot import name 'Markup' from 'jinja2' 
(/Users/monica/cd0037-API-Development-and-Documentation-exercises/1_Requests_Starter/venv/lib/python3.11/site-packages/jinja2/__init__.py)

Solution:



'''
