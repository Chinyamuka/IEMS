# app/__init__.py
"""
IEMS Application Factory

Creates the Flask app, initialises extensions, registers
blueprints, and wires app-wide request hooks.
"""

from flask import (
    Flask,
    flash,
    g,
    redirect,
    request,
    url_for,
)

from config import Config
from .context_processors import (
    inject_current_user,
    load_current_user,
)
from .extensions import db, migrate
from . import models
from .routes import register_routes
from .email import init_mail
from .email.commands import register_mail_commands


# =========================================================
# FORCED PASSWORD CHANGE
# =========================================================
#
# Endpoints that remain reachable while a user is
# flagged for a mandatory password change.
#
# Without these the user would be unable to reach the
# change form (redirect loop), unable to log out if
# they lost the temp password, or unable to load CSS
# on the change form.

ALLOWED_WHILE_FLAGGED = {
    "profile.change_password",
    "auth.logout",
}


def enforce_password_change():
    """
    before_request handler.

    If the authenticated user has must_change_password
    set, redirect them to /profile/change-password unless
    they are already on an allowlisted page.

    Runs after load_current_user, so g.current_user is
    already populated.
    """

    user = g.get("current_user")

    if user is None:
        return None

    if not user.must_change_password:
        return None

    endpoint = request.endpoint or ""

    if endpoint in ALLOWED_WHILE_FLAGGED:
        return None

    if endpoint.startswith("static"):
        return None

    flash(
        "You must change your password before continuing.",
        "warning",
    )

    return redirect(url_for("profile.change_password"))


# =========================================================
# APPLICATION FACTORY
# =========================================================

def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    init_mail(app)
    register_mail_commands(app)

    app.before_request(load_current_user)
    app.before_request(enforce_password_change)
    app.context_processor(inject_current_user)
    register_routes(app)

    return app
