"""
IEMS Equipment Assignment Routes

Handles:

- Viewing assignment history
- Assigning equipment to employees
- Returning equipment
- Equipment status updates
- RBAC protection for assignment operations

RBAC:

Administrator
    - View assignments
    - Assign equipment
    - Return equipment

Asset Officer
    - View assignments
    - Assign equipment
    - Return equipment

IT Manager
    - View assignments
    - Assign equipment
    - Return equipment

IT Officer
    - View assignments
    - Assign equipment
    - Return equipment

Employee
    - View assignment history
    - Cannot assign equipment
    - Cannot return equipment
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

# Store normalized role names.
#
# We convert the database role to lowercase before checking,
# so these all work correctly:
#
# Administrator
# administrator
# ADMINISTRATOR
#
# The same applies to the other roles.

ASSIGNMENT_MANAGEMENT_ROLES = {
    "administrator",
    "asset officer",
    "it manager",
    "it officer",
}


def get_current_user():
    """
    Get the currently logged-in User from the database.

    The session stores only the user's ID.

    We deliberately retrieve the actual User record from
    PostgreSQL so that authorization always uses the current
    database role.
    """

    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(
        User,
        user_id,
    )


def is_authenticated():
    """
    Check whether the current user exists and is active.
    """

    user = get_current_user()

    return (
        user is not None
        and user.is_active
    )


def can_manage_assignments():
    """
    Check whether the current user can:

    - Assign equipment
    - Return equipment
    """

    user = get_current_user()

    if not user:
        return False

    if not user.is_active:
        return False

    # Normalize the role from the database.
    role = (
        user.role or ""
    ).strip().lower()

    return role in ASSIGNMENT_MANAGEMENT_ROLES


def require_login():
    """
    Require an authenticated active user.

    Returns:
        Redirect response when authentication fails.
        None when authentication succeeds.
    """

    user = get_current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )

    if not user.is_active:

        session.clear()

        flash(
            "Your account is inactive. "
            "Please contact an administrator.",
            "danger",
        )

        return redirect(
            url_for("auth.login")
        )

    return None


def require_assignment_management():
    """
    Require permission to manage equipment assignments.

    Authorized roles:

        Administrator
        Asset Officer
        IT Manager
        IT Officer
    """

    # -----------------------------------------------------
    # AUTHENTICATION
    # -----------------------------------------------------

    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    # -----------------------------------------------------
    # RBAC
    # -----------------------------------------------------

    if not can_manage_assignments():

        flash(
            "You do not have permission to manage "
            "equipment assignments.",
            "danger",
        )

        return redirect(
            url_for("assignment.index")
        )

    return None


# =========================================================
# ASSIGN EQUIPMENT
# =========================================================

@assignment_bp.route(
    "/new",
    methods=["GET", "POST"],
)
def create():
    """
    Assign available ICT equipment to an active user.

    Only authorized operational roles can perform this
    operation.
    """

    # -----------------------------------------------------
    # RBAC
    # -----------------------------------------------------

    permission_redirect = (
        require_assignment_management()
    )

    if permission_redirect:
        return permission_redirect

    # -----------------------------------------------------
    # FORM
    # -----------------------------------------------------

    form = EquipmentAssignmentForm()

    # -----------------------------------------------------
    # AVAILABLE EQUIPMENT
    # -----------------------------------------------------

    # Find equipment that already has an active assignment.
    active_assignment_ids = (
        db.session.query(
            EquipmentAssignment.equipment_id
        )
        .filter(
            EquipmentAssignment.returned_at.is_(None)
        )
    )

    # Only equipment without an active assignment
    # should be available.
    equipment = (
        Equipment.query
        .filter(
            ~Equipment.id.in_(
                active_assignment_ids
            )
        )
        .filter(
            Equipment.status == "In Stock"
        )
        .order_by(
            Equipment.asset_tag.asc()
        )
        .all()
    )

    form.equipment_id.choices = [
        (
            item.id,
            f"{item.asset_tag} — "
            f"{item.manufacturer} {item.model}",
        )
        for item in equipment
    ]

    # -----------------------------------------------------
    # ACTIVE USERS
    # -----------------------------------------------------

    users = (
        User.query
        .filter_by(
            is_active=True
        )
        .order_by(
            User.first_name.asc(),
            User.last_name.asc(),
        )
        .all()
    )

    form.user_id.choices = [
        (
            user.id,
            f"{user.full_name} "
            f"({user.employee_number})",
        )
        for user in users
    ]

    # -----------------------------------------------------
    # PROCESS FORM
    # -----------------------------------------------------

    if form.validate_on_submit():

        # -------------------------------------------------
        # FIND EQUIPMENT
        # -------------------------------------------------

        equipment_item = db.session.get(
            Equipment,
            form.equipment_id.data,
        )

        if not equipment_item:

            flash(
                "The selected equipment could not be found.",
                "danger",
            )

            return redirect(
                url_for("assignment.create")
            )

        # -------------------------------------------------
        # FIND USER
        # -------------------------------------------------

        user = db.session.get(
            User,
            form.user_id.data,
        )

        if not user:

            flash(
                "The selected employee could not be found.",
                "danger",
            )

            return redirect(
                url_for("assignment.create")
            )

        # -------------------------------------------------
        # CHECK USER
        # -------------------------------------------------

        if not user.is_active:

            flash(
                "The selected employee account is inactive.",
                "warning",
            )

            return redirect(
                url_for("assignment.create")
            )

        # -------------------------------------------------
        # CHECK EQUIPMENT STATUS
        # -------------------------------------------------

        if equipment_item.status != "In Stock":

            flash(
                "Only equipment currently marked "
                "'In Stock' can be assigned.",
                "warning",
            )

            return redirect(
                url_for("assignment.create")
            )

        # -------------------------------------------------
        # CHECK EXISTING ACTIVE ASSIGNMENT
        # -------------------------------------------------

        existing_assignment = (
            EquipmentAssignment.query
            .filter_by(
                equipment_id=equipment_item.id,
                returned_at=None,
            )
            .first()
        )

        if existing_assignment:

            flash(
                "This equipment is already assigned.",
                "warning",
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
            notes=form.notes.data,
        )

        db.session.add(
            assignment
        )

        # -------------------------------------------------
        # UPDATE EQUIPMENT STATUS
        # -------------------------------------------------

        equipment_item.status = "Assigned"

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "The equipment assignment could not be "
                "completed. Please try again.",
                "danger",
            )

            return redirect(
                url_for("assignment.create")
            )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        flash(
            f"{equipment_item.asset_tag} has been assigned "
            f"to {user.full_name}.",
            "success",
        )

        return redirect(
            url_for("assignment.index")
        )

    # -----------------------------------------------------
    # DISPLAY FORM
    # -----------------------------------------------------

    return render_template(
        "assignment/create.html",
        form=form,
    )


# =========================================================
# ASSIGNMENT HISTORY
# =========================================================

@assignment_bp.route("/")
def index():
    """
    Display assignment history.

    All authenticated users can view assignment history.
    """

    # -----------------------------------------------------
    # AUTHENTICATION
    # -----------------------------------------------------

    login_redirect = require_login()

    if login_redirect:
        return login_redirect

    # -----------------------------------------------------
    # LOAD ASSIGNMENTS
    # -----------------------------------------------------

    assignments = (
        EquipmentAssignment.query
        .order_by(
            EquipmentAssignment.assigned_at.desc()
        )
        .all()
    )

    # -----------------------------------------------------
    # CURRENT USER
    # -----------------------------------------------------

    current_user = get_current_user()

    # -----------------------------------------------------
    # MANAGEMENT PERMISSION
    # -----------------------------------------------------

    can_manage = can_manage_assignments()

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render_template(
        "assignment/index.html",
        assignments=assignments,
        current_user=current_user,
        can_manage=can_manage,
    )


# =========================================================
# RETURN EQUIPMENT
# =========================================================

@assignment_bp.route(
    "/<int:assignment_id>/return",
    methods=["GET", "POST"],
)
def return_equipment(assignment_id):
    """
    Return currently assigned equipment.

    GET:
        Display return confirmation.

    POST:
        Complete the return and change equipment status
        back to In Stock.

    Only authorized operational roles may perform this
    operation.
    """

    # -----------------------------------------------------
    # RBAC
    # -----------------------------------------------------

    permission_redirect = (
        require_assignment_management()
    )

    if permission_redirect:
        return permission_redirect

    # -----------------------------------------------------
    # FIND ASSIGNMENT
    # -----------------------------------------------------

    assignment = db.session.get(
        EquipmentAssignment,
        assignment_id,
    )

    if not assignment:

        flash(
            "The assignment could not be found.",
            "danger",
        )

        return redirect(
            url_for("assignment.index")
        )

    # -----------------------------------------------------
    # CHECK ALREADY RETURNED
    # -----------------------------------------------------

    if not assignment.is_active:

        flash(
            "This equipment has already been returned.",
            "warning",
        )

        return redirect(
            url_for("assignment.index")
        )

    # -----------------------------------------------------
    # PROCESS RETURN
    # -----------------------------------------------------

    if request.method == "POST":

        # Record return timestamp.
        assignment.returned_at = datetime.utcnow()

        # Return equipment to inventory.
        assignment.equipment.status = "In Stock"

        # Save changes.
        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "The equipment could not be returned. "
                "Please try again.",
                "danger",
            )

            return redirect(
                url_for("assignment.index")
            )

        flash(
            f"{assignment.equipment.asset_tag} has been "
            f"returned from "
            f"{assignment.user.full_name}.",
            "success",
        )

        return redirect(
            url_for("assignment.index")
        )

    # -----------------------------------------------------
    # DISPLAY CONFIRMATION
    # -----------------------------------------------------

    return render_template(
        "assignment/return.html",
        assignment=assignment,
    )