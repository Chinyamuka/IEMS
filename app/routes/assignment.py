"""
IEMS Equipment Assignment Routes

Handles assigning and returning ICT equipment.
Every mutation is recorded in the activity log and
invalidates the dashboard cache.
"""

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
)

from app.extensions import db
from app.models import (
    Equipment,
    User,
    EquipmentAssignment,
)
from app.forms.assignment import EquipmentAssignmentForm
from app.utils.activity import log_activity
from app.utils.cache import cache_delete
from app.routes.dashboard import CACHE_KEY_DASHBOARD_STATS


# =========================================================
# BLUEPRINT
# =========================================================

assignment_bp = Blueprint(
    "assignment",
    __name__,
    url_prefix="/assignments",
)


# =========================================================
# RBAC
# =========================================================

ASSIGNMENT_MANAGEMENT_ROLES = {
    "administrator",
    "asset officer",
    "it manager",
    "it officer",
}


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def can_manage_assignments():
    user = get_current_user()
    if not user or not user.is_active:
        return False
    role = (user.role or "").strip().lower()
    return role in ASSIGNMENT_MANAGEMENT_ROLES


def require_login():
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))
    if not user.is_active:
        session.clear()
        flash(
            "Your account is inactive. Please contact an administrator.",
            "danger",
        )
        return redirect(url_for("auth.login"))
    return None


def require_assignment_management():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    if not can_manage_assignments():
        flash(
            "You do not have permission to manage equipment assignments.",
            "danger",
        )
        return redirect(url_for("assignment.index"))
    return None


# =========================================================
# ASSIGN EQUIPMENT
# =========================================================

@assignment_bp.route("/new", methods=["GET", "POST"])
def create():
    """Assign available ICT equipment to an active user."""

    permission_redirect = require_assignment_management()
    if permission_redirect:
        return permission_redirect

    form = EquipmentAssignmentForm()

    active_assignment_ids = (
        db.session.query(EquipmentAssignment.equipment_id)
        .filter(EquipmentAssignment.returned_at.is_(None))
    )

    equipment = (
        Equipment.query
        .filter(~Equipment.id.in_(active_assignment_ids))
        .filter(Equipment.status == "In Stock")
        .order_by(Equipment.asset_tag.asc())
        .all()
    )

    form.equipment_id.choices = [
        (item.id, f"{item.asset_tag} — {item.manufacturer} {item.model}")
        for item in equipment
    ]

    users = (
        User.query
        .filter_by(is_active=True)
        .order_by(User.first_name.asc(), User.last_name.asc())
        .all()
    )

    form.user_id.choices = [
        (user.id, f"{user.full_name} ({user.employee_number})")
        for user in users
    ]

    if form.validate_on_submit():

        equipment_item = db.session.get(Equipment, form.equipment_id.data)
        if not equipment_item:
            flash("The selected equipment could not be found.", "danger")
            return redirect(url_for("assignment.create"))

        user = db.session.get(User, form.user_id.data)
        if not user:
            flash("The selected employee could not be found.", "danger")
            return redirect(url_for("assignment.create"))

        if not user.is_active:
            flash("The selected employee account is inactive.", "warning")
            return redirect(url_for("assignment.create"))

        if equipment_item.status != "In Stock":
            flash(
                "Only equipment currently marked 'In Stock' can be assigned.",
                "warning",
            )
            return redirect(url_for("assignment.create"))

        existing_assignment = (
            EquipmentAssignment.query
            .filter_by(equipment_id=equipment_item.id, returned_at=None)
            .first()
        )

        if existing_assignment:
            flash("This equipment is already assigned.", "warning")
            return redirect(url_for("assignment.create"))

        assignment = EquipmentAssignment(
            equipment_id=equipment_item.id,
            user_id=user.id,
            assigned_at=form.assigned_at.data,
            notes=form.notes.data,
        )

        db.session.add(assignment)
        equipment_item.status = "Assigned"

        db.session.flush()

        log_activity(
            "assign",
            "EquipmentAssignment",
            assignment.id,
            f"Assigned {equipment_item.asset_tag} to {user.full_name}",
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "The equipment assignment could not be completed. Please try again.",
                "danger",
            )
            return redirect(url_for("assignment.create"))

        cache_delete(CACHE_KEY_DASHBOARD_STATS)

        flash(
            f"{equipment_item.asset_tag} has been assigned to {user.full_name}.",
            "success",
        )
        return redirect(url_for("assignment.index"))

    return render_template(
        "assignment/create.html",
        form=form,
    )


# =========================================================
# ASSIGNMENT HISTORY
# =========================================================

@assignment_bp.route("/")
def index():
    """Display assignment history."""

    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    assignments = (
        EquipmentAssignment.query
        .order_by(EquipmentAssignment.assigned_at.desc())
        .all()
    )

    current_user = get_current_user()
    can_manage = can_manage_assignments()

    return render_template(
        "assignment/index.html",
        assignments=assignments,
        current_user=current_user,
        can_manage=can_manage,
    )


# =========================================================
# RETURN EQUIPMENT
# =========================================================

@assignment_bp.route("/<int:assignment_id>/return", methods=["POST"])
def return_equipment(assignment_id):
    """Return currently assigned equipment."""

    permission_redirect = require_assignment_management()
    if permission_redirect:
        return permission_redirect

    assignment = db.session.get(EquipmentAssignment, assignment_id)

    if not assignment:
        flash("The assignment could not be found.", "danger")
        return redirect(url_for("assignment.index"))

    if not assignment.is_active:
        flash("This equipment has already been returned.", "warning")
        return redirect(url_for("assignment.index"))

    asset_tag = assignment.equipment.asset_tag
    holder_name = assignment.user.full_name

    assignment.returned_at = datetime.utcnow()
    assignment.equipment.status = "In Stock"

    log_activity(
        "return",
        "EquipmentAssignment",
        assignment.id,
        f"Returned {asset_tag} from {holder_name}",
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "The equipment could not be returned. Please try again.",
            "danger",
        )
        return redirect(url_for("assignment.index"))

    cache_delete(CACHE_KEY_DASHBOARD_STATS)

    flash(
        f"{asset_tag} has been returned from {holder_name}.",
        "success",
    )
    return redirect(url_for("assignment.index"))