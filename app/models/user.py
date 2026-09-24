"""
IEMS User Model

Stores employees/users who can access the Inventory Management System.
"""

from app.extensions import db


class User(db.Model):
    """Represents an employee/user in IEMS."""

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_number = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=True,
        unique=True
    )

    phone = db.Column(
        db.String(50),
        nullable=True
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("department.id"),
        nullable=True,
        index=True
    )

    # Stores the securely hashed password.
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # Role used by our RBAC system.
    role = db.Column(
        db.String(50),
        nullable=False,
        default="employee",
        index=True
    )

    # Controls whether the account can log in.
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # Explicit relationship to Department.
    department = db.relationship(
        "Department",
        back_populates="users"
    )

    @property
    def full_name(self):
        """Return the employee's full name."""
        return f"{self.first_name} {self.last_name}"
    def __repr__(self):
        return f"<User {self.employee_number}>"