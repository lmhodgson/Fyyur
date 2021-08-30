# ---------------------------------------------------------------------------- #
# Imports
# ---------------------------------------------------------------------------- #
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
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
    error = False
    recent_venues = []
    recent_artists = []

    try:
        # Get the 10 most recently listed venues
        recent_venues = Venue.query.order_by(db.desc(Venue.created_date)).limit(10).all()

        # Get the 10 most recently listed artists
        recent_artists = Artist.query.order_by(db.desc(Artist.created_date)).limit(10).all()
    except Exception as ex:
        error = True
        app.logger.error(ex)

    if error:
        flash('Something went wrong!')

    return render_template('pages/home.html', recent_venues=recent_venues, recent_artists=recent_artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    error = False
    data = []

    try:
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
    except:
        error = True
        app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    error = False
    response_data = {}

    try:
        search_term = request.form.get('search_term', '')

        # ilike makes the search case-insensitive
        venue_results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

        data = []
        current_time = datetime.datetime.now()

        for venue in venue_results:
            upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > current_time).all()

            data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows),
            })

        response_data = {
            "count": len(venue_results),
            "data": data
        }
    except Exception as ex:
        error = True
        app.logger.error(ex)

    if error:
        flash('Something went wrong!')

    return render_template('pages/search_venues.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    error = False
    data = {}

    try:
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
    except Exception as ex:
        error = True
        app.logger.error(ex)

    if error:
        flash('Something went wrong!')

    return render_template('pages/show_venue.html', venue=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']
        website = request.form['website_link']
        seeking_talent = True if 'seeking_talent' in request.form else False
        seeking_description = request.form['seeking_description']
        genres = request.form.getlist('genres')

        # Create the new venue
        venue = Venue(name=name, city=city, state=state, address=address, phone=phone, image_link=image_link,
                      facebook_link=facebook_link, website=website, seeking_talent=seeking_talent,
                      seeking_description=seeking_description)

        for genre in genres:
            # Try to get a genre from the database
            genre_data = Genre.query.filter_by(name=genre).first()
            if genre_data:
                # If there is a genre in the database, append it to the list
                venue.genres.append(genre_data)

            else:
                # This genre is not in the database, so create it
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                venue.genres.append(new_genre)

        db.session.add(venue)
        db.session.commit()
    except Exception as ex:
        error = True
        db.session.rollback()
        app.logger.error(ex)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be created.')
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully created!')

    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    try:
        form = VenueForm()

        venue = Venue.query.get(venue_id)

        # If no venue has been returned then return a 404 error
        if not venue:
            return render_template('errors/404.html')

        form.name.data = venue.name
        form.city.data = venue.city
        form.state.data = venue.state
        form.address.data = venue.address
        form.phone.data = venue.phone
        form.image_link.data = venue.image_link
        form.facebook_link.data = venue.facebook_link
        form.website_link.data = venue.website
        form.seeking_talent.data = venue.seeking_talent
        form.seeking_description.data = venue.seeking_description
        form.genres.data = [genre.name for genre in venue.genres]

        return render_template('forms/edit_venue.html', form=form, venue=venue)
    except:
        app.logger.error(sys.exc_info())
        return render_template('errors/500.html')


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)

        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        venue.website = request.form['website_link']
        venue.seeking_talent = True if 'seeking_talent' in request.form else False
        venue.seeking_description = request.form['seeking_description']

        genres = request.form.getlist('genres')
        venue.genres = []

        for genre in genres:
            # Try to get a genre from the database
            genre_data = Genre.query.filter_by(name=genre).first()
            if genre_data:
                # If there is a genre in the database, append it to the list
                venue.genres.append(genre_data)

            else:
                # This genre is not in the database, so create it
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                venue.genres.append(new_genre)

        db.session.commit()
    except Exception as ex:
        error = True
        db.session.rollback()
        app.logger.error(ex)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')

    return redirect(url_for('show_venue', venue_id=venue_id))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        error = True
        app.logger.error(ex)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue could not be deleted.')
    if not error:
        flash('Venue was successfully deleted!')

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    artist_data = Artist.query.all()
    return render_template('pages/artists.html', artists=artist_data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    error = False
    response_data = {}

    try:
        search_term = request.form.get('search_term', '')

        # ilike makes the search case-insensitive
        artist_results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

        data = []
        current_time = datetime.datetime.now()

        for artist in artist_results:
            upcoming_shows = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time > current_time).all()

            data.append({
                'id': artist.id,
                'name': artist.name,
                'num_upcoming_shows': len(upcoming_shows),
            })

        response_data = {
            "count": len(artist_results),
            "data": data
        }
    except Exception as ex:
        error = True
        app.logger.error(ex)

    if error:
        flash('Something went wrong!')

    return render_template('pages/search_artists.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    error = False
    data = {}

    try:
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
    except Exception as ex:
        error = True
        app.logger.error(ex)

    if error:
        flash('Something went wrong!')

    return render_template('pages/show_artist.html', artist=data)


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']
        website = request.form['website_link']
        seeking_venue = True if 'seeking_venue' in request.form else False
        seeking_description = request.form['seeking_description']
        genres = request.form.getlist('genres')

        # Create the new artist
        artist = Artist(name=name, city=city, state=state, phone=phone, image_link=image_link,
                        facebook_link=facebook_link, website=website, seeking_venue=seeking_venue,
                        seeking_description=seeking_description)

        for genre in genres:
            # Try to get a genre from the database
            genre_data = Genre.query.filter_by(name=genre).first()
            if genre_data:
                # If there is a genre in the database, append it to the list
                artist.genres.append(genre_data)

            else:
                # This genre is not in the database, so create it
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                artist.genres.append(new_genre)

        db.session.add(artist)
        db.session.commit()
    except Exception as ex:
        error = True
        db.session.rollback()
        app.logger.error(ex)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be created.')
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully created!')

    return render_template('pages/home.html')


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    try:
        form = ArtistForm()

        artist = Artist.query.get(artist_id)

        # If no artist has been returned then return a 404 error
        if not artist:
            return render_template('errors/404.html')

        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.image_link.data = artist.image_link
        form.facebook_link.data = artist.facebook_link
        form.website_link.data = artist.website
        form.seeking_venue.data = artist.seeking_venue
        form.seeking_description.data = artist.seeking_description
        form.genres.data = [genre.name for genre in artist.genres]

        return render_template('forms/edit_artist.html', form=form, artist=artist)
    except Exception as ex:
        app.logger.error(ex)
        return render_template('errors/500.html')


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)

        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.website = request.form['website_link']
        artist.seeking_venue = True if 'seeking_venue' in request.form else False
        artist.seeking_description = request.form['seeking_description']

        genres = request.form.getlist('genres')
        artist.genres = []

        for genre in genres:
            # Try to get a genre from the database
            genre_data = Genre.query.filter_by(name=genre).first()
            if genre_data:
                # If there is a genre in the database, append it to the list
                artist.genres.append(genre_data)

            else:
                # This genre is not in the database, so create it
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                artist.genres.append(new_genre)

        db.session.commit()
    except Exception as ex:
        error = True
        db.session.rollback()
        app.logger.error(ex)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        error = True
        app.logger.error(ex)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist could not be deleted.')
    if not error:
        flash('Artist was successfully deleted!')

    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
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
    except Exception as ex:
        error = True
        app.logger.error(ex)

    if error:
        flash('Something went wrong!')

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']

        # Create the new show
        show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

        db.session.add(show)
        db.session.commit()
    except Exception as ex:
        error = True
        db.session.rollback()
        app.logger.error(ex)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Show could not be created.')
    if not error:
        flash('Show was successfully created!')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


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
