import os
import logging

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:ShushPaul123@localhost:5432/Fyyur'
SQLALCHEMY_TRACK_MODIFICATIONS = False