from flask import Flask

from config import Config
from .extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def home():
        return "IEMS - ICT Equipment Management System"

    return app
