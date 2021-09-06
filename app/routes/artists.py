from flask import Blueprint, render_template, request, flash, redirect, url_for

from app.forms import *
from app.models import *

artist_bp = Blueprint('artists', __name__, url_prefix='/artists')


@artist_bp.route('/')
def artists():
    """ Shows the list of artists.

    Returns: The artists view with a list of all artists.
    """

    artist_data = Artist.query.all()
    return render_template('pages/artists.html', artists=artist_data)


@artist_bp.route('/search', methods=['POST'])
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
        # app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/search_artists.html', results=response_data,
                           search_term=request.form.get('search_term', ''))


@artist_bp.route('/<int:artist_id>')
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
        # app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/show_artist.html', artist=data)


@artist_bp.route('/create', methods=['GET'])
def create_artist_form():
    """ Shows the create artist form.

    Returns: Returns the create artist view.
    """

    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@artist_bp.route('/create', methods=['POST'])
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
            # app.logger.error(sys.exc_info())
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


@artist_bp.route('/<int:artist_id>/edit', methods=['GET'])
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
        # app.logger.error(sys.exc_info())
        return render_template('errors/500.html')


@artist_bp.route('/artists/<int:artist_id>/edit', methods=['POST'])
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
            # app.logger.error(sys.exc_info())
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


@artist_bp.route('/<artist_id>', methods=['DELETE'])
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
        # app.logger.error(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + artist_name +
              ' could not be deleted.')
    if not error:
        flash('Artist ' + artist_name + ' was successfully deleted!')

    return redirect(url_for('index'))
