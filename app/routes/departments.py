"""
IEMS Department Management Routes

Administrator-only CRUD for the Department lookup table.

Departments are referenced by User.department_id. Deleting
a department that still has users attached is blocked (see
the delete route).

Routes:
    GET  /departments/                  - list all
    GET  /departments/new               - display create form
    POST /departments/new               - save new
    GET  /departments/<id>/edit         - display edit form
    POST /departments/<id>/edit         - save changes
    GET  /departments/<id>/delete       - display confirm
    POST /departments/<id>/delete       - delete
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
from app.models import Department
from app.auth.decorators import login_required
from app.utils.permissions import role_required

departments_bp = Blueprint('departments', __name__, url_prefix='/departments')

# LISTING THE DEPARTMENTS

@departments_bp.route('/')
@login_required
@role_required("Administrator")
def index():
    """ Display all departments """
    departments = Department.query.order_by(Department.name.asc).all()
    return render_template("departments/index.html", departments=departments)

# CREATING THE DEPARTMENTS

@departments_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required("Administrator")
def create():
    """ Create a new department """
    if request.method == 'POST':
        flash("Not implemented yet", "warning")
        return redirect(url_for('departments.index'))
    return render_template("departments/create.html")


# EDITING THE DEPT

@departments_bp.route('/<id>', methods=['GET', 'POST'])
@login_required
@role_required("Administrator")
def edit(department_id):
    """ Edit an existing department """
    department = db.get_or_404(Department, department_id)
    if request.method == 'POST':
        flash("Not implemented yet", "warning")
        return redirect(url_for('departments.index'))
    return render_template("departments/edit.html", department=department)


# =========================================================
# DELETE
# =========================================================

@departments_bp.route("/<int:department_id>/delete", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def delete(department_id):
    """
    Delete a department.
    """
    department = db.get_or_404(Department, department_id)
    if request.method == "POST":
        flash("Not implemented yet.", "warning")
        return redirect(url_for("departments.index"))
    return render_template(
        "departments/delete.html",
        department=department,
    )