from flask import Flask

from config import Config
from .extensions import db, migrate
from . import models
from .routes import register_routes


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    register_routes(app)

    return app