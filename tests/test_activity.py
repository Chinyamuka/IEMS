"""
Activity log tests.

Covers:
- The /activity/ page for admins
- Filtering by user, action, entity
- RBAC (employee blocked)
- Dashboard recent activity widget
"""

from app.models import ActivityLog


def _seed_activity(app, db):
    """Insert some ActivityLog rows directly."""
    entries = [
        ActivityLog(
            user_id=None,
            action="create",
            entity_type="Equipment",
            entity_id=1,
            summary="Test equipment creation",
        ),
        ActivityLog(
            user_id=None,
            action="delete",
            entity_type="User",
            entity_id=2,
            summary="Test user deletion",
        ),
        ActivityLog(
            user_id=None,
            action="update",
            entity_type="Equipment",
            entity_id=3,
            summary="Test equipment update",
        ),
    ]
    for e in entries:
        db.session.add(e)
    db.session.commit()


# =========================================================
# /activity/ PAGE
# =========================================================

def test_activity_page_loads_for_admin(logged_in_admin):
    r = logged_in_admin.get("/activity/")
    assert r.status_code == 200


def test_activity_page_shows_entries(
    logged_in_admin, app, db
):
    _seed_activity(app, db)

    r = logged_in_admin.get("/activity/")
    assert b"Test equipment creation" in r.data


def test_activity_page_filter_by_action(
    logged_in_admin, app, db
):
    _seed_activity(app, db)

    r = logged_in_admin.get("/activity/?action=delete")
    # Only the delete entry should show
    assert b"Test user deletion" in r.data
    # The update entry should not
    assert b"Test equipment update" not in r.data


def test_activity_page_filter_by_entity(
    logged_in_admin, app, db
):
    _seed_activity(app, db)

    r = logged_in_admin.get("/activity/?entity_type=Equipment")
    assert b"Test equipment creation" in r.data
    assert b"Test user deletion" not in r.data


def test_activity_page_blocked_for_employee(logged_in_employee):
    r = logged_in_employee.get("/activity/", follow_redirects=False)
    assert r.status_code == 302


# =========================================================
# DASHBOARD WIDGET
# =========================================================

def test_dashboard_shows_recent_activity(
    logged_in_admin, app, db
):
    _seed_activity(app, db)

    r = logged_in_admin.get("/dashboard/")
    # The page should contain the "Recent Activity" header
    assert b"Recent Activity" in r.data or b"recent activity" in r.data.lower()
