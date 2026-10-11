"""
IEMS Self-Service Profile Routes

Every logged-in user can view and edit their own
profile. Unlike app/routes/users.py, which is the
Administrator-only employee management tool, this
blueprint never touches anyone but the currently
logged-in user.

The current user is read from g.current_user, which
is populated by load_current_user() on every request
(see app/__init__.py). That means these routes always
operate on the live User row, never on stale session
data.

Routes:
    GET  /profile                  - view own profile
    GET  /profile/edit             - display edit form
    POST /profile/edit             - save changes
    GET  /profile/change-password  - display password form
    POST /profile/change-password  - save new password
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    g,
)

from app.extensions import db
from app.auth.decorators import login_required
from app.utils.uploads import (
    save_image,
    delete_image,
    ImageUploadError,
)


# =========================================================
# BLUEPRINT
# =========================================================

profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/profile",
)


# =========================================================
# VIEW
# =========================================================

@profile_bp.route("/")
@login_required
def index():
    """
    Display the current user's profile.

    Read-only. Editing happens on /profile/edit, and
    password changes on /profile/change-password, so
    that each page has exactly one job.
    """
    return render_template(
        "profile/index.html",
        user=g.current_user,
    )


# =========================================================
# EDIT
# =========================================================

@profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """
    Edit the current user's name, email, phone and photo.

    Deliberately does NOT allow editing:

        - employee_number (an identifier issued by HR,
          not self-managed)
        - department_id (organisational, assigned by HR)
        - role (RBAC concern, admin-only)
        - is_active (admin-only)

    Those are all managed through /users/<id>/edit by an
    Administrator.

    Full implementation lands in commit B3.
    """
    return render_template(
        "profile/edit.html",
        user=g.current_user,
    )


# =========================================================
# CHANGE PASSWORD
# =========================================================

@profile_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Change the current user's password.

    Deliberately requires the current password to be
    entered again, so that a hijacked session cannot
    silently rotate the credential and lock the real
    owner out.

    Full implementation lands in commit B4.
    """
    return render_template(
        "profile/change_password.html",
        user=g.current_user,
    )