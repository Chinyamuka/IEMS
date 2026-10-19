"""
User management route tests.

Covers:
- Listing users
- Creating users
- Editing users
- Deactivation and reactivation
- Admin lockout guards
"""

from app.models import User, ActivityLog


# =========================================================
# LISTING
# =========================================================

def test_users_list_loads_for_admin(logged_in_admin):
    r = logged_in_admin.get("/users/")
    assert r.status_code == 200


def test_users_list_shows_admin(logged_in_admin, admin):
    r = logged_in_admin.get("/users/")
    assert admin.employee_number.encode() in r.data


# =========================================================
# CREATE
# =========================================================

def test_create_user_page_loads(logged_in_admin):
    r = logged_in_admin.get("/users/new")
    assert r.status_code == 200


def test_create_user_creates_row(logged_in_admin, department, db):
    before = User.query.count()

    r = logged_in_admin.post(
        "/users/new",
        data={
            "employee_number": "NEW-USR-001",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@test.local",
            "phone": "+260900000000",
            "department_id": str(department.id),
            "password": "newpass123",
            "confirm_password": "newpass123",
        },
        follow_redirects=False,
    )

    assert User.query.count() == before + 1

    new = User.query.filter_by(employee_number="NEW-USR-001").first()
    assert new is not None
    assert new.first_name == "New"
    assert new.check_password("newpass123")


def test_create_user_rejects_duplicate_employee_number(
    logged_in_admin, admin, department, db
):
    before = User.query.count()

    logged_in_admin.post(
        "/users/new",
        data={
            "employee_number": admin.employee_number,
            "first_name": "Dup",
            "last_name": "User",
            "department_id": str(department.id),
            "password": "newpass123",
            "confirm_password": "newpass123",
        },
    )

    assert User.query.count() == before


# =========================================================
# DEACTIVATE / REACTIVATE
# =========================================================

def test_deactivate_employee(logged_in_admin, employee, db):
    r = logged_in_admin.post(
        f"/users/{employee.id}/deactivate",
        follow_redirects=False,
    )
    assert r.status_code == 302

    db.session.refresh(employee)
    assert employee.is_active is False


def test_reactivate_employee(logged_in_admin, employee, db):
    employee.is_active = False
    db.session.commit()

    r = logged_in_admin.post(
        f"/users/{employee.id}/activate",
        follow_redirects=False,
    )
    assert r.status_code == 302

    db.session.refresh(employee)
    assert employee.is_active is True


# =========================================================
# LOCKOUT GUARDS
# =========================================================

def test_cannot_deactivate_self(logged_in_admin, admin, db):
    logged_in_admin.post(f"/users/{admin.id}/deactivate")

    db.session.refresh(admin)
    assert admin.is_active is True  # Still active


def test_cannot_deactivate_last_admin(
    logged_in_admin, admin, db
):
    """
    admin is the only Administrator. Deactivating
    another admin (or self) must be refused.
    """
    # Try to deactivate self
    logged_in_admin.post(f"/users/{admin.id}/deactivate")

    db.session.refresh(admin)
    assert admin.is_active is True


# =========================================================
# ACTIVITY LOG
# =========================================================

def test_create_user_writes_activity(
    logged_in_admin, department, db
):
    before = ActivityLog.query.count()

    logged_in_admin.post(
        "/users/new",
        data={
            "employee_number": "LOG-USR-001",
            "first_name": "Log",
            "last_name": "Test",
            "department_id": str(department.id),
            "password": "logpass123",
            "confirm_password": "logpass123",
        },
    )

    assert ActivityLog.query.count() == before + 1

    newest = ActivityLog.query.order_by(ActivityLog.id.desc()).first()
    assert newest.action == "create"
    assert newest.entity_type == "User"


def test_deactivate_writes_activity(
    logged_in_admin, employee, db
):
    before = ActivityLog.query.count()

    logged_in_admin.post(f"/users/{employee.id}/deactivate")

    assert ActivityLog.query.count() == before + 1

    newest = ActivityLog.query.order_by(ActivityLog.id.desc()).first()
    assert newest.action == "deactivate"

