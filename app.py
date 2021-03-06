# ---------------------------------------------------------------------#
# Imports
# ---------------------------------------------------------------------#
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler

from flask_wtf import CSRFProtect

from forms import *
from models import *
from datetime import datetime
from enums import Genre

# ---------------------------------------------------------------------#
# App Config.
# ---------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
csrf = CSRFProtect(app)
db.init_app(app)

migrate = Migrate(app, db)


# ---------------------------------------------------------------------#
# Filters.
# ---------------------------------------------------------------------#

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


# ---------------------------------------------------------------------#
# Controllers.
# ---------------------------------------------------------------------#

@app.route('/')
def index():
    """ Shows the home page.

    Returns: The home view with the 10 most recently listed venues and artists.
    """

    error = False
    recent_venues = []
    recent_artists = []

    try:
        # Get the 10 most recently listed venues
        recent_venues = Venue.query.order_by(db.desc(Venue.created_date)) \
            .limit(10).all()

        # Get the 10 most recently listed artists
        recent_artists = Artist.query.order_by(db.desc(Artist.created_date)) \
            .limit(10).all()
    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/home.html',
                           recent_venues=recent_venues,
                           recent_artists=recent_artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    """ Shows the list of venues grouped by city and state.

    Returns: The venues view with the distinct areas. For each area, there will
        be a list of venues.
    """

    error = False
    response = []

    try:
        venues_list = Venue.query.all()

        # Get all the distinct state and city combinations
        places = Venue.query.distinct(Venue.city, Venue.state).all()

        for place in places:
            response.append({
                'city': place.city,
                'state': place.state,
                'venues': [{
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows':
                        len([show for show in venue.shows
                             if show.start_time > datetime.now()])
                } for venue in venues_list if
                    venue.city == place.city and venue.state == place.state]
            })
    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/venues.html', areas=response)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """ Searches venues in the database for the user's query.

    Returns: Returns the venues that match the user's search query.
    """

    error = False
    response_data = {}

    try:
        search_term = request.form.get('search_term', '')

        # ilike makes the search case-insensitive
        result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

        data = []
        current_time = datetime.now()

        for venue in result:
            upcoming_shows = Show.query.filter_by(venue_id=venue.id) \
                .filter(Show.start_time > current_time).all()

            data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows),
            })

        response_data = {
            "count": len(result),
            "data": data
        }
    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/search_venues.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """ Shows the venue details for a specific venue.

    Args:
        venue_id: The id of the venue that the user has clicked on.

    Returns: Returns the show venue view with the venue data.
    """

    error = False
    data = {}

    try:
        venue = Venue.query.get_or_404(venue_id)

        past_shows = []
        upcoming_shows = []

        # Uses joined loading (lazy='joined') within relationship in the model
        for show in venue.shows:
            temp_show = {
                'artist_id': show.artist_id,
                'artist_name': show.artist.name,
                'artist_image_link': show.artist.image_link,
                'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
            }
            if show.start_time <= datetime.now():
                past_shows.append(temp_show)
            else:
                upcoming_shows.append(temp_show)

        # object class to dict
        data = vars(venue)

        data['past_shows'] = past_shows
        data['upcoming_shows'] = upcoming_shows
        data['past_shows_count'] = len(past_shows)
        data['upcoming_shows_count'] = len(upcoming_shows)

        genre_list = []
        for genre in venue.genres:
            genre_list.append(Genre[genre].value)

        data['genres'] = genre_list
    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/show_venue.html', venue=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    """ Shows the create venue form.

    Returns: Returns the create venue view.
    """

    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    """ Creates a venue within the database if the form submission is valid.

    Returns: Returns the homepage view with a flash indicating whether the
        creation was a success or failure.
    """

    error = False

    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            venue = Venue()
            form.populate_obj(venue)

            db.session.add(venue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            app.logger.error(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occurred. Venue ' + form.name.data +
                  ' could not be created.')
        if not error:
            flash('Venue ' + form.name.data + ' was successfully created!')
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    """ Shows the edit venue form.

    Args:
        venue_id: The id of the venue that the user wants to update.

    Returns: Returns the edit venue view with the
        venue details to populate the form.
    """

    try:
        venue = Venue.query.get_or_404(venue_id)

        form = VenueForm(obj=venue)

        return render_template('forms/edit_venue.html', form=form, venue=venue)
    except:
        app.logger.error(sys.exc_info())
        return render_template('errors/500.html')


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    """ Updates a venue within the database if the form submission is valid.

    Args:
        venue_id: The id of the venue that the user wants to update.

    Returns: Returns the show venue view with a flash indicating whether the
        update was a success or failure.
    """

    error = False
    form = VenueForm(request.form)

    if form.validate():
        try:
            venue = Venue.query.get(venue_id)

            form.populate_obj(venue)

            db.session.commit()
        except:
            error = True
            db.session.rollback()
            app.logger.error(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occurred. Venue ' + form.name.data +
                  ' could not be updated.')
        if not error:
            flash('Venue ' + form.name.data + ' was successfully updated!')
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return redirect(url_for('show_venue', venue_id=venue_id))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """ Deletes a venue within the database.

    Args:
        venue_id: The id of the venue that the user wants to delete.

    Returns: Returns the homepage view with a flash indicating whether the
        delete was a success or failure.
    """

    error = False
    venue_name = ""

    try:
        venue = Venue.query.get(venue_id)

        # Set the name to a variable so it can be used in the flash message.
        venue_name = venue.name

        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        app.logger.error(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + venue_name +
              ' could not be deleted.')
    if not error:
        flash('Venue ' + venue_name + ' was successfully deleted!')

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    """ Shows the list of artists.

    Returns: The artists view with a list of all artists.
    """

    artist_data = Artist.query.all()
    return render_template('pages/artists.html', artists=artist_data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    """ Searches artists in the database for the user's query.

    Returns: Returns the artists that match the user's search query.
    """

    error = False
    response_data = {}

    try:
        search_term = request.form.get('search_term', '')

        # ilike makes the search case-insensitive
        artist_results = Artist.query \
            .filter(Artist.name.ilike(f'%{search_term}%')).all()

        data = []
        current_time = datetime.now()

        for artist in artist_results:
            upcoming_shows = Show.query.filter_by(artist_id=artist.id) \
                .filter(Show.start_time > current_time).all()

            data.append({
                'id': artist.id,
                'name': artist.name,
                'num_upcoming_shows': len(upcoming_shows),
            })

        response_data = {
            "count": len(artist_results),
            "data": data
        }
    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/search_artists.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """ Shows the artist details for a specific artist.

    Args:
        artist_id: The id of the artist that the user has clicked on.

    Returns: Returns the show artist view with the artist data.
    """

    error = False
    data = {}

    try:
        artist = Artist.query.get_or_404(artist_id)

        past_shows = []
        upcoming_shows = []

        # Uses joined loading (lazy='joined') within relationship in the model
        for show in artist.shows:
            temp_show = {
                'venue_id': show.venue_id,
                'venue_name': show.venue.name,
                'venue_image_link': show.venue.image_link,
                'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
            }
            if show.start_time <= datetime.now():
                past_shows.append(temp_show)
            else:
                upcoming_shows.append(temp_show)

        # object class to dict
        data = vars(artist)

        data['past_shows'] = past_shows
        data['upcoming_shows'] = upcoming_shows
        data['past_shows_count'] = len(past_shows)
        data['upcoming_shows_count'] = len(upcoming_shows)

        genre_list = []
        for genre in artist.genres:
            genre_list.append(Genre[genre].value)

        data['genres'] = genre_list

    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/show_artist.html', artist=data)


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    """ Shows the create artist form.

    Returns: Returns the create artist view.
    """

    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    """ Creates an artist within the database if the form submission is valid.

    Returns: Returns the homepage view with a flash indicating whether the
        creation was a success or failure.
    """

    error = False
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist()

            form.populate_obj(artist)

            db.session.add(artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            app.logger.error(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occurred. Artist ' + form.name.data +
                  ' could not be created.')
        if not error:
            flash('Artist ' + form.name.data + ' was successfully created!')

    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return render_template('pages/home.html')


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    """ Shows the edit artist form.

    Args:
        artist_id: The id of the artist that the user wants to update.

    Returns: Returns the edit artist view with the
        artist details to populate the form.
    """

    try:
        artist = Artist.query.get_or_404(artist_id)

        form = ArtistForm(obj=artist)

        return render_template('forms/edit_artist.html',
                               form=form, artist=artist)
    except:
        app.logger.error(sys.exc_info())
        return render_template('errors/500.html')


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    """ Updates an artist within the database if the form submission is valid.

    Args:
        artist_id: The id of the artist that the user wants to update.

    Returns: Returns the show artist view with a flash indicating whether the
        update was a success or failure.
    """

    error = False
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist.query.get_or_404(artist_id)

            form.populate_obj(artist)

            db.session.commit()
        except:
            error = True
            db.session.rollback()
            app.logger.error(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occurred. Artist ' + form.name.data +
                  ' could not be updated.')
        if not error:
            flash('Artist ' + form.name.data + ' was successfully updated!')

    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    """ Deletes an artist within the database.

    Args:
        artist_id: The id of the artist that the user wants to delete.

    Returns: Returns the homepage view with a flash indicating whether the
        delete was a success or failure.
    """

    error = False
    artist_name = ""

    try:
        artist = Artist.query.get(artist_id)

        # Set the name to a variable so it can be used in the flash message.
        artist_name = artist.name

        db.session.delete(artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        app.logger.error(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + artist_name +
              ' could not be deleted.')
    if not error:
        flash('Artist ' + artist_name + ' was successfully deleted!')

    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    """ Shows the list of shows.

    Returns: The shows view with a list of all shows.
    """

    error = False
    data = []

    try:
        show_data = Show.query.order_by(Show.start_time).all()

        for show in show_data:
            data.append({
                'venue_id': show.venue_id,
                'venue_name': show.venue.name,
                'artist_id': show.artist_id,
                'artist_name': show.artist.name,
                'artist_image_link': show.artist.image_link,
                'start_time': show.start_time
            })
    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    """ Shows the create show form.

    Returns: Returns the create show view.
    """

    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    """ Creates a show within the database if the form submission is valid.

    Returns: Returns the homepage view with a flash indicating whether the
        creation was a success or failure.
    """

    error = False
    form = ShowForm(request.form)

    if form.validate():
        try:
            show = Show()
            form.populate_obj(show)

            db.session.add(show)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            app.logger.error(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occurred. Show could not be created.')
        if not error:
            flash('Show was successfully created!')

    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


file_handler = FileHandler('error.log')
file_handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%('
              'lineno)d]')
)
app.logger.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.info('errors')

# ---------------------------------------------------------------------#
# Launch.
# ---------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
