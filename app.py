# ---------------------------------------------------------------------------- #
# Imports
# ---------------------------------------------------------------------------- #
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
import datetime

# ---------------------------------------------------------------------------- #
# App Config.
# ---------------------------------------------------------------------------- #

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, date_format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value

    if date_format == 'full':
        date_format = "EEEE MMMM, d, y 'at' h:mma"
    elif date_format == 'medium':
        date_format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, date_format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []

    venue_locations = db.session.query(Venue.city, Venue.state).group_by(Venue.state, Venue.city).all()
    current_time = datetime.datetime.now()

    for location in venue_locations:
        city = location[0]
        state = location[1]

        location_venues = Venue.query.filter_by(city=city, state=state).all()
        venue_data = []

        for venue in location_venues:
            upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > current_time).all()

            venue_data.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(upcoming_shows),
            })

        data.append({"city": city, "state": state, "venues": venue_data})

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')

    # ilike makes the search case-insensitive
    venue_data = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

    data = []
    current_time = datetime.datetime.now()

    for venue in venue_data:
        upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > current_time).all()

        data.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(upcoming_shows),
        })

    response_data = {
        "count": len(venue_data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    # If no venue has been returned then return a 404 error
    if not venue:
        return render_template('errors/404.html')

    current_time = datetime.datetime.now()

    upcoming_shows_data = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > current_time).all()
    upcoming_shows = []

    for upcoming_show in upcoming_shows_data:
        upcoming_shows.append({
            'artist_id': upcoming_show.venue_id,
            'artist_name': upcoming_show.venue.name,
            'artist_image_link': upcoming_show.venue.image_link,
            'start_time': upcoming_show.start_time
        })

    past_shows_data = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time <= current_time).all()
    past_shows = []

    for past_show in past_shows_data:
        past_shows.append({
            'artist_id': past_show.venue_id,
            'artist_name': past_show.venue.name,
            'artist_image_link': past_show.venue.image_link,
            'start_time': past_show.start_time
        })

    genres = []
    for genre in venue.genres:
        genres.append(genre.name)

    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artist_data = Artist.query.all()
    return render_template('pages/artists.html', artists=artist_data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')

    # ilike makes the search case-insensitive
    artist_data = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    data = []
    current_time = datetime.datetime.now()

    for artist in artist_data:
        upcoming_shows = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time > current_time).all()

        data.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows),
        })

    response_data = {
        "count": len(artist_data),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)

    # If no artist has been returned then return a 404 error
    if not artist:
        return render_template('errors/404.html')

    current_time = datetime.datetime.now()

    upcoming_shows_data = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time > current_time).all()
    upcoming_shows = []

    for upcoming_show in upcoming_shows_data:
        upcoming_shows.append({
            'venue_id': upcoming_show.venue_id,
            'venue_name': upcoming_show.venue.name,
            'venue_image_link': upcoming_show.venue.image_link,
            'start_time': upcoming_show.start_time
        })

    past_shows_data = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time <= current_time).all()
    past_shows = []

    for past_show in past_shows_data:
        past_shows.append({
            'venue_id': past_show.venue_id,
            'venue_name': past_show.venue.name,
            'venue_image_link': past_show.venue.image_link,
            'start_time': past_show.start_time
        })

    genres = []
    for genre in artist.genres:
        genres.append(genre.name)

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
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
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    show_data = Show.query.all()

    for show in show_data:
        data.append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time
        })

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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
