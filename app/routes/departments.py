"""
IEMS Department Management Routes

Administrator-only CRUD for the Department lookup table.
Every mutation is recorded in the activity log.
"""
from app.utils.cache import get_cached_departments, invalidate_departments

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from app.extensions import db
from app.models import Department, User
from app.auth.decorators import login_required
from app.utils.permissions import role_required
from app.utils.activity import log_activity


# =========================================================
# BLUEPRINT
# =========================================================

departments_bp = Blueprint(
    "departments",
    __name__,
    url_prefix="/departments",
)


# =========================================================
# HELPER
# =========================================================

def _name_in_use(name, exclude_id=None):
    """
    True if a Department with this name already exists
    (case-insensitive). exclude_id is used by the edit
    route so saving unchanged data does not report a
    false duplicate.
    """
    query = Department.query.filter(
        db.func.lower(Department.name) == name.lower()
    )

    if exclude_id is not None:
        query = query.filter(Department.id != exclude_id)

    return query.first() is not None


# =========================================================
# LIST
# =========================================================

@departments_bp.route("/")
@login_required
@role_required("Administrator")
def index():
    """Display all departments."""
    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    return render_template(
        "departments/index.html",
        departments=departments,
    )


# =========================================================
# CREATE
# =========================================================

@departments_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def create():
    """Create a new department."""

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Department name is required.", "danger")
            return render_template("departments/create.html")

        if _name_in_use(name):
            flash(
                f"A department named '{name}' already exists.",
                "danger",
            )
            return render_template("departments/create.html")

        department = Department(
            name=name,
            description=description or None,
        )

        db.session.add(department)

        # flush() populates department.id for the log's
        # entity_id column. Rolled back with the commit if
        # anything fails.
        db.session.flush()

        log_activity(
            "create",
            "Department",
            department.id,
            f"Created department {department.name}",
        )

        try:
            db.session.commit()
            invalidate_departments()
        except Exception:
            db.session.rollback()
            flash(
                "The department could not be saved. "
                "Please try again.",
                "danger",
            )
            return render_template("departments/create.html")

        flash(
            f"Department '{department.name}' was created.",
            "success",
        )
        return redirect(url_for("departments.index"))

    return render_template("departments/create.html")


# =========================================================
# EDIT
# =========================================================

@departments_bp.route("/<int:department_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def edit(department_id):
    """Edit an existing department."""

    department = db.get_or_404(Department, department_id)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Department name is required.", "danger")
            return render_template(
                "departments/edit.html",
                department=department,
            )

        if _name_in_use(name, exclude_id=department.id):
            flash(
                f"A department named '{name}' already exists.",
                "danger",
            )
            return render_template(
                "departments/edit.html",
                department=department,
            )

        department.name = name
        department.description = description or None

        log_activity(
            "update",
            "Department",
            department.id,
            f"Updated department {department.name}",
        )

        try:
            db.session.commit()
            invalidate_departments()
        except Exception:
            db.session.rollback()
            flash(
                "The department could not be saved. "
                "Please try again.",
                "danger",
            )
            return render_template(
                "departments/edit.html",
                department=department,
            )

        flash(
            f"Department '{department.name}' was updated.",
            "success",
        )
        return redirect(url_for("departments.index"))

    return render_template(
        "departments/edit.html",
        department=department,
    )


# =========================================================
# DELETE
# =========================================================

@departments_bp.route("/<int:department_id>/delete", methods=["POST"])
@login_required
@role_required("Administrator")
def delete(department_id):
    """
    Delete a department.

    POST-only. Server-side guard refuses to remove a
    department that still has users assigned.
    """

    department = db.get_or_404(Department, department_id)

    # -----------------------------------------------------
    # REFERENCE GUARD
    # -----------------------------------------------------

    user_count = User.query.filter_by(
        department_id=department.id
    ).count()

    if user_count > 0:
        flash(
            f"Cannot delete '{department.name}' — "
            f"{user_count} user"
            f"{'s are' if user_count != 1 else ' is'} "
            f"still assigned to it.",
            "warning",
        )
        return redirect(url_for("departments.index"))

    # -----------------------------------------------------
    # CAPTURE FOR LOG
    # -----------------------------------------------------
    #
    # Capture the name before deletion. After commit the
    # row is gone and its attributes are no longer safe
    # to access.

    department_name = department.name
    department_db_id = department.id

    db.session.delete(department)

    log_activity(
        "delete",
        "Department",
        department_db_id,
        f"Deleted department {department_name}",
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "The department could not be deleted. "
            "Please try again.",
            "danger",
        )
        return redirect(url_for("departments.index"))

    flash(
        f"Department '{department_name}' was deleted.",
        "success",
    )
    return redirect(url_for("departments.index"))