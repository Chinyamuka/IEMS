"""
IEMS Employee Management Routes

Administrator-only employee management. Every mutation
is recorded in the activity log.
"""
from app.utils.cache import get_cached_departments

import secrets
from app.auth.decorators import login_required
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    g,
)

from app.extensions import db
from app.models import User, Department
from app.utils.uploads import (
    save_image,
    delete_image,
    ImageUploadError,
)
from app.utils.activity import log_activity
from app.utils.permissions import role_required

# =========================================================
# HELPERS
# =========================================================

def generate_temp_password():
    """
    Produce a random temporary password of the form
    IEMS-XXXXXX, where X is a decimal digit.

    Uses secrets.choice rather than random.choice: the
    latter is not cryptographically secure and could
    allow an attacker to predict generated passwords
    from earlier observations.

    Six digits gives 10^6 = 1,000,000 possibilities.
    Combined with must_change_password=True (so the
    password only works once) and short admin-mediated
    handoff, this is sufficient. If we ever add
    self-service password reset via email, we would
    increase the entropy.
    """
    digits = "".join(
        secrets.choice("0123456789")
        for _ in range(6)
    )
    return f"IEMS-{digits}"


# =========================================================
# BLUEPRINT
# =========================================================


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
@role_required("Administrator")
def index():
    """Display all employees with optional search."""

    search = request.args.get(
        "search", "", type=str
    ).strip()

    query = User.query

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
@role_required("Administrator")
def create():
    """Create a new employee account."""

    departments = get_cached_departments()

    if request.method == "POST":

        employee_number = request.form.get("employee_number", "").strip()
        first_name      = request.form.get("first_name", "").strip()
        last_name       = request.form.get("last_name", "").strip()
        email           = request.form.get("email", "").strip()
        phone           = request.form.get("phone", "").strip()
        department_id   = request.form.get("department_id")
        password        = request.form.get("password", "")
        confirm_password= request.form.get("confirm_password", "")

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

        user.set_password(password)

        db.session.add(user)

        # flush() populates user.id for the log's entity_id.
        db.session.flush()

        log_activity(
            "create",
            "User",
            user.id,
            f"Created user {user.employee_number} "
            f"({user.full_name})",
        )

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
@role_required("Administrator")
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
@role_required("Administrator")
def edit(user_id):
    """
    Edit an existing employee, with optional profile-photo
    upload.

    Ordering matters:
        save file  ->  assign fields  ->  commit  ->  delete old file
    """

    user = db.get_or_404(User, user_id)

    departments = Department.query.order_by(
        Department.name.asc()
    ).all()

    if request.method == "POST":

        employee_number = request.form.get("employee_number", "").strip()
        first_name      = request.form.get("first_name", "").strip()
        last_name       = request.form.get("last_name", "").strip()
        email           = request.form.get("email", "").strip()
        phone           = request.form.get("phone", "").strip()
        department_id   = request.form.get("department_id")

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

        user.employee_number = employee_number
        user.first_name = first_name
        user.last_name = last_name
        user.email = email or None
        user.phone = phone or None

        user.department_id = (
            int(department_id) if department_id else None
        )

        if new_image_filename is not None:
            user.profile_image = new_image_filename

        log_activity(
            "update",
            "User",
            user.id,
            f"Updated user {user.employee_number}",
        )

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()

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

@users_bp.route("/<int:user_id>/deactivate",methods=["POST"])
@login_required
@role_required("Administrator")
def deactivate(user_id):
    """
    Deactivate an employee.

    Two guards prevent Administrator lockout:

    1. An admin cannot deactivate their own account.
    2. An admin cannot deactivate the last active
       Administrator.
    """

    user = db.get_or_404(User, user_id)

    # Guard 1 — self-deactivation
    if g.current_user is not None and user.id == g.current_user.id:
        flash(
            "You cannot deactivate your own account.",
            "warning"
        )
        return redirect(
            url_for("users.detail", user_id=user.id)
        )

    # Guard 2 — last active Administrator
    if user.role == "Administrator":
        active_admin_count = User.query.filter_by(
            role="Administrator",
            is_active=True,
        ).count()

        if active_admin_count <= 1:
            flash(
                "You cannot deactivate the last active "
                "Administrator.",
                "warning"
            )
            return redirect(
                url_for("users.detail", user_id=user.id)
            )

    user.is_active = False

    log_activity(
        "deactivate",
        "User",
        user.id,
        f"Deactivated user {user.employee_number}",
    )

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

@users_bp.route("/<int:user_id>/activate",methods=["POST"])
@login_required
@role_required("Administrator")
def activate(user_id):
    """Reactivate an employee."""

    user = db.get_or_404(User, user_id)

    user.is_active = True

    log_activity(
        "activate",
        "User",
        user.id,
        f"Activated user {user.employee_number}",
    )

    db.session.commit()

    flash(
        f"{user.full_name} has been reactivated.",
        "success"
    )

    return redirect(
        url_for("users.detail", user_id=user.id)
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@users_bp.route( "/<int:user_id>/reset-password",  methods=["POST"])
@login_required
@role_required("Administrator")
def reset_password(user_id):
    """
    Admin-initiated password reset.

    Generates a random temporary password, stores only
    its hash, sets must_change_password=True so the user
    is forced to change it on the next login, and flashes
    the plaintext one time so the administrator can hand
    it to the employee.

    The plaintext is never written to the database.
    """

    user = db.get_or_404(User, user_id)

    # -----------------------------------------------------
    # GUARD — CANNOT RESET YOUR OWN PASSWORD HERE
    # -----------------------------------------------------

    if g.current_user is not None and user.id == g.current_user.id:
        flash(
            "Use the Profile page to change your own password.",
            "warning"
        )
        return redirect(
            url_for("users.detail", user_id=user.id)
        )

    # -----------------------------------------------------
    # GENERATE + STORE
    # -----------------------------------------------------

    temp_password = generate_temp_password()

    user.set_password(temp_password)
    user.must_change_password = True

    log_activity(
        "password_reset",
        "User",
        user.id,
        f"Reset password for {user.employee_number}",
    )

    db.session.commit()

    # -----------------------------------------------------
    # FLASH THE TEMP PASSWORD — SHOWN ONCE
    # -----------------------------------------------------

    flash(
        f"Password reset for {user.full_name}. "
        f"Temporary password: {temp_password}. "
        f"The user must change it on next login.",
        "success"
    )

    return redirect(
        url_for("users.detail", user_id=user.id)
    )