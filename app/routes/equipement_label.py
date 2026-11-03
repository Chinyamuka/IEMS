"""
IEMS Equipment Label Routes

Two routes:
    GET /equipment/<id>/label     single-item printable label
    GET /equipment/labels         grid of all equipment labels

Both send a print-friendly HTML page. The QR image itself
is served by a sub-route that streams PNG bytes directly.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    url_for,
    abort,
)
from io import BytesIO

from app.extensions import db
from app.models import Equipment
from app.auth.decorators import login_required
from app.utils.qr import generate_qr_png


equipment_label_bp = Blueprint(
    "equipment_label",
    __name__,
    url_prefix="/equipment",
)


# =========================================================
# SINGLE LABEL PAGE
# =========================================================

@equipment_label_bp.route("/<int:equipment_id>/label")
@login_required
def single(equipment_id):
    """Printable label for one equipment item."""

    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        abort(404)

    equipment_url = url_for(
        "equipment.detail",
        equipment_id=equipment.id,
        _external=True,
    )

    return render_template(
        "equipment/label_single.html",
        equipment=equipment,
        equipment_url=equipment_url,
    )


# =========================================================
# ALL LABELS PAGE
# =========================================================

@equipment_label_bp.route("/labels")
@login_required
def all_labels():
    """
    Grid of labels for every equipment record.

    Accepts the same filter params as the list page so an
    operator can print labels for just "In Stock" items,
    or just "Laptops", without printing the whole inventory.
    """

    category_id = request.args.get("category", type=int)
    status = request.args.get("status", "").strip()
    location_id = request.args.get("location", type=int)
    search = request.args.get("q", "").strip()

    query = Equipment.query

    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Equipment.asset_tag.ilike(term),
                Equipment.serial_number.ilike(term),
                Equipment.manufacturer.ilike(term),
                Equipment.model.ilike(term),
            )
        )
    if category_id:
        query = query.filter(Equipment.category_id == category_id)
    if status:
        query = query.filter(Equipment.status == status)
    if location_id:
        query = query.filter(Equipment.location_id == location_id)

    items = query.order_by(Equipment.asset_tag.asc()).all()

    # Pre-build the (equipment, url) pairs so the template
    # doesn't call url_for() inside a loop.
    labels = [
        {
            "equipment": eq,
            "url": url_for(
                "equipment.detail",
                equipment_id=eq.id,
                _external=True,
            ),
        }
        for eq in items
    ]

    return render_template(
        "equipment/labels_all.html",
        labels=labels,
    )


# =========================================================
# QR IMAGE STREAM
# =========================================================

@equipment_label_bp.route("/<int:equipment_id>/label.png")
@login_required
def single_png(equipment_id):
    """
    Return the QR PNG for one equipment item, in-memory.

    This is what the <img src> on the label pages points at.
    """

    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        abort(404)

    equipment_url = url_for(
        "equipment.detail",
        equipment_id=equipment.id,
        _external=True,
    )

    png_bytes = generate_qr_png(equipment_url)

    return send_file(
        BytesIO(png_bytes),
        mimetype="image/png",
        as_attachment=False,
    )