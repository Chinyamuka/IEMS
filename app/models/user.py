"""
IEMS User Model

This model represents employees/users in the system.

It also contains the authentication information required
for the future RBAC security system.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(db.Model):
    """Represents an employee and system user."""

    __tablename__ = "user"

    # ---------------------------------------------------------
    # PRIMARY KEY
    # ---------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ---------------------------------------------------------
    # EMPLOYEE INFORMATION
    # ---------------------------------------------------------

    # Unique employee identification number.
    employee_number = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True
    )

    # Employee first name.
    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    # Employee last name.
    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    # Employee email address.
    email = db.Column(
        db.String(150),
        nullable=True,
        unique=True
    )

    # Employee telephone number.
    phone = db.Column(
        db.String(50),
        nullable=True
    )

    # ---------------------------------------------------------
    # DEPARTMENT
    # ---------------------------------------------------------

    # Connects the employee to a department.
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("department.id"),
        nullable=True,
        index=True
    )

    # SQLAlchemy relationship to Department.
    department = db.relationship(
        "Department",
        back_populates="users"
    )

    # ---------------------------------------------------------
    # AUTHENTICATION
    # ---------------------------------------------------------

    # IMPORTANT:
    # We NEVER store the user's plain-text password.
    #
    # This column stores only the securely hashed password.
    password_hash = db.Column(
        db.String(300),
        nullable=False
    )

    # ---------------------------------------------------------
    # ACCOUNT STATUS
    # ---------------------------------------------------------

    # Determines whether the account can be used.
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # ---------------------------------------------------------
    # PASSWORD METHODS
    # ---------------------------------------------------------

    def set_password(self, password):
        """
        Hash a plain-text password and store the resulting hash.

        The actual password is never stored in the database.
        """

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Check a plain-text password against the stored hash.

        Returns:
            True  -> password is correct
            False -> password is incorrect
        """

        return check_password_hash(
            self.password_hash,
            password
        )

    # ---------------------------------------------------------
    # DISPLAY HELPERS
    # ---------------------------------------------------------

    @property
    def full_name(self):
        """Return the employee's complete name."""

        return f"{self.first_name} {self.last_name}"

    # ---------------------------------------------------------
    # DEBUG REPRESENTATION
    # ---------------------------------------------------------

    def __repr__(self):
        return f"<User {self.employee_number}>"