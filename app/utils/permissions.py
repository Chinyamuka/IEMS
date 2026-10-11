"""
IEMS RBAC Permission Utilities

Centralized authentication and role-based authorization
for the Inventory Equipment Management System.

The role for a request is read from g.current_user, which
is populated by load_current_user() on every request via
app.before_request. This ensures:

- Role changes take effect on the user's next request
  (not at their next login).
- Deactivated users lose access immediately, because
  load_current_user clears the session and sets
  g.current_user = None when user.is_active is False.
"""

from functools import wraps

from flask import (
    flash,
    g,
    redirect,
    session,
    url_for,
)


# =========================================================
# IEMS ROLES
# =========================================================

ADMINISTRATOR = "Administrator"
ASSET_OFFICER = "Asset Officer"
IT_MANAGER = "IT Manager"
IT_OFFICER = "IT Officer"
EMPLOYEE = "Employee"


# =========================================================
# ROLE GROUPS
# =========================================================

EQUIPMENT_MANAGEMENT_ROLES = {
    ADMINISTRATOR,
    ASSET_OFFICER,
    IT_MANAGER,
    IT_OFFICER,
}

EQUIPMENT_DELETE_ROLES = {
    ADMINISTRATOR,
}

ASSIGNMENT_MANAGEMENT_ROLES = {
    ADMINISTRATOR,
    ASSET_OFFICER,
    IT_MANAGER,
    IT_OFFICER,
}

USER_MANAGEMENT_ROLES = {
    ADMINISTRATOR,
}


# =========================================================
# AUTHENTICATION
# =========================================================

def login_required(view):
    """
    Require an authenticated, active user.

    The active check is delegated to load_current_user(),
    which runs before every request and clears the
    session if the user is missing or inactive. We
    therefore only need to confirm that a session
    exists and that g.current_user has been populated.
    """

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if not session.get("user_id"):
            flash(
                "Please log in to continue.",
                "error",
            )
            return redirect(
                url_for("auth.login")
            )

        if g.get("current_user") is None:
            # load_current_user cleared the session because
            # the account was deleted or deactivated.
            flash(
                "Your session is no longer valid. "
                "Please sign in again.",
                "warning",
            )
            return redirect(
                url_for("auth.login")
            )

        return view(*args, **kwargs)

    return wrapped_view


# =========================================================
# ROLE CHECKING
# =========================================================

def role_required(*allowed_roles):
    """
    Require the authenticated user to have one of the
    specified roles.

    Example:

        @role_required("Administrator")

    Multiple roles:

        @role_required(
            "Administrator",
            "Asset Officer",
        )

    The role is read from g.current_user, NOT from the
    session. The session is a snapshot taken at login and
    becomes stale whenever an administrator changes a
    user's role or deactivates the account mid-session.
    g.current_user is refreshed on every request by
    load_current_user().
    """

    allowed_roles_set = set(allowed_roles)

    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            # -------------------------------------------------
            # AUTHENTICATION
            # -------------------------------------------------

            if not session.get("user_id"):
                flash(
                    "Please log in to continue.",
                    "error",
                )
                return redirect(
                    url_for("auth.login")
                )

            current_user = g.get("current_user")

            if current_user is None:
                flash(
                    "Your session is no longer valid. "
                    "Please sign in again.",
                    "warning",
                )
                return redirect(
                    url_for("auth.login")
                )

            # -------------------------------------------------
            # AUTHORIZATION
            # -------------------------------------------------
            #
            # Read the role from the live User object, not
            # from session["role"].

            user_role = current_user.role

            if user_role not in allowed_roles_set:
                flash(
                    "You do not have permission "
                    "to access that page.",
                    "error",
                )
                return redirect(
                    url_for("dashboard.index")
                )

            return view(*args, **kwargs)

        return wrapped_view

    return decorator