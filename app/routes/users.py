"""
IEMS Employee Management Routes

Handles:
- Employee listing
- Employee creation
- Employee details
- Employee editing
- Employee deactivation
- Employee reactivation

Authentication and RBAC will be connected to these routes
as the security layer is implemented.
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
from app.models import User, Department

# =========================================================
# BLUEPRINT
# =========================================================

users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/users"
)


# =========================================================
# EMPLOYEE LIST
# =========================================================

@users_bp.route("/")
def index():
    """Display all employees with optional search."""

    search = request.args.get(
        "search",
        "",
        type=str
    ).strip()

    query = User.query

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:

        search_pattern = f"%{search}%"

        query = query.filter(
            db.or_(
                User.employee_number.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    # -----------------------------------------------------
    # ORDERING
    # -----------------------------------------------------

    users = query.order_by(
        User.first_name.asc(),
        User.last_name.asc()
    ).all()

    return render_template(
        "users/index.html",
        users=users,
        search=search
    )


# =========================================================
# CREATE EMPLOYEE
# =========================================================

@users_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new employee account."""

    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        employee_number = request.form.get(
            "employee_number",
            ""
        ).strip()

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        department_id = request.form.get(
            "department_id"
        )

        # -------------------------------------------------
        # GET PASSWORD DATA
        # -------------------------------------------------

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not employee_number:

            flash(
                "Employee number is required.",
                "danger"
            )

            return render_template(
                "users/create.html",
                departments=departments
            )

        if not first_name:

            flash(
                "First name is required.",
                "danger"
            )

            return render_template(
                "users/create.html",
                departments=departments
            )

        if not last_name:

            flash(
                "Last name is required.",
                "danger"
            )

            return render_template(
                "users/create.html",
                departments=departments
            )

        # -------------------------------------------------
        # PASSWORD VALIDATION
        # -------------------------------------------------

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "users/create.html",
                departments=departments
            )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )

            return render_template(
                "users/create.html",
                departments=departments
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "users/create.html",
                departments=departments
            )

        # -------------------------------------------------
        # DUPLICATE EMPLOYEE NUMBER
        # -------------------------------------------------

        existing_employee = User.query.filter_by(
            employee_number=employee_number
        ).first()

        if existing_employee:

            flash(
                "That employee number already exists.",
                "danger"
            )

            return render_template(
                "users/create.html",
                departments=departments
            )

        # -------------------------------------------------
        # DUPLICATE EMAIL
        # -------------------------------------------------

        if email:

            existing_email = User.query.filter_by(
                email=email
            ).first()

            if existing_email:

                flash(
                    "That email address is already in use.",
                    "danger"
                )

                return render_template(
                    "users/create.html",
                    departments=departments
                )

        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        user = User(
            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name,
            email=email or None,
            phone=phone or None,
            department_id=(
                int(department_id)
                if department_id
                else None
            ),
            is_active=True
        )

        # -------------------------------------------------
        # HASH PASSWORD
        # -------------------------------------------------

        # IMPORTANT:
        # Never store the plain-text password.
        #
        # set_password() uses Werkzeug's secure
        # password hashing implementation.
        user.set_password(password)

        # -------------------------------------------------
        # SAVE USER
        # -------------------------------------------------

        db.session.add(user)
        db.session.commit()

        flash(
            f"{user.full_name} was added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "users.detail",
                user_id=user.id
            )
        )

    # -----------------------------------------------------
    # DISPLAY FORM
    # -----------------------------------------------------

    return render_template(
        "users/create.html",
        departments=departments
    )


# =========================================================
# EMPLOYEE DETAILS
# =========================================================

@users_bp.route("/<int:user_id>")
def detail(user_id):
    """Display employee details."""

    user = db.get_or_404(
        User,
        user_id
    )

    return render_template(
        "users/detail.html",
        user=user
    )


# =========================================================
# EDIT EMPLOYEE
# =========================================================

@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
def edit(user_id):
    """Edit an existing employee."""

    user = db.get_or_404(
        User,
        user_id
    )

    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        employee_number = request.form.get(
            "employee_number",
            ""
        ).strip()

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        department_id = request.form.get(
            "department_id"
        )

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not employee_number or not first_name or not last_name:

            flash(
                "Employee number, first name and last name are required.",
                "danger"
            )

            return render_template(
                "users/edit.html",
                user=user,
                departments=departments
            )

        # -------------------------------------------------
        # CHECK EMPLOYEE NUMBER
        # -------------------------------------------------

        duplicate_employee = User.query.filter(
            User.employee_number == employee_number,
            User.id != user.id
        ).first()

        if duplicate_employee:

            flash(
                "That employee number is already assigned to another employee.",
                "danger"
            )

            return render_template(
                "users/edit.html",
                user=user,
                departments=departments
            )

        # -------------------------------------------------
        # CHECK EMAIL
        # -------------------------------------------------

        if email:

            duplicate_email = User.query.filter(
                User.email == email,
                User.id != user.id
            ).first()

            if duplicate_email:

                flash(
                    "That email address is already in use.",
                    "danger"
                )

                return render_template(
                    "users/edit.html",
                    user=user,
                    departments=departments
                )

        # -------------------------------------------------
        # UPDATE EMPLOYEE
        # -------------------------------------------------

        user.employee_number = employee_number
        user.first_name = first_name
        user.last_name = last_name
        user.email = email or None
        user.phone = phone or None

        user.department_id = (
            int(department_id)
            if department_id
            else None
        )

        db.session.commit()

        flash(
            f"{user.full_name} was updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "users.detail",
                user_id=user.id
            )
        )

    # -----------------------------------------------------
    # DISPLAY EDIT FORM
    # -----------------------------------------------------

    return render_template(
        "users/edit.html",
        user=user,
        departments=departments
    )


# =========================================================
# DEACTIVATE EMPLOYEE
# =========================================================

@users_bp.route(
    "/<int:user_id>/deactivate",
    methods=["POST"]
)
def deactivate(user_id):
    """
    Deactivate an employee.

    We deliberately do not delete the employee record.
    Historical equipment assignments must remain intact.
    """

    user = db.get_or_404(
        User,
        user_id
    )

    user.is_active = False

    db.session.commit()

    flash(
        f"{user.full_name} has been deactivated.",
        "success"
    )

    return redirect(
        url_for(
            "users.detail",
            user_id=user.id
        )
    )


# =========================================================
# REACTIVATE EMPLOYEE
# =========================================================

@users_bp.route(
    "/<int:user_id>/activate",
    methods=["POST"]
)
def activate(user_id):
    """Reactivate an employee."""

    user = db.get_or_404(
        User,
        user_id
    )

    user.is_active = True

    db.session.commit()

    flash(
        f"{user.full_name} has been reactivated.",
        "success"
    )
    return redirect(
        url_for(
            "users.detail",
            user_id=user.id
        )
    )