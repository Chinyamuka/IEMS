"""
Tests for bulk actions on equipment and users.
"""


def test_bulk_retire_equipment(
    client, logged_in_admin, equipment
):
    eq_id = equipment.id
    response = logged_in_admin.post(
        "/equipment/bulk/",
        data={
            "action": "retire",
            "ids[]": [str(eq_id)],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    from app.models import Equipment
    refreshed = Equipment.query.get(eq_id)
    assert refreshed is not None
    assert refreshed.status == "Retired"


def test_bulk_delete_equipment(
    client, logged_in_admin, equipment
):
    eq_id = equipment.id
    response = logged_in_admin.post(
        "/equipment/bulk/",
        data={
            "action": "delete",
            "ids[]": [str(eq_id)],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    from app.models import Equipment
    assert Equipment.query.get(eq_id) is None


def test_bulk_requires_selection(
    client, logged_in_admin
):
    response = logged_in_admin.post(
        "/equipment/bulk/",
        data={"action": "retire"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"No items were selected" in response.data


def test_bulk_deactivate_users(
    client, logged_in_admin, employee
):
    user_id = employee.id
    response = logged_in_admin.post(
        "/users/bulk/",
        data={
            "action": "deactivate",
            "ids[]": [str(user_id)],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    from app.models import User
    refreshed = User.query.get(user_id)
    assert refreshed is not None
    assert refreshed.is_active is False


def test_bulk_activate_users(
    client, logged_in_admin, inactive_user
):
    user_id = inactive_user.id
    response = logged_in_admin.post(
        "/users/bulk/",
        data={
            "action": "activate",
            "ids[]": [str(user_id)],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    from app.models import User
    refreshed = User.query.get(user_id)
    assert refreshed is not None
    assert refreshed.is_active is True


def test_bulk_users_requires_admin(
    client, logged_in_employee, employee
):
    response = logged_in_employee.post(
        "/users/bulk/",
        data={
            "action": "deactivate",
            "ids[]": [str(employee.id)],
        },
        follow_redirects=False,
    )
    assert response.status_code in (301, 302)