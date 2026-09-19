"""
IEMS Location Model

Stores the physical locations where ICT equipment
can be installed, stored, or assigned.
"""

from app.extensions import db


class Location(db.Model):
    """Represents a physical location within the organization."""

    id = db.Column( db.Integer,primary_key=True)
    name = db.Column(db.String(150),nullable=False,unique=True)
    description = db.Column(db.Text,nullable=True)
    building = db.Column(db.String(150),nullable=True)
    room = db.Column(db.String(100),nullable=True)

    def __repr__(self):
        """Developer-friendly representation."""
        return f"<Location {self.name}>"
