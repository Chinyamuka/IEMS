"""
IEMS Equipment Bulk Actions

Handles bulk retire and bulk delete from the equipment
list page. Both are POST-only; each row's ID arrives
via the `ids[]` form field.
"""

from flask import (
    Blueprint,
    redirect,
    url_for,
    flash,
    request,
)

from app.extensions import db
from app.models import Equipment
from app.auth.decorators import login_required
from app.utils.permissions import role_required
from app.utils.activity import log_activity
from app.utils.cache import cache_delete
from app.routes.dashboard import CACHE_KEY_DASHBOARD_STATS


equipment_bulk_bp = Blueprint(
    "equipment_bulk",
    __name__,
    url_prefix="/equipment/bulk",
)


@equipment_bulk_bp.route("/", methods=["POST"])
@login_required
@role_required("Administrator")
def index():
    """Apply a bulk action to selected equipment rows."""

    action = request.form.get("action", "").strip()
    ids = request.form.getlist("ids[]")

    if not ids:
        flash("No items were selected.", "warning")
        return redirect(url_for("equipment.index"))

    if action not in {"retire", "delete"}:
        flash("Unknown action.", "danger")
        return redirect(url_for("equipment.index"))

    items = Equipment.query.filter(Equipment.id.in_(ids)).all()

    if not items:
        flash("The selected items could not be found.", "warning")
        return redirect(url_for("equipment.index"))

    count = 0

    if action == "retire":
        for eq in items:
            if eq.status != "Retired":
                eq.status = "Retired"
                log_activity(
                    "update",
                    "Equipment",
                    eq.id,
                    f"Bulk retired {eq.asset_tag}",
                )
                count += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "Bulk retire failed. Please try again.",
                "danger",
            )
            return redirect(url_for("equipment.index"))

        cache_delete(CACHE_KEY_DASHBOARD_STATS)
        flash(
            f"{count} equipment item"
            f"{'s' if count != 1 else ''} retired.",
            "success",
        )

    elif action == "delete":
        for eq in items:
            log_activity(
                "delete",
                "Equipment",
                eq.id,
                f"Bulk deleted {eq.asset_tag}",
            )
            db.session.delete(eq)
            count += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "Bulk delete failed. Please try again.",
                "danger",
            )
            return redirect(url_for("equipment.index"))

        cache_delete(CACHE_KEY_DASHBOARD_STATS)
        flash(
            f"{count} equipment item"
            f"{'s' if count != 1 else ''} deleted.",
            "success",
        )

    return redirect(url_for("equipment.index"))