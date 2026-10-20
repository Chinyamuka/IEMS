"""
Pytest fixtures for the IEMS test suite.

Key behaviours:

- Each test gets a fresh Flask app instance.
- The database is in-memory SQLite, not PostgreSQL. Every
  test starts with an empty schema, created and dropped
  around it. This is fast and isolated.

- CSRF is disabled during tests. WTForms/Flask-WTF
  otherwise rejects POST requests without a token, which
  would make every form test fail.

- Mail is enabled with MAIL_SUPPRESS_SEND cleared, so
  flask_mail.record_messages() captures sends instead of
  service.send() short-circuiting. No real SMTP is
  touched — record_messages() intercepts at the
  mail.send() boundary.

- load_current_user and the forced-password-change guard
  in app/__init__.py still run. Tests exercise the real
  request lifecycle.
"""

import os
import tempfile

import pytest

from app import create_app
from app.extensions import db as _db
from app.models import User, Department
from tests.test_config import TestConfig


# =========================================================
# APP + DB
# =========================================================

@pytest.fixture
def app():
    """
    A fresh Flask app per test, pointed at an in-memory
    SQLite database.

    TestConfig is passed to create_app so SQLAlchemy
    binds the engine to sqlite:///:memory: BEFORE
    db.init_app runs. Mutating app.config afterwards
    would be a no-op for the DATABASE engine — the engine
    would already be bound to whatever Config specified.

    MAIL_* config is different: it is read at
    send-time by service.send(), so it can be flipped
    after create_app() returns. We enable mail here so
    tests that exercise the send path reach
    flask_mail.record_messages() instead of being
    short-circuited by MAIL_SUPPRESS_SEND.
    """

    app = create_app(config_class=TestConfig)

    # TestConfig inherits Config, so MAIL_ENABLED comes
    # from .env like production. Local .env typically has
    # MAIL_ENABLED=false, which sets MAIL_SUPPRESS_SEND=True
    # in Config. Tests that exercise the send path need
    # that off; record_messages() intercepts at
    # mail.send() so no real SMTP is contacted.
    app.config["MAIL_SUPPRESS_SEND"] = False

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client bound to the app fixture."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Shortcut to the SQLAlchemy session inside the app."""
    return _db


# =========================================================
# USER FIXTURES
# =========================================================

@pytest.fixture
def department(app):
    """A Department row for tests that need one."""
    dept = Department(name="Test Department")
    _db.session.add(dept)
    _db.session.commit()
    return dept


@pytest.fixture
def admin(app, department):
    """
    An active Administrator user.
    Password is 'admin1234'.
    """
    user = User(
        employee_number="ADM-TEST-001",
        first_name="Test",
        last_name="Admin",
        email="admin@test.local",
        role="Administrator",
        department_id=department.id,
        is_active=True,
    )
    user.set_password("admin1234")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def employee(app, department):
    """
    An active Employee user.
    Password is 'emp12345'.
    """
    user = User(
        employee_number="EMP-TEST-001",
        first_name="Test",
        last_name="Employee",
        email="employee@test.local",
        role="Employee",
        department_id=department.id,
        is_active=True,
    )
    user.set_password("emp12345")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def inactive_user(app, department):
    """
    An inactive Employee. Used to test login rejection.
    """
    user = User(
        employee_number="EMP-TEST-002",
        first_name="Inactive",
        last_name="Employee",
        email="inactive@test.local",
        role="Employee",
        department_id=department.id,
        is_active=False,
    )
    user.set_password("inactive1234")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def officer(app, department):
    """
    An IT Officer user (equipment management role).
    Password is 'officer1234'.
    """
    user = User(
        employee_number="OFF-TEST-001",
        first_name="Test",
        last_name="Officer",
        email="officer@test.local",
        role="IT Officer",
        department_id=department.id,
        is_active=True,
    )
    user.set_password("officer1234")
    _db.session.add(user)
    _db.session.commit()
    return user


# =========================================================
# LOGGED-IN CLIENT FIXTURES
# =========================================================

def _login(client, employee_number, password):
    """POST to /auth/login and return the response."""
    return client.post(
        "/auth/login",
        data={
            "employee_number": employee_number,
            "password": password,
        },
        follow_redirects=False,
    )


@pytest.fixture
def logged_in_admin(client, admin):
    """Client already authenticated as the admin fixture."""
    _login(client, "ADM-TEST-001", "admin1234")
    return client


@pytest.fixture
def logged_in_employee(client, employee):
    """Client already authenticated as the employee fixture."""
    _login(client, "EMP-TEST-001", "emp12345")
    return client


@pytest.fixture
def logged_in_officer(client, officer):
    """Client authenticated as the officer fixture."""
    _login(client, "OFF-TEST-001", "officer1234")
    return client


# =========================================================
# ADDITIONAL FIXTURES FOR EXPANDED TESTS
# =========================================================

@pytest.fixture
def category(app):
    """An equipment Category for equipment tests."""
    from app.models import Category

    cat = Category(
        name="Laptops",
        description="Portable computers",
    )
    _db.session.add(cat)
    _db.session.commit()
    return cat


@pytest.fixture
def location(app):
    """A Location for equipment tests."""
    from app.models import Location

    loc = Location(
        name="Main Office",
        building="Building A",
        room="101",
    )
    _db.session.add(loc)
    _db.session.commit()
    return loc


@pytest.fixture
def equipment(app, category, location):
    """An Equipment row for tests that need one."""
    from datetime import date
    from app.models import Equipment

    eq = Equipment(
        asset_tag="EQ-TEST-001",
        serial_number="SN-TEST-001",
        manufacturer="Test Manufacturer",
        model="Test Model",
        description="Test equipment",
        category_id=category.id,
        location_id=location.id,
        status="In Stock",
        condition="Good",
        purchase_date=date(2026, 1, 1),
    )
    _db.session.add(eq)
    _db.session.commit()
    return eq
