"""
Role-based access control tests.

Confirm that:
- Anonymous users are redirected to login.
- Employees cannot reach administrator pages.
- Administrators can reach administrator pages.
- Forced password change redirects correctly.
"""


# =========================================================
# ADMIN-ONLY PAGES: ALLOW
# =========================================================

def test_admin_can_reach_users_list(logged_in_admin):
    r = logged_in_admin.get("/users/")
    assert r.status_code == 200


def test_admin_can_reach_departments(logged_in_admin):
    r = logged_in_admin.get("/departments/")
    assert r.status_code == 200


def test_admin_can_reach_locations(logged_in_admin):
    r = logged_in_admin.get("/locations/")
    assert r.status_code == 200


def test_admin_can_reach_categories(logged_in_admin):
    r = logged_in_admin.get("/categories/")
    assert r.status_code == 200


def test_admin_can_reach_activity_log(logged_in_admin):
    r = logged_in_admin.get("/activity/")
    assert r.status_code == 200


def test_admin_can_reach_equipment_create(logged_in_admin):
    r = logged_in_admin.get("/equipment/new")
    assert r.status_code == 200


# =========================================================
# ADMIN-ONLY PAGES: DENY EMPLOYEE
# =========================================================

def test_employee_blocked_from_users(logged_in_employee):
    r = logged_in_employee.get("/users/", follow_redirects=False)
    # RBAC blocks with a 302 to /dashboard/
    assert r.status_code == 302
    assert "/dashboard" in r.headers.get("Location", "")


def test_employee_blocked_from_departments(logged_in_employee):
    r = logged_in_employee.get("/departments/", follow_redirects=False)
    assert r.status_code == 302


def test_employee_blocked_from_locations(logged_in_employee):
    r = logged_in_employee.get("/locations/", follow_redirects=False)
    assert r.status_code == 302


def test_employee_blocked_from_categories(logged_in_employee):
    r = logged_in_employee.get("/categories/", follow_redirects=False)
    assert r.status_code == 302


def test_employee_blocked_from_activity(logged_in_employee):
    r = logged_in_employee.get("/activity/", follow_redirects=False)
    assert r.status_code == 302


def test_employee_blocked_from_equipment_create(logged_in_employee):
    r = logged_in_employee.get("/equipment/new", follow_redirects=False)
    assert r.status_code == 302


# =========================================================
# EMPLOYEE-ALLOWED PAGES
# =========================================================

def test_employee_can_reach_dashboard(logged_in_employee):
    r = logged_in_employee.get("/dashboard/")
    assert r.status_code == 200


def test_employee_can_reach_equipment_list(logged_in_employee):
    r = logged_in_employee.get("/equipment/")
    assert r.status_code == 200


def test_employee_can_reach_own_profile(logged_in_employee):
    r = logged_in_employee.get("/profile/")
    assert r.status_code == 200


# =========================================================
# FORCED PASSWORD CHANGE
# =========================================================

def test_flagged_user_redirected_from_dashboard(
    client, employee, db
):
    """
    A user with must_change_password=True is redirected
    from any non-allowlisted page to /profile/change-password.
    """
    employee.must_change_password = True
    db.session.commit()

    # Log in
    client.post(
        "/auth/login",
        data={
            "employee_number": "EMP-TEST-001",
            "password": "emp12345",
        },
    )

    r = client.get("/dashboard/", follow_redirects=False)
    assert r.status_code == 302
    assert "/profile/change-password" in r.headers.get("Location", "")


def test_flagged_user_can_reach_change_password(
    client, employee, db
):
    """The allowlisted page itself loads."""
    employee.must_change_password = True
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "employee_number": "EMP-TEST-001",
            "password": "emp12345",
        },
    )

    r = client.get("/profile/change-password")
    assert r.status_code == 200


def test_flagged_user_can_logout(client, employee, db):
    """The escape hatch — logout still works."""
    employee.must_change_password = True
    db.session.commit()

    client.post(
        "/auth/login",
        data={
            "employee_number": "EMP-TEST-001",
            "password": "emp12345",
        },
    )

    r = client.post("/auth/logout", follow_redirects=False)
    assert r.status_code == 302
