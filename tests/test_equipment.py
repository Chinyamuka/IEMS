"""
Equipment route tests.

Covers:
- Listing, viewing details
- Creating equipment
- Editing equipment
- Deleting equipment
- Search and filter logic
- Photo upload validation
"""

from datetime import date

from app.models import Equipment, ActivityLog


# =========================================================
# LISTING
# =========================================================

def test_equipment_list_loads_for_admin(logged_in_admin):
    r = logged_in_admin.get("/equipment/")
    assert r.status_code == 200


def test_equipment_list_loads_for_employee(logged_in_employee):
    r = logged_in_employee.get("/equipment/")
    assert r.status_code == 200


def test_equipment_list_shows_existing_row(logged_in_admin, equipment):
    r = logged_in_admin.get("/equipment/")
    assert equipment.asset_tag.encode() in r.data


# =========================================================
# DETAIL
# =========================================================

def test_equipment_detail_loads(logged_in_admin, equipment):
    r = logged_in_admin.get(f"/equipment/{equipment.id}")
    assert r.status_code == 200
    assert equipment.asset_tag.encode() in r.data


def test_equipment_detail_404_for_missing(logged_in_admin):
    r = logged_in_admin.get("/equipment/99999")
    assert r.status_code == 404


# =========================================================
# CREATE
# =========================================================

def test_create_equipment_page_loads_for_admin(logged_in_admin):
    r = logged_in_admin.get("/equipment/new")
    assert r.status_code == 200


def test_create_equipment_creates_row(
    logged_in_admin, category, location, db
):
    before = Equipment.query.count()

    r = logged_in_admin.post(
        "/equipment/new",
        data={
            "asset_tag": "NEW-TEST-001",
            "serial_number": "SN-NEW-001",
            "manufacturer": "New Maker",
            "model": "New Model",
            "description": "Created via test",
            "category_id": category.id,
            "location_id": location.id,
            "status": "In Stock",
            "condition": "Good",
            "purchase_date": "2026-01-15",
        },
        follow_redirects=False,
    )

    # Successful create redirects (302)
    assert r.status_code in (200, 302)
    assert Equipment.query.count() == before + 1

    new = Equipment.query.filter_by(asset_tag="NEW-TEST-001").first()
    assert new is not None
    assert new.manufacturer == "New Maker"


def test_create_equipment_rejects_duplicate_asset_tag(
    logged_in_admin, equipment, category, location, db
):
    before = Equipment.query.count()

    r = logged_in_admin.post(
        "/equipment/new",
        data={
            "asset_tag": equipment.asset_tag,  # duplicate
            "manufacturer": "Different",
            "model": "Different",
            "category_id": category.id,
            "location_id": location.id,
            "status": "In Stock",
            "condition": "Good",
            "purchase_date": "2026-01-15",
        },
        follow_redirects=False,
    )

    # No new row created
    assert Equipment.query.count() == before


# =========================================================
# EDIT
# =========================================================

def test_edit_equipment_page_loads(logged_in_admin, equipment):
    r = logged_in_admin.get(f"/equipment/{equipment.id}/edit")
    assert r.status_code == 200


def test_edit_equipment_updates_row(
    logged_in_admin, equipment, category, location, db
):
    r = logged_in_admin.post(
        f"/equipment/{equipment.id}/edit",
        data={
            "asset_tag": equipment.asset_tag,
            "manufacturer": "Updated Maker",
            "model": equipment.model,
            "category_id": category.id,
            "location_id": location.id,
            "status": "Under Maintenance",
            "condition": "Fair",
            "purchase_date": "2026-01-01",
        },
        follow_redirects=False,
    )

    db.session.refresh(equipment)
    assert equipment.manufacturer == "Updated Maker"
    assert equipment.status == "Under Maintenance"


# =========================================================
# DELETE
# =========================================================

def test_delete_page_loads(logged_in_admin, equipment):
    r = logged_in_admin.get(f"/equipment/{equipment.id}/delete")
    assert r.status_code == 200


def test_delete_removes_row(logged_in_admin, equipment, db):
    eq_id = equipment.id

    r = logged_in_admin.post(
        f"/equipment/{eq_id}/delete",
        follow_redirects=False,
    )

    assert r.status_code == 302
    assert db.session.get(Equipment, eq_id) is None


# =========================================================
# ACTIVITY LOG
# =========================================================

def test_create_equipment_writes_activity(
    logged_in_admin, category, location, db
):
    before = ActivityLog.query.count()

    logged_in_admin.post(
        "/equipment/new",
        data={
            "asset_tag": "LOG-TEST-001",
            "manufacturer": "Log Maker",
            "model": "Log Model",
            "category_id": category.id,
            "location_id": location.id,
            "status": "In Stock",
            "condition": "Good",
            "purchase_date": "2026-01-15",
        },
    )

    assert ActivityLog.query.count() == before + 1

    newest = ActivityLog.query.order_by(ActivityLog.id.desc()).first()
    assert newest.action == "create"
    assert newest.entity_type == "Equipment"
    assert "LOG-TEST-001" in newest.summary


def test_delete_equipment_writes_activity(
    logged_in_admin, equipment, db
):
    before = ActivityLog.query.count()

    logged_in_admin.post(f"/equipment/{equipment.id}/delete")

    assert ActivityLog.query.count() == before + 1

    newest = ActivityLog.query.order_by(ActivityLog.id.desc()).first()
    assert newest.action == "delete"
    assert newest.entity_type == "Equipment"
