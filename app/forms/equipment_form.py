"""
IEMS Equipment Form

Defines the form used to register ICT equipment.
"""

from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    DateField,
    DecimalField,
    FileField,
    SubmitField,
)

from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
    NumberRange,
)


class EquipmentForm(FlaskForm):
    """Form used to create a new equipment record."""

    # -----------------------------------------------------
    # IDENTIFICATION
    # -----------------------------------------------------

    asset_tag = StringField(
        "Asset Tag",
        validators=[
            DataRequired(),
            Length(max=50),
        ],
        render_kw={"placeholder": "Example: ICT-00001"},
    )

    serial_number = StringField(
        "Serial Number",
        validators=[
            Optional(),
            Length(max=150),
        ],
        render_kw={"placeholder": "Example: ABC123456"},
    )

    manufacturer = StringField(
        "Manufacturer",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
        render_kw={"placeholder": "Example: Dell"},
    )

    model = StringField(
        "Model",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
        render_kw={"placeholder": "Example: Latitude 5540"},
    )

    description = TextAreaField(
        "Description",
        validators=[Optional()],
        render_kw={
            "placeholder": "Additional information about the equipment"
        },
    )

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------
    #
    # Optional. The upload helper (app/utils/uploads.py)
    # validates the extension and contents with Pillow.
    # No WTForms validators here — they would duplicate
    # that logic and produce competing error messages.
    #
    image = FileField(
        "Equipment Photo",
    )

    # -----------------------------------------------------
    # CLASSIFICATION
    # -----------------------------------------------------

    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired()],
    )

    location_id = SelectField(
        "Location",
        coerce=int,
        validators=[Optional()],
    )

    status = SelectField(
        "Status",
        choices=[
            ("In Stock", "In Stock"),
            ("Assigned", "Assigned"),
            ("Under Maintenance", "Under Maintenance"),
            ("Lost", "Lost"),
            ("Retired", "Retired"),
            ("Disposed", "Disposed"),
        ],
        validators=[DataRequired()],
    )

    condition = SelectField(
        "Condition",
        choices=[
            ("Excellent", "Excellent"),
            ("Good", "Good"),
            ("Fair", "Fair"),
            ("Poor", "Poor"),
            ("Damaged", "Damaged"),
        ],
        validators=[DataRequired()],
    )

    # -----------------------------------------------------
    # PROCUREMENT
    # -----------------------------------------------------

    purchase_date = DateField(
        "Purchase Date",
        validators=[DataRequired()],
    )

    purchase_price = DecimalField(
        "Purchase Price",
        validators=[Optional(), NumberRange(min=0)],
        places=2,
    )

    warranty_expiry = DateField(
        "Warranty Expiry",
        validators=[Optional()],
    )

    # -----------------------------------------------------
    # SUBMIT
    # -----------------------------------------------------

    submit = SubmitField("Register Equipment")  