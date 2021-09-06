from flask import Blueprint, render_template, request, flash, redirect, url_for

from app.forms import *
from app.models import *

venue_bp = Blueprint('venues', __name__, url_prefix='/venues')


@venue_bp.route('/')
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
        # app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/venues.html', areas=response)


@venue_bp.route('/search', methods=['POST'])
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
        # app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/search_venues.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@venue_bp.route('/<int:venue_id>')
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
        # app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/show_venue.html', venue=data)


@venue_bp.route('/create', methods=['GET'])
def create_venue_form():
    """ Shows the create venue form.

    Returns: Returns the create venue view.
    """

    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@venue_bp.route('/create', methods=['POST'])
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
            # app.logger.error(sys.exc_info())
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


@venue_bp.route('/<int:venue_id>/edit', methods=['GET'])
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
        # app.logger.error(sys.exc_info())
        return render_template('errors/500.html')


@venue_bp.route('/<int:venue_id>/edit', methods=['POST'])
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
            # app.logger.error(sys.exc_info())
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


@venue_bp.route('/<venue_id>', methods=['DELETE'])
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
        # app.logger.error(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + venue_name +
              ' could not be deleted.')
    if not error:
        flash('Venue ' + venue_name + ' was successfully deleted!')

    return redirect(url_for('index'))
