from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(300))
    genres = db.relationship("Genre", secondary="VenueGenre", backref="venue_genre", lazy=True)
    shows = db.relationship('Show', backref='venue', lazy=True, cascade="all, delete")
    created_date = db.Column(db.DateTime, nullable=False, default=func.now())


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(300))
    genres = db.relationship("Genre", secondary="ArtistGenre", backref="artist_genre", lazy=True)
    shows = db.relationship('Show', backref='artist', lazy=True, cascade="all, delete")
    created_date = db.Column(db.DateTime, nullable=False, default=func.now())


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id", ondelete='CASCADE'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id", ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)


class Genre(db.Model):
    __tablename__ = "Genre"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class ArtistGenre(db.Model):
    __tablename__ = "ArtistGenre"
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id", ondelete='CASCADE'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey("Genre.id", ondelete='CASCADE'), primary_key=True)


class VenueGenre(db.Model):
    __tablename__ = "VenueGenre"
    artist_id = db.Column(db.Integer, db.ForeignKey("Venue.id", ondelete='CASCADE'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey("Genre.id", ondelete='CASCADE'), primary_key=True)
