"""
IEMS Equipment Assignment Form

This form is used when assigning ICT equipment
to an employee/user.
"""

from flask_wtf import FlaskForm

from wtforms import (
    SelectField,
    DateTimeLocalField,
    TextAreaField,
    SubmitField,
)

from wtforms.validators import DataRequired, Optional


class EquipmentAssignmentForm(FlaskForm):
    """
    Form used to assign equipment to a user.
    """

    # ---------------------------------------------------------
    # EQUIPMENT
    # ---------------------------------------------------------
    # The choices will be populated dynamically from the
    # equipment database inside the route.
    equipment_id = SelectField(
        "Equipment",
        coerce=int,
        validators=[
            DataRequired()
        ]
    )

    # ---------------------------------------------------------
    # USER
    # ---------------------------------------------------------
    # The choices will also be populated dynamically from
    # active users in the database.
    user_id = SelectField(
        "Assign To",
        coerce=int,
        validators=[
            DataRequired()
        ]
    )

    # ---------------------------------------------------------
    # ASSIGNMENT DATE
    # ---------------------------------------------------------
    # This allows the user to specify when the equipment
    # was assigned.
    assigned_at = DateTimeLocalField(
        "Assignment Date",
        format="%Y-%m-%dT%H:%M",
        validators=[
            DataRequired()
        ]
    )

    # ---------------------------------------------------------
    # NOTES
    # ---------------------------------------------------------
    # Optional notes about the assignment.
    notes = TextAreaField(
        "Notes",
        validators=[
            Optional()
        ]
    )

    # ---------------------------------------------------------
    # SUBMIT BUTTON
    # ---------------------------------------------------------
    submit = SubmitField(
        "Assign Equipment"
    )