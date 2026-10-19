"""
Lookup table route tests.

Covers CRUD for Departments, Locations, Categories,
and the reference guards that prevent deleting a row
still referenced by other records.
"""

from app.models import (
    Department,
    Location,
    Category,
    User,
    Equipment,
    ActivityLog,
)


# =========================================================
# DEPARTMENTS
# =========================================================

def test_departments_list_loads(logged_in_admin):
    r = logged_in_admin.get("/departments/")
    assert r.status_code == 200


def test_create_department(logged_in_admin, db):
    before = Department.query.count()

    logged_in_admin.post(
        "/departments/new",
        data={
            "name": "Test Dept",
            "description": "A department for tests",
        },
    )

    assert Department.query.count() == before + 1

    dept = Department.query.filter_by(name="Test Dept").first()
    assert dept is not None


def test_cannot_delete_department_with_users(
    logged_in_admin, department, employee, db
):
    """
    department has employee attached. Delete must be refused.
    """
    dept_id = department.id

    logged_in_admin.post(f"/departments/{dept_id}/delete")

    assert db.session.get(Department, dept_id) is not None


def test_can_delete_empty_department(logged_in_admin, db):
    dept = Department(name="Empty Dept")
    db.session.add(dept)
    db.session.commit()

    dept_id = dept.id

    logged_in_admin.post(f"/departments/{dept_id}/delete")

    assert db.session.get(Department, dept_id) is None


# =========================================================
# LOCATIONS
# =========================================================

def test_locations_list_loads(logged_in_admin):
    r = logged_in_admin.get("/locations/")
    assert r.status_code == 200


def test_create_location(logged_in_admin, db):
    before = Location.query.count()

    logged_in_admin.post(
        "/locations/new",
        data={
            "name": "Test Location",
            "building": "Test Building",
            "room": "T1",
        },
    )

    assert Location.query.count() == before + 1


def test_cannot_delete_location_with_equipment(
    logged_in_admin, location, equipment, db
):
    loc_id = location.id

    logged_in_admin.post(f"/locations/{loc_id}/delete")

    assert db.session.get(Location, loc_id) is not None


# =========================================================
# CATEGORIES
# =========================================================

def test_categories_list_loads(logged_in_admin):
    r = logged_in_admin.get("/categories/")
    assert r.status_code == 200


def test_create_category(logged_in_admin, db):
    before = Category.query.count()

    logged_in_admin.post(
        "/categories/new",
        data={
            "name": "Test Category",
            "description": "For testing",
        },
    )

    assert Category.query.count() == before + 1


def test_cannot_delete_category_with_equipment(
    logged_in_admin, category, equipment, db
):
    cat_id = category.id

    logged_in_admin.post(f"/categories/{cat_id}/delete")

    assert db.session.get(Category, cat_id) is not None


# =========================================================
# ACTIVITY LOG
# =========================================================

def test_create_department_writes_activity(
    logged_in_admin, db
):
    before = ActivityLog.query.count()

    logged_in_admin.post(
        "/departments/new",
        data={"name": "Activity Dept"},
    )

    assert ActivityLog.query.count() == before + 1

    newest = ActivityLog.query.order_by(ActivityLog.id.desc()).first()
    assert newest.action == "create"
    assert newest.entity_type == "Department"
