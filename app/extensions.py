"""
IEMS Flask Extensions

This file contains Flask extensions that will be shared
throughout the application.
"""

# SQLAlchemy allows us to work with our database using
# Python classes and objects instead of writing SQL everywhere.
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail


# Create the SQLAlchemy database object.
db = SQLAlchemy()
migrate = Migrate()

# Flask-Mail extension. Bound to the app in create_app()
# via app.email.bootstrap.init_mail(). Importable everywhere
# without a cycle because this module imports nothing from
# the app package.
mail = Mail()
