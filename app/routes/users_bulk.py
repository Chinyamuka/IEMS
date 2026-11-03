"""
IEMS Users Bulk Actions

Handles bulk deactivate and bulk activate from the
users list page. Both are POST-only; each row's ID
arrives via the `ids[]` form field.

Safety guard: if any of the selected users is the
last active Administrator, that user is skipped and
counted separately, so the app cannot be locked out.
"""

from flask import (
    Blueprint,
    redirect,
    url_for,
    flash,
    request,
    g,
)

from app.extensions import db
from app.models import User
from app.auth.decorators import login_required
from app.utils.permissions import role_required
from app.utils.activity import log_activity


users_bulk_bp = Blueprint(
    "users_bulk",
    __name__,
    url_prefix="/users/bulk",
)


@users_bulk_bp.route("/", methods=["POST"])
@login_required
@role_required("Administrator")
def index():
    """Apply a bulk action to selected users."""

    action = request.form.get("action", "").strip()
    ids = request.form.getlist("ids[]")

    if not ids:
        flash("No items were selected.", "warning")
        return redirect(url_for("users.index"))

    if action not in {"deactivate", "activate"}:
        flash("Unknown action.", "danger")
        return redirect(url_for("users.index"))

    users = User.query.filter(User.id.in_(ids)).all()

    if not users:
        flash("The selected users could not be found.", "warning")
        return redirect(url_for("users.index"))

    changed = 0
    skipped = 0

    if action == "deactivate":
        for u in users:
            if g.current_user is not None and u.id == g.current_user.id:
                skipped += 1
                continue

            if u.role == "Administrator" and u.is_active:
                other_active_admins = User.query.filter(
                    User.role == "Administrator",
                    User.is_active.is_(True),
                    User.id != u.id,
                ).count()
                if other_active_admins == 0:
                    skipped += 1
                    continue

            if u.is_active:
                u.is_active = False
                log_activity(
                    "deactivate",
                    "User",
                    u.id,
                    f"Bulk deactivated {u.employee_number}",
                )
                changed += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "Bulk deactivate failed. Please try again.",
                "danger",
            )
            return redirect(url_for("users.index"))

        message = f"{changed} user{'s' if changed != 1 else ''} deactivated."
        if skipped:
            message += (
                f" {skipped} skipped "
                f"(self or last active Administrator)."
            )
        flash(message, "success")

    elif action == "activate":
        for u in users:
            if not u.is_active:
                u.is_active = True
                log_activity(
                    "activate",
                    "User",
                    u.id,
                    f"Bulk activated {u.employee_number}",
                )
                changed += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "Bulk activate failed. Please try again.",
                "danger",
            )
            return redirect(url_for("users.index"))

        flash(
            f"{changed} user{'s' if changed != 1 else ''} activated.",
            "success",
        )

    return redirect(url_for("users.index"))