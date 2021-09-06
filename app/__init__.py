# ---------------------------------------------------------------------#
# Imports
# ---------------------------------------------------------------------#
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, flash
from flask_migrate import Migrate
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler

from flask_wtf import CSRFProtect

from app.models import *
from app.routes.venues import venue_bp
from app.routes.artists import artist_bp
from app.routes.shows import show_bp

# ---------------------------------------------------------------------#
# App Config.
# ---------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
csrf = CSRFProtect(app)
db.init_app(app)

migrate = Migrate(app, db)

app.register_blueprint(venue_bp)
app.register_blueprint(artist_bp)
app.register_blueprint(show_bp)


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


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


file_handler = FileHandler('../error.log')
file_handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%('
              'lineno)d]')
)
app.logger.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.info('errors')
