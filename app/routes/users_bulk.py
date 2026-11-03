"""
IEMS Users Bulk Actions
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
    action = request.form.get("action", "").strip()
    ids = request.form.getlist("ids[]")

    if not ids:
        flash("No items were selected.", "warning")
        return redirect(url_for("users.index"))

    if action not in {"deactivate", "activate"}:
        flash("Unknown action.", "danger")
        return redirect(url_for("users.index"))

    users = User.query.filter(User.id.in_(ids)).all()
    count = 0

    if action == "deactivate":
        for u in users:
            if u.id == g.current_user.id:
                continue
            if u.role == "Administrator":
                other_admins = User.query.filter(
                    User.role == "Administrator",
                    User.is_active == True,
                    User.id != u.id,
                ).count()
                if other_admins == 0:
                    continue
            if u.is_active:
                u.is_active = False
                log_activity(
                    "deactivate",
                    "User",
                    u.id,
                    f"Bulk deactivated {u.employee_number}",
                )
                count += 1

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
                count += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Bulk action failed. Please try again.", "danger")
        return redirect(url_for("users.index"))

    flash(f"{count} item(s) updated.", "success")
    return redirect(url_for("users.index"))