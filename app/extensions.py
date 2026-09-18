"""
IEMS Flask Extensions

This file contains Flask extensions that will be shared
throughout the application.
"""

# SQLAlchemy allows us to work with our database using
# Python classes and objects instead of writing SQL everywhere.
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# Create the SQLAlchemy database object.
db = SQLAlchemy()
migrate = Migrate()