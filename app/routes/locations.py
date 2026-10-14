"""
IEMS Location Management Routes

Administrator-only CRUD for the Location lookup table.
Every mutation is recorded in the activity log.
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from app.extensions import db
from app.models import Location, Equipment
from app.auth.decorators import login_required
from app.utils.permissions import role_required
from app.utils.activity import log_activity


# =========================================================
# BLUEPRINT
# =========================================================

locations_bp = Blueprint(
    "locations",
    __name__,
    url_prefix="/locations",
)


# =========================================================
# HELPER
# =========================================================

def _name_in_use(name, exclude_id=None):
    """True if a Location with this name already exists."""
    query = Location.query.filter(
        db.func.lower(Location.name) == name.lower()
    )

    if exclude_id is not None:
        query = query.filter(Location.id != exclude_id)

    return query.first() is not None


# =========================================================
# LIST
# =========================================================

@locations_bp.route("/")
@login_required
@role_required("Administrator")
def index():
    """Display all locations."""
    locations = Location.query.order_by(
        Location.name.asc()
    ).all()

    return render_template(
        "locations/index.html",
        locations=locations,
    )


# =========================================================
# CREATE
# =========================================================

@locations_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def create():
    """Create a new location."""

    if request.method == "POST":

        name        = request.form.get("name", "").strip()
        building    = request.form.get("building", "").strip()
        room        = request.form.get("room", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Location name is required.", "danger")
            return render_template("locations/create.html")

        if _name_in_use(name):
            flash(
                f"A location named '{name}' already exists.",
                "danger",
            )
            return render_template("locations/create.html")

        location = Location(
            name=name,
            building=building or None,
            room=room or None,
            description=description or None,
        )

        db.session.add(location)
        db.session.flush()

        log_activity(
            "create",
            "Location",
            location.id,
            f"Created location {location.name}",
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "The location could not be saved. "
                "Please try again.",
                "danger",
            )
            return render_template("locations/create.html")

        flash(
            f"Location '{location.name}' was created.",
            "success",
        )
        return redirect(url_for("locations.index"))

    return render_template("locations/create.html")


# =========================================================
# EDIT
# =========================================================

@locations_bp.route("/<int:location_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def edit(location_id):
    """Edit an existing location."""

    location = db.get_or_404(Location, location_id)

    if request.method == "POST":

        name        = request.form.get("name", "").strip()
        building    = request.form.get("building", "").strip()
        room        = request.form.get("room", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Location name is required.", "danger")
            return render_template(
                "locations/edit.html",
                location=location,
            )

        if _name_in_use(name, exclude_id=location.id):
            flash(
                f"A location named '{name}' already exists.",
                "danger",
            )
            return render_template(
                "locations/edit.html",
                location=location,
            )

        location.name = name
        location.building = building or None
        location.room = room or None
        location.description = description or None

        log_activity(
            "update",
            "Location",
            location.id,
            f"Updated location {location.name}",
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "The location could not be saved. "
                "Please try again.",
                "danger",
            )
            return render_template(
                "locations/edit.html",
                location=location,
            )

        flash(
            f"Location '{location.name}' was updated.",
            "success",
        )
        return redirect(url_for("locations.index"))

    return render_template(
        "locations/edit.html",
        location=location,
    )


# =========================================================
# DELETE
# =========================================================

@locations_bp.route("/<int:location_id>/delete", methods=["POST"])
@login_required
@role_required("Administrator")
def delete(location_id):
    """
    Delete a location.

    POST-only. Refuses to delete a location still
    referenced by any equipment record.
    """

    location = db.get_or_404(Location, location_id)

    equipment_count = Equipment.query.filter_by(
        location_id=location.id
    ).count()

    if equipment_count > 0:
        flash(
            f"Cannot delete '{location.name}' — "
            f"{equipment_count} equipment item"
            f"{'s are' if equipment_count != 1 else ' is'} "
            f"still located here.",
            "warning",
        )
        return redirect(url_for("locations.index"))

    location_name = location.name
    location_db_id = location.id

    db.session.delete(location)

    log_activity(
        "delete",
        "Location",
        location_db_id,
        f"Deleted location {location_name}",
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "The location could not be deleted. "
            "Please try again.",
            "danger",
        )
        return redirect(url_for("locations.index"))

    flash(
        f"Location '{location_name}' was deleted.",
        "success",
    )
    return redirect(url_for("locations.index"))