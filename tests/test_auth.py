"""
Authentication tests.

Covers the login and logout flow, and the credential
validations that block bad logins.
"""


# =========================================================
# LOGIN FORM
# =========================================================

def test_login_page_loads(client):
    """The login form is reachable without authentication."""
    r = client.get("/auth/login")
    assert r.status_code == 200
    assert b"Sign in" in r.data or b"Employee number" in r.data


# =========================================================
# LOGIN SUCCESS
# =========================================================

def test_login_succeeds_with_valid_credentials(client, admin):
    """A valid login redirects to the dashboard."""
    r = client.post(
        "/auth/login",
        data={
            "employee_number": "ADM-TEST-001",
            "password": "admin1234",
        },
        follow_redirects=False,
    )
    # Successful login issues a 302 to /dashboard/
    assert r.status_code == 302
    assert "/dashboard" in r.headers.get("Location", "")


def test_login_creates_session(client, admin):
    """After login, /dashboard/ is reachable."""
    client.post(
        "/auth/login",
        data={
            "employee_number": "ADM-TEST-001",
            "password": "admin1234",
        },
    )
    r = client.get("/dashboard/")
    assert r.status_code == 200


# =========================================================
# LOGIN FAILURE
# =========================================================

def test_login_fails_with_wrong_password(client, admin):
    r = client.post(
        "/auth/login",
        data={
            "employee_number": "ADM-TEST-001",
            "password": "wrong-password",
        },
        follow_redirects=False,
    )
    # Login form re-renders with 200 on bad credentials
    assert r.status_code == 200


def test_login_fails_with_unknown_user(client):
    r = client.post(
        "/auth/login",
        data={
            "employee_number": "NOT-A-REAL-ID",
            "password": "anything",
        },
        follow_redirects=False,
    )
    assert r.status_code == 200


def test_login_fails_for_inactive_user(client, inactive_user):
    r = client.post(
        "/auth/login",
        data={
            "employee_number": "EMP-TEST-002",
            "password": "inactive1234",
        },
        follow_redirects=False,
    )
    assert r.status_code == 200


def test_login_fails_with_empty_fields(client):
    r = client.post(
        "/auth/login",
        data={"employee_number": "", "password": ""},
        follow_redirects=False,
    )
    assert r.status_code == 200


# =========================================================
# LOGOUT
# =========================================================

def test_logout_clears_session(logged_in_admin):
    r = logged_in_admin.post(
        "/auth/logout",
        follow_redirects=False,
    )
    assert r.status_code == 302
    # After logout, /dashboard/ should redirect to login
    r2 = logged_in_admin.get("/dashboard/", follow_redirects=False)
    assert r2.status_code == 302
    assert "/auth/login" in r2.headers.get("Location", "")


# =========================================================
# ANONYMOUS ACCESS
# =========================================================

def test_dashboard_redirects_anonymous(client):
    r = client.get("/dashboard/", follow_redirects=False)
    assert r.status_code == 302
    assert "/auth/login" in r.headers.get("Location", "")


def test_equipment_list_redirects_anonymous(client):
    r = client.get("/equipment/", follow_redirects=False)
    assert r.status_code == 302
    assert "/auth/login" in r.headers.get("Location", "")
