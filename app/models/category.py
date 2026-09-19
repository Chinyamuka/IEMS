"""
IEMS Equipment Category Model

This model stores the different categories of ICT equipment
managed by the system.
"""
from app.extensions import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    def __repr__(self):
        return f"<Category {self.name}>"