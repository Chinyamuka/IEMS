"""
IEMS Equipment Routes

Contains routes responsible for creating and viewing
ICT equipment records.
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    url_for,
)

from app.extensions import db
from app.forms.equipment_form import EquipmentForm
from app.models.category import Category
from app.models.location import Location
from app.models.equipment import Equipment


# Create the equipment Blueprint.
#
# A Blueprint allows us to organize routes into separate
# modules instead of putting every route in app/__init__.py.
equipment_bp = Blueprint(
    "equipment",
    __name__,
    url_prefix="/equipment",
)


@equipment_bp.route("/new", methods=["GET", "POST"])
def create():
    """
    Display the equipment registration form and process
    submitted equipment data.
    """

    # Create the WTForms form.
    form = EquipmentForm()

    # ---------------------------------------------------------
    # LOAD CATEGORY OPTIONS
    # ---------------------------------------------------------

    # Retrieve all categories from PostgreSQL.
    categories = Category.query.order_by(
        Category.name
    ).all()

    # Convert categories into choices understood by SelectField.
    form.category_id.choices = [
        (category.id, category.name)
        for category in categories
    ]

    # ---------------------------------------------------------
    # LOAD LOCATION OPTIONS
    # ---------------------------------------------------------

    # Retrieve all locations from PostgreSQL.
    locations = Location.query.order_by(
        Location.name
    ).all()

    form.location_id.choices = [
        (location.id, location.name)
        for location in locations
    ]

    # ---------------------------------------------------------
    # PROCESS FORM SUBMISSION
    # ---------------------------------------------------------

    if form.validate_on_submit():
        # CHECK FOR DUPLICATION IN ASSET TAGS AND/OR SERIAL NUMBERS
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

        equipment = Equipment(
            asset_tag=form.asset_tag.data,
            serial_number=form.serial_number.data,
            manufacturer=form.manufacturer.data,
            model=form.model.data,
            description=form.description.data,
            category_id=form.category_id.data,
            location_id=form.location_id.data,
            status=form.status.data,
            condition=form.condition.data,
            purchase_date=form.purchase_date.data,
            purchase_price=form.purchase_price.data,
            warranty_expiry=form.warranty_expiry.data,
        )

        # Add the new object to SQLAlchemy's session.
        db.session.add(equipment)

        # Save the record to PostgreSQL.
        db.session.commit()

        # Show a success message to the user.
        flash(
            "Equipment registered successfully.",
            "success",
        )

        # Redirect to the equipment list.
        return redirect(
            url_for("equipment.index")
        )

    # Display the registration page.
    return render_template(
        "equipment/create.html",
        form=form,
    )


@equipment_bp.route("/")
def index():
    """
    Display all registered ICT equipment.
    """

    # Retrieve equipment from PostgreSQL.
    equipment = Equipment.query.order_by(
        Equipment.id.desc()
    ).all()

    return render_template(
        "equipment/index.html",
        equipment=equipment,
    )

# DETAILS OF THE EQUIPMENT
@equipment_bp.route("/<int:equipment_id>")
def detail(equipment_id):
    # If it does not exist:
    # Flask automatically returns a 404 page.
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template(
        "equipment/detail.html",
        equipment=equipment,
    )