"""
IEMS Employee Management Routes

Handles:
- Employee listing
- Employee creation
- Employee details
- Employee editing (incl. profile-photo upload)
- Employee deactivation
- Employee reactivation

Authentication and RBAC are enforced by @login_required.
"""

from app.auth.decorators import login_required

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
from app.utils.uploads import (
    save_image,
    delete_image,
    ImageUploadError,
)


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
@login_required
def index():
    """Display all employees with optional search."""

    search = request.args.get(
        "search", "", type=str
    ).strip()

    query = User.query

    # Search across employee number, name, and email.
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                User.employee_number.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

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
@login_required
def create():
    """Create a new employee account."""

    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    if request.method == "POST":

        # -------------------------------------------------
        # READ FIELDS
        # -------------------------------------------------

        employee_number = request.form.get("employee_number", "").strip()
        first_name      = request.form.get("first_name", "").strip()
        last_name       = request.form.get("last_name", "").strip()
        email           = request.form.get("email", "").strip()
        phone           = request.form.get("phone", "").strip()
        department_id   = request.form.get("department_id")
        password        = request.form.get("password", "")
        confirm_password= request.form.get("confirm_password", "")

        # -------------------------------------------------
        # REQUIRED-FIELD VALIDATION
        # -------------------------------------------------

        if not employee_number:
            flash("Employee number is required.", "danger")
            return render_template(
                "users/create.html",
                departments=departments
            )

        if not first_name:
            flash("First name is required.", "danger")
            return render_template(
                "users/create.html",
                departments=departments
            )

        if not last_name:
            flash("Last name is required.", "danger")
            return render_template(
                "users/create.html",
                departments=departments
            )

        # -------------------------------------------------
        # PASSWORD VALIDATION
        # -------------------------------------------------

        if not password:
            flash("Password is required.", "danger")
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
            flash("Passwords do not match.", "danger")
            return render_template(
                "users/create.html",
                departments=departments
            )

        # -------------------------------------------------
        # DUPLICATE CHECKS
        # -------------------------------------------------

        if User.query.filter_by(
            employee_number=employee_number
        ).first():
            flash(
                "That employee number already exists.",
                "danger"
            )
            return render_template(
                "users/create.html",
                departments=departments
            )

        if email and User.query.filter_by(email=email).first():
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
                int(department_id) if department_id else None
            ),
            is_active=True
        )

        # Hashing is owned by the model (see User.set_password).
        # The route never touches password_hash directly.
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(
            f"{user.full_name} was added successfully.",
            "success"
        )

        return redirect(
            url_for("users.detail", user_id=user.id)
        )

    return render_template(
        "users/create.html",
        departments=departments
    )


# =========================================================
# EMPLOYEE DETAILS
# =========================================================

@users_bp.route("/<int:user_id>")
@login_required
def detail(user_id):
    """Display employee details."""

    user = db.get_or_404(User, user_id)

    return render_template(
        "users/detail.html",
        user=user
    )


# =========================================================
# EDIT EMPLOYEE
# =========================================================

@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit(user_id):
    """
    Edit an existing employee, with optional profile-photo upload.

    Ordering matters:
        save file  ->  assign fields  ->  commit  ->  delete old file

    - If the file is invalid, the DB object is untouched.
    - If the commit fails, the newly written file is removed.
    - The previous photo is only deleted after the new filename
      is safely persisted in the database.
    """

    user = db.get_or_404(User, user_id)

    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    if request.method == "POST":

        # -------------------------------------------------
        # READ FIELDS
        # -------------------------------------------------

        employee_number = request.form.get("employee_number", "").strip()
        first_name      = request.form.get("first_name", "").strip()
        last_name       = request.form.get("last_name", "").strip()
        email           = request.form.get("email", "").strip()
        phone           = request.form.get("phone", "").strip()
        department_id   = request.form.get("department_id")

        # -------------------------------------------------
        # REQUIRED-FIELD VALIDATION
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
        # DUPLICATE CHECKS (excluding self)
        # -------------------------------------------------

        if User.query.filter(
            User.employee_number == employee_number,
            User.id != user.id
        ).first():
            flash(
                "That employee number is already assigned "
                "to another employee.",
                "danger"
            )
            return render_template(
                "users/edit.html",
                user=user,
                departments=departments
            )

        if email and User.query.filter(
            User.email == email,
            User.id != user.id
        ).first():
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
        # PROFILE IMAGE
        # -------------------------------------------------
        #
        # save_image returns:
        #   None  -> no file submitted; keep existing photo.
        #   str   -> new filename; file is already on disk.
        #
        # It raises ImageUploadError for invalid uploads.
        #
        # We call it BEFORE mutating the user object so that
        # a bad file never leaves the DB half-updated.
        #

        new_image_filename = None
        old_image_filename = user.profile_image

        try:
            new_image_filename = save_image(
                request.files.get("profile_image"),
                "users"
            )
        except ImageUploadError as error:
            flash(str(error), "danger")
            return render_template(
                "users/edit.html",
                user=user,
                departments=departments
            )

        # -------------------------------------------------
        # ASSIGN FIELDS
        # -------------------------------------------------

        user.employee_number = employee_number
        user.first_name = first_name
        user.last_name = last_name
        user.email = email or None
        user.phone = phone or None

        user.department_id = (
            int(department_id) if department_id else None
        )

        # Only overwrite the filename if a new file was saved.
        if new_image_filename is not None:
            user.profile_image = new_image_filename

        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()

            # Commit failed: the new file (if any) is now an
            # orphan on disk. Remove it so we don't leak.
            if new_image_filename is not None:
                delete_image(new_image_filename, "users")

            flash(
                "Changes could not be saved. Please try again.",
                "danger"
            )
            return render_template(
                "users/edit.html",
                user=user,
                departments=departments
            )

        # -------------------------------------------------
        # DELETE OLD IMAGE (AFTER SUCCESSFUL COMMIT)
        # -------------------------------------------------
        #
        # Safe now: the DB points at the new filename.
        # Only delete if we actually uploaded a new file
        # AND there was a previous one.
        #

        if (
            new_image_filename is not None
            and old_image_filename is not None
        ):
            delete_image(old_image_filename, "users")

        flash(
            f"{user.full_name} was updated successfully.",
            "success"
        )

        return redirect(
            url_for("users.detail", user_id=user.id)
        )

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
@login_required
def deactivate(user_id):
    """
    Deactivate an employee.

    Records are never deleted — historical assignments
    must remain intact.
    """

    user = db.get_or_404(User, user_id)

    user.is_active = False
    db.session.commit()

    flash(
        f"{user.full_name} has been deactivated.",
        "success"
    )

    return redirect(
        url_for("users.detail", user_id=user.id)
    )


# =========================================================
# REACTIVATE EMPLOYEE
# =========================================================

@users_bp.route(
    "/<int:user_id>/activate",
    methods=["POST"]
)
@login_required
def activate(user_id):
    """Reactivate an employee."""

    user = db.get_or_404(User, user_id)

    user.is_active = True
    db.session.commit()

    flash(
        f"{user.full_name} has been reactivated.",
        "success"
    )

    return redirect(
        url_for("users.detail", user_id=user.id)
    )