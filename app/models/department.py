"""
IEMS Department Model

Stores organizational departments.
"""

from app.extensions import db

class Department(db.Model):
    __tablename__ = "department"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False,unique=True,index=True)
    description = db.Column(db.Text,nullable=True)
    users = db.relationship("User",back_populates="department", lazy=True)
    def __repr__(self):
        return f"<Department {self.name}>"