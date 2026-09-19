"""
IEMS Department Model

Stores organizational departments that users and ICT equipment
can be associated with.
"""

from app.extensions import db


class Department(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(150),nullable=False,unique=True)
    description = db.Column(db.Text,nullable=True)
    users = db.relationship( "User", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"