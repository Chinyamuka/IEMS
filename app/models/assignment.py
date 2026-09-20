
from datetime import datetime
from app.extensions import db


class EquipmentAssignment(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    equipment_id = db.Column(db.Integer,db.ForeignKey("equipment.id"),nullable=False, index=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False,index=True)
    assigned_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow )
    returned_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column( db.Text, nullable=True)
    equipment = db.relationship("Equipment",backref=db.backref("assignments",lazy=True))
    user = db.relationship( "User", backref=db.backref("equipment_assignments",lazy=True))

    @property
    def is_active(self):
        return self.returned_at is None

    def __repr__(self):
        return f"<EquipmentAssignment {self.id}>"