"""
IEMS Global Search

Cross-entity search from the top bar. Returns grouped
results across all major entities. No filters — global
search is deliberately simple.
"""

from flask import (
    Blueprint,
    render_template,
    request,
)

from app.extensions import db
from app.models import (
    Equipment,
    User,
    EquipmentAssignment,
    Department,
    Location,
)
from app.auth.decorators import login_required


search_bp = Blueprint(
    "search",
    __name__,
    url_prefix="/search",
)


PER_GROUP = 20


@search_bp.route("/")
@login_required
def index():
    """Global search across all entities."""

    q = request.args.get("q", "").strip()

    if not q:
        return render_template(
            "search/index.html",
            query="",
            equipment=[],
            users=[],
            assignments=[],
            departments=[],
            locations=[],
            total=0,
        )

    term = f"%{q}%"

    equipment_matches = (
        Equipment.query
        .filter(
            db.or_(
                Equipment.asset_tag.ilike(term),
                Equipment.serial_number.ilike(term),
                Equipment.manufacturer.ilike(term),
                Equipment.model.ilike(term),
            )
        )
        .order_by(Equipment.asset_tag.asc())
        .limit(PER_GROUP)
        .all()
    )

    user_matches = (
        User.query
        .filter(
            db.or_(
                User.employee_number.ilike(term),
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
            )
        )
        .order_by(User.first_name.asc())
        .limit(PER_GROUP)
        .all()
    )

    # Assignment search: match by equipment asset_tag or
    # user full name via joins.
    assignment_matches = (
        EquipmentAssignment.query
        .join(Equipment, EquipmentAssignment.equipment_id == Equipment.id)
        .join(User, EquipmentAssignment.user_id == User.id)
        .filter(
            db.or_(
                Equipment.asset_tag.ilike(term),
                User.first_name.ilike(term),
                User.last_name.ilike(term),
            )
        )
        .order_by(EquipmentAssignment.assigned_at.desc())
        .limit(PER_GROUP)
        .all()
    )

    department_matches = (
        Department.query
        .filter(Department.name.ilike(term))
        .order_by(Department.name.asc())
        .limit(PER_GROUP)
        .all()
    )

    location_matches = (
        Location.query
        .filter(Location.name.ilike(term))
        .order_by(Location.name.asc())
        .limit(PER_GROUP)
        .all()
    )

    total = (
        len(equipment_matches)
        + len(user_matches)
        + len(assignment_matches)
        + len(department_matches)
        + len(location_matches)
    )

    return render_template(
        "search/index.html",
        query=q,
        equipment=equipment_matches,
        users=user_matches,
        assignments=assignment_matches,
        departments=department_matches,
        locations=location_matches,
        total=total,
    )
