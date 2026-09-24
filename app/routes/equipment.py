"""
IEMS Equipment Routes

Contains routes responsible for creating and viewing
ICT equipment records.
"""
from app.models import category
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    url_for,
    request,
)
from app.utils.permissions import login_required, role_required
from app.extensions import db
from app.forms.equipment_form import EquipmentForm
from app.models.category import Category
from app.models.location import Location
from app.models.equipment import Equipment
from app.auth.decorators import login_required


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
@role_required("ADMIN","INVENTORY_MANAGER")
@login_required
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

# DETAILS OF THE EQUIPMENT
@equipment_bp.route("/<int:equipment_id>")
@login_required
def detail(equipment_id):
    # If it does not exist:
    # Flask automatically returns a 404 page.
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template(
        "equipment/detail.html",
        equipment=equipment,
    )

@equipment_bp.route("/<int:equipment_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("ADMIN","INVENTORY_MANAGER")
def edit(equipment_id):
    """
    Edit an existing equipment record.

    GET:
        Display the existing equipment information
        inside the form.

    POST:
        Validate the submitted changes and save them
        to PostgreSQL.
    """

    # ---------------------------------------------------------
    # FIND THE EQUIPMENT
    # ---------------------------------------------------------

    # Find the equipment using its primary key.
    #
    # If the equipment doesn't exist, Flask automatically
    # returns a 404 Not Found response.
    equipment = Equipment.query.get_or_404(
        equipment_id
    )

    # ---------------------------------------------------------
    # CREATE THE FORM
    # ---------------------------------------------------------

    # Populate the form with the current equipment values.
    #
    # obj=equipment means WTForms will initially display
    # the values already stored in the database.
    form = EquipmentForm(obj=equipment)

    # ---------------------------------------------------------
    # LOAD CATEGORY OPTIONS
    # ---------------------------------------------------------

    categories = Category.query.order_by(
        Category.name
    ).all()

    form.category_id.choices = [
        (category.id, category.name)
        for category in categories
    ]

    # ---------------------------------------------------------
    # LOAD LOCATION OPTIONS
    # ---------------------------------------------------------

    locations = Location.query.order_by(
        Location.name
    ).all()

    form.location_id.choices = [
        (location.id, location.name)
        for location in locations
    ]

    # ---------------------------------------------------------
    # PROCESS SUBMISSION
    # ---------------------------------------------------------

    if form.validate_on_submit():

        # -----------------------------------------------------
        # CHECK FOR DUPLICATE ASSET TAG
        # -----------------------------------------------------

        # Search for another equipment record using the
        # submitted asset tag.
        existing_equipment = Equipment.query.filter(
            Equipment.asset_tag == form.asset_tag.data,
            Equipment.id != equipment.id,
        ).first()

        # If another record already uses this asset tag,
        # stop the update.
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

        # -----------------------------------------------------
        # UPDATE THE EQUIPMENT
        # -----------------------------------------------------

        # Copy the submitted form values into the existing
        # SQLAlchemy object.

        equipment.asset_tag = form.asset_tag.data

        equipment.serial_number = (
            form.serial_number.data
        )

        equipment.manufacturer = (
            form.manufacturer.data
        )

        equipment.model = form.model.data

        equipment.description = (
            form.description.data
        )

        equipment.category_id = (
            form.category_id.data
        )

        equipment.location_id = (
            form.location_id.data
        )

        equipment.status = form.status.data

        equipment.condition = form.condition.data

        equipment.purchase_date = (
            form.purchase_date.data
        )

        equipment.purchase_price = (
            form.purchase_price.data
        )

        equipment.warranty_expiry = (
            form.warranty_expiry.data
        )

        # -----------------------------------------------------
        # SAVE CHANGES
        # -----------------------------------------------------

        # SQLAlchemy detects the changes and generates the
        # appropriate UPDATE statement.
        #
        # Our updated_at column will also be updated because
        # of the model's onupdate configuration.
        db.session.commit()

        # Tell the user the update was successful.
        flash(
            "Equipment updated successfully.",
            "success",
        )

        # Return to the equipment detail page.
        return redirect(
            url_for(
                "equipment.detail",
                equipment_id=equipment.id,
            )
        )

    # ---------------------------------------------------------
    # DISPLAY EDIT FORM
    # ---------------------------------------------------------

    return render_template(
        "equipment/edit.html",
        form=form,
        equipment=equipment,
    )

@equipment_bp.route("/<int:equipment_id>/delete", methods=["GET", "POST"])
@login_required
@role_required("ADMIN")
def delete(equipment_id):
    """
    Delete an equipment record.

    GET:
        Display a confirmation page.

    POST:
        Permanently remove the equipment from the database.
    """

    # ---------------------------------------------------------
    # FIND EQUIPMENT
    # ---------------------------------------------------------

    equipment = Equipment.query.get_or_404(
        equipment_id
    )

    # ---------------------------------------------------------
    # CONFIRM DELETION
    # ---------------------------------------------------------

    if request.method == "POST":

        # Delete the equipment object.
        db.session.delete(equipment)

        # Save the deletion to PostgreSQL.
        db.session.commit()

        # Tell the user the deletion succeeded.
        flash(
            "Equipment deleted successfully.",
            "success",
        )

        # Return to the equipment list.
        return redirect(
            url_for("equipment.index")
        )

    # ---------------------------------------------------------
    # SHOW CONFIRMATION PAGE
    # ---------------------------------------------------------

    return render_template(
        "equipment/delete.html",
        equipment=equipment,
    )

@equipment_bp.route("/")
@login_required
def index():
    """
    Display the ICT equipment inventory.

    Features:
    - Search by asset tag
    - Search by serial number
    - Search by manufacturer
    - Search by model
    - Filter by category
    - Filter by status
    - Filter by location
    - Pagination
    """

    # =========================================================
    # READ SEARCH AND FILTER VALUES FROM THE URL
    # =========================================================

    # Search text.
    #
    # Example:
    # /equipment/?q=dell
    search = request.args.get(
        "q",
        ""
    ).strip()


    # Category filter.
    #
    # type=int automatically converts the value
    # from a string to an integer.
    #
    # Example:
    # /equipment/?category=2
    category_id = request.args.get(
        "category",
        type=int
    )


    # Status filter.
    #
    # Example:
    # /equipment/?status=In%20Stock
    status = request.args.get(
        "status",
        ""
    ).strip()


    # Location filter.
    #
    # Example:
    # /equipment/?location=1
    location_id = request.args.get(
        "location",
        type=int
    )


    # =========================================================
    # READ PAGE NUMBER
    # =========================================================

    # Get the requested page from the URL.
    #
    # Example:
    # /equipment/?page=2
    #
    # If no page is supplied, page 1 is used.
    page = request.args.get(
        "page",
        1,
        type=int
    )


    # =========================================================
    # LOAD CATEGORY OPTIONS
    # =========================================================

    # Import the Category model.
    from app.models.category import Category

    # Get all categories for the filter dropdown.
    categories = Category.query.order_by(
        Category.name.asc()
    ).all()


    # =========================================================
    # LOAD LOCATION OPTIONS
    # =========================================================

    # Import the Location model.
    from app.models.location import Location

    # Get all locations for the filter dropdown.
    locations = Location.query.order_by(
        Location.name.asc()
    ).all()


    # =========================================================
    # START THE EQUIPMENT QUERY
    # =========================================================

    # Start with all equipment.
    #
    # We will progressively add filters to this query.
    query = Equipment.query


    # =========================================================
    # SEARCH FILTER
    # =========================================================

    if search:

        # Add % around the search value.
        #
        # Example:
        # Dell
        #
        # becomes:
        # %Dell%
        #
        # This means "contains Dell".
        search_term = f"%{search}%"


        # Search across multiple equipment fields.
        query = query.filter(
            db.or_(
                Equipment.asset_tag.ilike(search_term),
                Equipment.serial_number.ilike(search_term),
                Equipment.manufacturer.ilike(search_term),
                Equipment.model.ilike(search_term),
            )
        )


    # =========================================================
    # CATEGORY FILTER
    # =========================================================

    if category_id:

        query = query.filter(
            Equipment.category_id == category_id
        )


    # =========================================================
    # STATUS FILTER
    # =========================================================

    if status:

        query = query.filter(
            Equipment.status == status
        )


    # =========================================================
    # LOCATION FILTER
    # =========================================================

    if location_id:

        query = query.filter(
            Equipment.location_id == location_id
        )


    # =========================================================
    # PAGINATION
    # =========================================================

    # Number of records displayed on each page.
    per_page = 10
    pagination = query.order_by(
        Equipment.id.desc()
    ).paginate(
        page=page,
        per_page=per_page
    )


    # =========================================================
    # GET RECORDS FOR CURRENT PAGE
    # =========================================================

    # pagination.items contains only the equipment
    # records belonging to the current page.
    equipment = pagination.items


    # =========================================================
    # SEND DATA TO THE TEMPLATE
    # =========================================================

    return render_template(
        "equipment/index.html",
        equipment=equipment,
        pagination=pagination,
        search=search,
        categories=categories,
        locations=locations,
        selected_category=category_id,
        selected_status=status,
        selected_location=location_id,
    )

