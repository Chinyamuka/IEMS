"""
IEMS Authentication Decorators

Contains reusable decorators used to protect
routes that require an authenticated user.
"""

from functools import wraps
from flask import ( session, redirect, url_for,flash, g,)
from app.extensions import db
from app.models import User


def login_required(view_function):
    """ Require the user to be authenticated before
    accessing a protected route. """
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        # Get the user's ID from the session.
        user_id = session.get("user_id")

        # No session means the user is not authenticated.
        if user_id is None:

            flash(
                "Please sign in to access this page.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        # Find the user in the database.
        user = db.session.get(
            User,
            user_id
        )

        # User no longer exists.
        if user is None:

            session.clear()

            flash(
                "Your session is no longer valid. "
                "Please sign in again.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        # Account has been disabled.
        if not user.is_active:

            session.clear()

            flash(
                "Your account has been deactivated.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        # Make the current user available to the request.
        g.current_user = user

        # Continue to the protected route.
        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view