"""
Tests for the global search route.
"""


def test_search_with_empty_query_renders(client, logged_in_admin):
    response = logged_in_admin.get("/search/?q=")
    assert response.status_code == 200
    assert b"Search results" in response.data


def test_search_finds_equipment_by_asset_tag(
    client, logged_in_admin, equipment
):
    response = logged_in_admin.get(f"/search/?q={equipment.asset_tag}")
    assert response.status_code == 200
    assert equipment.asset_tag.encode() in response.data


def test_search_finds_user_by_employee_number(
    client, logged_in_admin, employee
):
    response = logged_in_admin.get(f"/search/?q={employee.employee_number}")
    assert response.status_code == 200
    assert employee.employee_number.encode() in response.data


def test_search_with_no_matches_shows_empty_state(
    client, logged_in_admin
):
    response = logged_in_admin.get("/search/?q=XYZ-NO-MATCH-9999")
    assert response.status_code == 200
    assert b"No matches" in response.data


def test_search_requires_login(client):
    response = client.get("/search/?q=test", follow_redirects=False)
    assert response.status_code in (301, 302)