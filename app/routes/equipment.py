"""
IEMS Equipment Routes

Contains routes responsible for creating and viewing
ICT equipment records. Every mutation is recorded in
the activity log and invalidates the dashboard cache.
"""

from app.utils.cache import (
    cache_delete,
    get_cached_departments,      # unused here, but keep imports tidy
    get_cached_locations,
    get_cached_categories,
)


from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    url_for,
    request,
)


from app.extensions import db
from app.forms.equipment_form import EquipmentForm
from app.models.category import Category
from app.models.location import Location
from app.models.equipment import Equipment
from app.auth.decorators import login_required
from app.utils.permissions import role_required
from app.utils.uploads import (
    save_image,
    delete_image,
    ImageUploadError,
)
from app.utils.activity import log_activity
from app.utils.cache import cache_delete
from app.routes.dashboard import CACHE_KEY_DASHBOARD_STATS


# =========================================================
# BLUEPRINT
# =========================================================

equipment_bp = Blueprint(
    "equipment",
    __name__,
    url_prefix="/equipment",
)


# =========================================================
# CREATE
# =========================================================

@equipment_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(
    "Administrator",
    "Asset Officer",
    "IT Manager",
    "IT Officer",
)
def create():
    """Register a new piece of ICT equipment."""

    form = EquipmentForm()

    categories = get_cached_categories()
    form.category_id.choices = [
        (c["id"], c["name"]) for c in categories
    ]

    locations = get_cached_locations()
    form.location_id.choices = [
        (l["id"], l["name"]) for l in locations
    ]

    if form.validate_on_submit():

        existing_equipment = Equipment.query.filter_by(
            asset_tag=form.asset_tag.data
        ).first()

        if existing_equipment:
            flash(
                "An equipment record with this asset tag already exists.",
                "error",
            )
            return render_template(
                "equipment/create.html",
                form=form,
            )

        new_image_filename = None

        try:
            new_image_filename = save_image(
                form.image.data,
                "equipment",
            )
        except ImageUploadError as error:
            flash(str(error), "danger")
            return render_template(
                "equipment/create.html",
                form=form,
            )

        equipment = Equipment(
            asset_tag=form.asset_tag.data,
            serial_number=form.serial_number.data,
            manufacturer=form.manufacturer.data,
            model=form.model.data,
            description=form.description.data,
            image_filename=new_image_filename,
            category_id=form.category_id.data,
            location_id=form.location_id.data,
            status=form.status.data,
            condition=form.condition.data,
            purchase_date=form.purchase_date.data,
            purchase_price=form.purchase_price.data,
            warranty_expiry=form.warranty_expiry.data,
        )

        db.session.add(equipment)
        db.session.flush()

        log_activity(
            "create",
            "Equipment",
            equipment.id,
            f"Registered equipment {equipment.asset_tag}",
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            if new_image_filename is not None:
                delete_image(new_image_filename, "equipment")
            flash(
                "Equipment could not be saved. Please try again.",
                "danger",
            )
            return render_template(
                "equipment/create.html",
                form=form,
            )

        cache_delete(CACHE_KEY_DASHBOARD_STATS)

        flash(
            "Equipment registered successfully.",
            "success",
        )
        return redirect(url_for("equipment.index"))

    return render_template(
        "equipment/create.html",
        form=form,
    )


# =========================================================
# DETAIL
# =========================================================

@equipment_bp.route("/<int:equipment_id>")
@login_required
def detail(equipment_id):
    """Display a single equipment record."""
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template(
        "equipment/detail.html",
        equipment=equipment,
    )


# =========================================================
# EDIT
# =========================================================

@equipment_bp.route("/<int:equipment_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(
    "Administrator",
    "Asset Officer",
    "IT Manager",
    "IT Officer",
)
def edit(equipment_id):
    """Edit an existing equipment record."""

    equipment = Equipment.query.get_or_404(equipment_id)
    form = EquipmentForm(obj=equipment)

    categories = Category.query.order_by(Category.name).all()
    form.category_id.choices = [
        (c.id, c.name) for c in categories
    ]

    locations = Location.query.order_by(Location.name).all()
    form.location_id.choices = [
        (l.id, l.name) for l in locations
    ]

    if form.validate_on_submit():

        existing_equipment = Equipment.query.filter(
            Equipment.asset_tag == form.asset_tag.data,
            Equipment.id != equipment.id,
        ).first()

        if existing_equipment:
            flash(
                f"Asset tag '{form.asset_tag.data}' "
                "already belongs to another equipment record.",
                "error",
            )
            return render_template(
                "equipment/edit.html",
                form=form,
                equipment=equipment,
            )

        new_image_filename = None
        old_image_filename = equipment.image_filename

        try:
            new_image_filename = save_image(
                form.image.data,
                "equipment",
            )
        except ImageUploadError as error:
            flash(str(error), "danger")
            return render_template(
                "equipment/edit.html",
                form=form,
                equipment=equipment,
            )

        equipment.asset_tag = form.asset_tag.data
        equipment.serial_number = form.serial_number.data
        equipment.manufacturer = form.manufacturer.data
        equipment.model = form.model.data
        equipment.description = form.description.data
        equipment.category_id = form.category_id.data
        equipment.location_id = form.location_id.data
        equipment.status = form.status.data
        equipment.condition = form.condition.data
        equipment.purchase_date = form.purchase_date.data
        equipment.purchase_price = form.purchase_price.data
        equipment.warranty_expiry = form.warranty_expiry.data

        if new_image_filename is not None:
            equipment.image_filename = new_image_filename

        log_activity(
            "update",
            "Equipment",
            equipment.id,
            f"Updated equipment {equipment.asset_tag}",
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            if new_image_filename is not None:
                delete_image(new_image_filename, "equipment")
            flash(
                "Changes could not be saved. Please try again.",
                "danger",
            )
            return render_template(
                "equipment/edit.html",
                form=form,
                equipment=equipment,
            )

        if (
            new_image_filename is not None
            and old_image_filename is not None
        ):
            delete_image(old_image_filename, "equipment")

        cache_delete(CACHE_KEY_DASHBOARD_STATS)

        flash(
            "Equipment updated successfully.",
            "success",
        )
        return redirect(url_for(
            "equipment.detail",
            equipment_id=equipment.id,
        ))

    return render_template(
        "equipment/edit.html",
        form=form,
        equipment=equipment,
    )


# =========================================================
# DELETE
# =========================================================

@equipment_bp.route("/<int:equipment_id>/delete", methods=["GET", "POST"])
@login_required
@role_required("Administrator")
def delete(equipment_id):
    """Delete an equipment record."""

    equipment = Equipment.query.get_or_404(equipment_id)

    if request.method == "POST":

        asset_tag = equipment.asset_tag
        equipment_db_id = equipment.id

        if equipment.image_filename:
            delete_image(equipment.image_filename, "equipment")

        db.session.delete(equipment)

        log_activity(
            "delete",
            "Equipment",
            equipment_db_id,
            f"Deleted equipment {asset_tag}",
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "Equipment could not be deleted. Please try again.",
                "danger",
            )
            return redirect(url_for("equipment.index"))

        cache_delete(CACHE_KEY_DASHBOARD_STATS)

        flash(
            "Equipment deleted successfully.",
            "success",
        )
        return redirect(url_for("equipment.index"))

    return render_template(
        "equipment/delete.html",
        equipment=equipment,
    )


# =========================================================
# INDEX
# =========================================================

@equipment_bp.route("/")
@login_required
def index():
    """Display the ICT equipment inventory."""

    search = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    status = request.args.get("status", "").strip()
    location_id = request.args.get("location", type=int)
    page = request.args.get("page", 1, type=int)

    categories = get_cached_categories()
    locations = get_cached_locations()

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

    pagination = query.order_by(Equipment.id.desc()).paginate(
        page=page,
        per_page=10,
    )

    return render_template(
        "equipment/index.html",
        equipment=pagination.items,
        pagination=pagination,
        search=search,
        categories=categories,
        locations=locations,
        selected_category=category_id,
        selected_status=status,
        selected_location=location_id,
    )