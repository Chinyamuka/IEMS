"""
IEMS RBAC Permission Utilities

Provides reusable decorators for:

- Authentication checks
- Role-based authorization
"""

from functools import wraps

from flask import (
    flash,
    redirect,
    session,
    url_for,
)


def login_required(view):
    """
    Require the user to be authenticated.
    """

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if not session.get("user_id"):
            flash(
                "Please log in to continue.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )

        return view(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    """
    Require the authenticated user to have
    one of the specified roles.

    Example:

        @role_required("ADMIN")

    or:

        @role_required(
            "ADMIN",
            "INVENTORY_MANAGER"
        )
    """

    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            # User must be logged in first.
            if not session.get("user_id"):
                flash(
                    "Please log in to continue.",
                    "error"
                )

                return redirect(
                    url_for("auth.login")
                )

            user_role = session.get("role")

            if user_role not in allowed_roles:
                flash(
                    "You do not have permission "
                    "to access that page.",
                    "error"
                )

                return redirect(
                    url_for("dashboard.index")
                )

            return view(*args, **kwargs)

        return wrapped_view

    return decorator