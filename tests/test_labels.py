"""Tests for equipment QR label routes."""


def test_single_label_renders(client, logged_in_admin, equipment):
    response = logged_in_admin.get(f"/equipment/{equipment.id}/label")
    assert response.status_code == 200
    assert equipment.asset_tag.encode() in response.data
    assert b"Print this label" in response.data


def test_single_label_404_for_missing(client, logged_in_admin):
    response = logged_in_admin.get("/equipment/99999/label")
    assert response.status_code == 404


def test_single_png_returns_image(client, logged_in_admin, equipment):
    response = logged_in_admin.get(f"/equipment/{equipment.id}/label.png")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data[:8] == b"\x89PNG\r\n\x1a\n"


def test_single_png_404_for_missing(client, logged_in_admin):
    response = logged_in_admin.get("/equipment/99999/label.png")
    assert response.status_code == 404


def test_all_labels_renders(client, logged_in_admin, equipment):
    response = logged_in_admin.get("/equipment/labels")
    assert response.status_code == 200
    assert equipment.asset_tag.encode() in response.data
    assert b"Print all labels" in response.data


def test_labels_require_login(client, equipment):
    single = client.get(
        f"/equipment/{equipment.id}/label",
        follow_redirects=False,
    )
    all_resp = client.get(
        "/equipment/labels",
        follow_redirects=False,
    )
    assert single.status_code in (301, 302)
    assert all_resp.status_code in (301, 302)
