"""
IEMS Equipment Model

This is the central database model for the Inventory Management
System. Each record represents one physical ICT asset.
"""

from datetime import date

from app.extensions import db


class Equipment(db.Model):
    """Represents one physical piece of ICT equipment."""

    id = db.Column( db.Integer, primary_key=True  )
    asset_tag = db.Column(   db.String(50), nullable=False,unique=True,index=True)
    serial_number = db.Column(db.String(150),nullable=True,unique=True,index=True)
    manufacturer = db.Column(db.String(100),nullable=False)
    model = db.Column(db.String(150),nullable=False)
    description = db.Column(db.Text,nullable=True)
    category_id = db.Column(db.Integer,db.ForeignKey("category.id"),nullable=False,index=True)
    location_id = db.Column(db.Integer,db.ForeignKey("location.id"),nullable=True,index=True)
    status = db.Column(db.String(50),nullable=False,default="In Stock",index=True)
    condition = db.Column(db.String(50),nullable=False,default="Good")
    purchase_date = db.Column(db.Date,nullable=True)
    purchase_price = db.Column(db.Numeric(12, 2),nullable=True)
    warranty_expiry = db.Column(db.Date,nullable=True)
    created_at = db.Column(db.DateTime,nullable=False,server_default=db.func.now())
    updated_at = db.Column( db.DateTime,nullable=False,erver_default=db.func.now(),onupdate=db.func.now())
    category = db.relationship( "Category",backref=db.backref("equipment",lazy=True))
    location = db.relationship("Location",backref=db.backref("equipment",lazy=True))
    def __repr__(self):
        return f"<Equipment {self.asset_tag}>"
