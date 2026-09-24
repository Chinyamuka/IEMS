"""
IEMS Authentication Routes

Handles:
- User login
- User logout
- Session management

Passwords are never stored or compared as plaintext.
Werkzeug verifies the stored password hash.
"""
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import User


# ---------------------------------------------------------
# Blueprint
# ---------------------------------------------------------

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
)


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate an IEMS user.

    GET:
        Display the login form.

    POST:
        Validate the employee number and password,
        then create a Flask session.
    """

    # If the user is already logged in,
    # there is no reason to show the login page again.
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":

        # -------------------------------------------------
        # Get submitted form values
        # -------------------------------------------------

        employee_number = request.form.get(
            "employee_number",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # -------------------------------------------------
        # Basic validation
        # -------------------------------------------------

        if not employee_number or not password:
            flash(
                "Employee number and password are required.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        # -------------------------------------------------
        # Find the user
        # -------------------------------------------------

        user = User.query.filter_by(
            employee_number=employee_number
        ).first()

        # -------------------------------------------------
        # Check user and password
        # -------------------------------------------------

        if user is None or not check_password_hash(
            user.password_hash,
            password
        ):
            flash(
                "Invalid employee number or password.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        # -------------------------------------------------
        # Check whether account is active
        # -------------------------------------------------

        if not user.is_active:
            flash(
                "Your account is inactive. "
                "Please contact an administrator.",
                "error"
            )

            return render_template(
                "auth/login.html"
            )

        # -------------------------------------------------
        # Create authenticated session
        # -------------------------------------------------

        session.clear()

        session["user_id"] = user.id
        session["employee_number"] = user.employee_number
        session["role"] = user.role

        # -------------------------------------------------
        # Optional: remember the user's display name
        # -------------------------------------------------

        session["user_name"] = user.full_name

        flash(
            f"Welcome back, {user.full_name}!",
            "success"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # -----------------------------------------------------
    # GET request
    # -----------------------------------------------------

    return render_template(
        "auth/login.html"
    )


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Log the current user out.

    POST is intentionally used instead of GET so that
    logout is an explicit state-changing action.
    """

    # Remove everything stored in the current session.
    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )