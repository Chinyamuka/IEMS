"""
IEMS RBAC Permission Utilities

Centralized authentication and role-based authorization
for the Inventory Equipment Management System.
"""

from functools import wraps

from flask import (
    flash,
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

# Users who can create, edit and manage equipment.
EQUIPMENT_MANAGEMENT_ROLES = {
    ADMINISTRATOR,
    ASSET_OFFICER,
    IT_MANAGER,
    IT_OFFICER,
}


# Users who can delete equipment.
# Deletion is deliberately restricted to Administrators.
EQUIPMENT_DELETE_ROLES = {
    ADMINISTRATOR,
}


# Users who can manage assignments.
ASSIGNMENT_MANAGEMENT_ROLES = {
    ADMINISTRATOR,
    ASSET_OFFICER,
    IT_MANAGER,
    IT_OFFICER,
}


# Users who can manage system users.
USER_MANAGEMENT_ROLES = {
    ADMINISTRATOR,
}


# =========================================================
# AUTHENTICATION
# =========================================================

def login_required(view):
    """
    Require the user to be authenticated.
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

        return view(*args, **kwargs)

    return wrapped_view


# =========================================================
# ROLE CHECKING
# =========================================================

def role_required(*allowed_roles):
    """
    Require the authenticated user to have one
    of the specified roles.

    Example:

        @role_required("Administrator")

    Multiple roles:

        @role_required(
            "Administrator",
            "Asset Officer",
        )
    """

    # Convert to a set for clean membership testing.
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

            # -------------------------------------------------
            # ROLE
            # -------------------------------------------------

            user_role = session.get("role")

            # -------------------------------------------------
            # AUTHORIZATION
            # -------------------------------------------------

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