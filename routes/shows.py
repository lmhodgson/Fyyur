from flask import Blueprint, render_template, request, flash

from forms import *
from models import *

show_bp = Blueprint('shows', __name__, url_prefix='/shows')


@show_bp.route('/')
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
        # app.logger.error(sys.exc_info())

    if error:
        flash('Something went wrong!')

    return render_template('pages/shows.html', shows=data)


@show_bp.route('/create')
def create_shows():
    """ Shows the create show form.

    Returns: Returns the create show view.
    """

    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@show_bp.route('/create', methods=['POST'])
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
            # app.logger.error(sys.exc_info())
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
