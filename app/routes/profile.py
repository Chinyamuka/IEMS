"""
IEMS Self-Service Profile Routes

Every logged-in user can view and edit their own
profile. Every mutation is recorded in the activity log.
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
from app.models import User
from app.auth.decorators import login_required
from app.utils.uploads import (
    save_image,
    delete_image,
    ImageUploadError,
)
from app.utils.activity import log_activity


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
    """Display the current user's profile (read-only)."""
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

    Deliberately does NOT allow editing employee_number,
    department_id, role or is_active.
    """

    user = g.current_user

    if request.method == "POST":

        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        phone      = request.form.get("phone", "").strip()

        if not first_name or not last_name:
            flash(
                "First name and last name are required.",
                "danger",
            )
            return render_template(
                "profile/edit.html",
                user=user,
            )

        if email:
            duplicate_email = User.query.filter(
                User.email == email,
                User.id != user.id,
            ).first()

            if duplicate_email:
                flash(
                    "That email address is already in use.",
                    "danger",
                )
                return render_template(
                    "profile/edit.html",
                    user=user,
                )

        new_image_filename = None
        old_image_filename = user.profile_image

        try:
            new_image_filename = save_image(
                request.files.get("profile_image"),
                "users",
            )
        except ImageUploadError as error:
            flash(str(error), "danger")
            return render_template(
                "profile/edit.html",
                user=user,
            )

        user.first_name = first_name
        user.last_name = last_name
        user.email = email or None
        user.phone = phone or None

        if new_image_filename is not None:
            user.profile_image = new_image_filename

        log_activity(
            "update",
            "User",
            user.id,
            "Updated own profile",
        )

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()

            if new_image_filename is not None:
                delete_image(new_image_filename, "users")

            flash(
                "Changes could not be saved. Please try again.",
                "danger",
            )
            return render_template(
                "profile/edit.html",
                user=user,
            )

        if (
            new_image_filename is not None
            and old_image_filename is not None
        ):
            delete_image(old_image_filename, "users")

        flash(
            "Your profile was updated successfully.",
            "success",
        )

        return redirect(url_for("profile.index"))

    return render_template(
        "profile/edit.html",
        user=user,
    )


# =========================================================
# CHANGE PASSWORD
# =========================================================

@profile_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Change the current user's password.

    Also clears must_change_password on success, which
    releases the before_request guard in app/__init__.py
    that otherwise forces the user back to this page on
    every request.

    The log entry says only 'Changed password' — the
    password itself is never recorded.
    """

    user = g.current_user

    if request.method == "POST":

        current_password = request.form.get("current_password", "")
        new_password     = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            flash(
                "All three fields are required.",
                "danger",
            )
            return render_template(
                "profile/change_password.html",
                user=user,
            )

        if len(new_password) < 8:
            flash(
                "The new password must be at least 8 characters.",
                "danger",
            )
            return render_template(
                "profile/change_password.html",
                user=user,
            )

        if new_password != confirm_password:
            flash(
                "The new passwords do not match.",
                "danger",
            )
            return render_template(
                "profile/change_password.html",
                user=user,
            )

        if new_password == current_password:
            flash(
                "The new password must be different "
                "from the current password.",
                "danger",
            )
            return render_template(
                "profile/change_password.html",
                user=user,
            )

        if not user.check_password(current_password):
            flash(
                "Your current password is incorrect.",
                "danger",
            )
            return render_template(
                "profile/change_password.html",
                user=user,
            )

        user.set_password(new_password)

        # Clear the flag in the same transaction as the
        # password change. If we set it after the commit
        # and the process crashed between the two, the
        # user would be flagged despite having changed.
        user.must_change_password = False

        log_activity(
            "password_change",
            "User",
            user.id,
            "Changed password",
        )

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            flash(
                "Your password could not be changed. "
                "Please try again.",
                "danger",
            )
            return render_template(
                "profile/change_password.html",
                user=user,
            )

        flash(
            "Your password was changed successfully.",
            "success",
        )

        return redirect(url_for("profile.index"))

    return render_template(
        "profile/change_password.html",
        user=user,
    )