"""
IEMS Equipment Assignment Routes

Handles assigning ICT equipment to users and viewing
assignment history.
"""

from flask import Blueprint, render_template, redirect, url_for, flash

from app.extensions import db
from app.models import Equipment, User, EquipmentAssignment
from app.forms.assignment import EquipmentAssignmentForm


# ---------------------------------------------------------
# BLUEPRINT
# ---------------------------------------------------------
assignment_bp = Blueprint(
    "assignment",
    __name__,
    url_prefix="/assignments"
)


# ---------------------------------------------------------
# ASSIGN EQUIPMENT
# ---------------------------------------------------------
@assignment_bp.route("/new", methods=["GET", "POST"])
def create():
    """
    Assign an available piece of equipment to a user.
    """

    form = EquipmentAssignmentForm()

    # -----------------------------------------------------
    # LOAD EQUIPMENT
    # -----------------------------------------------------
    # Only equipment that is not currently assigned should
    # appear in the equipment dropdown.
    active_assignment_ids = db.session.query(
        EquipmentAssignment.equipment_id
    ).filter(
        EquipmentAssignment.returned_at.is_(None)
    )

    equipment = Equipment.query.filter(
        ~Equipment.id.in_(active_assignment_ids)
    ).order_by(
        Equipment.asset_tag.asc()
    ).all()

    form.equipment_id.choices = [
        (
            item.id,
            f"{item.asset_tag} — {item.manufacturer} {item.model}"
        )
        for item in equipment
    ]

    # -----------------------------------------------------
    # LOAD ACTIVE USERS
    # -----------------------------------------------------
    # Only active users should be available for assignment.
    users = User.query.filter_by(
        is_active=True
    ).order_by(
        User.first_name.asc(),
        User.last_name.asc()
    ).all()

    form.user_id.choices = [
        (
            user.id,
            f"{user.full_name} ({user.employee_number})"
        )
        for user in users
    ]

    # -----------------------------------------------------
    # PROCESS FORM
    # -----------------------------------------------------
    if form.validate_on_submit():

        # Find the selected equipment.
        equipment_item = db.session.get(
            Equipment,
            form.equipment_id.data
        )

        # Find the selected user.
        user = db.session.get(
            User,
            form.user_id.data
        )

        # Safety check in case a record was deleted
        # between loading the page and submitting it.
        if not equipment_item or not user:
            flash(
                "The selected equipment or user could not be found.",
                "danger"
            )

            return redirect(
                url_for("assignment.create")
            )

        # -------------------------------------------------
        # DOUBLE-CHECK CURRENT ASSIGNMENT
        # -------------------------------------------------
        # This prevents assigning the same equipment twice.
        existing_assignment = EquipmentAssignment.query.filter_by(
            equipment_id=equipment_item.id,
            returned_at=None
        ).first()

        if existing_assignment:
            flash(
                "This equipment is already assigned.",
                "warning"
            )

            return redirect(
                url_for("assignment.create")
            )

        # -------------------------------------------------
        # CREATE ASSIGNMENT
        # -------------------------------------------------
        assignment = EquipmentAssignment(
            equipment_id=equipment_item.id,
            user_id=user.id,
            assigned_at=form.assigned_at.data,
            notes=form.notes.data
        )

        db.session.add(assignment)

        # -------------------------------------------------
        # UPDATE EQUIPMENT STATUS
        # -------------------------------------------------
        # The equipment is no longer in stock.
        equipment_item.status = "Assigned"

        # Save everything to PostgreSQL.
        db.session.commit()

        flash(
            f"{equipment_item.asset_tag} has been assigned to "
            f"{user.full_name}.",
            "success"
        )

        return redirect(
            url_for(
                "equipment.detail",
                equipment_id=equipment_item.id
            )
        )

    return render_template(
        "assignment/create.html",
        form=form
    )


# ---------------------------------------------------------
# ASSIGNMENT HISTORY
# ---------------------------------------------------------
@assignment_bp.route("/")
def index():
    """
    Display all equipment assignments.

    The newest assignments appear first.
    """

    assignments = EquipmentAssignment.query.order_by(
        EquipmentAssignment.assigned_at.desc()
    ).all()

    return render_template(
        "assignment/index.html",
        assignments=assignments
    )