

from app.extensions import db


class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    employee_number = db.Column(db.String(50),nullable=False,unique=True,index=True)
    first_name = db.Column(db.String(100), nullable=False )
    last_name = db.Column(db.String(100),nullable=False)
    email = db.Column( db.String(150),nullable=True, unique=True)
    phone = db.Column( db.String(50),nullable=True)
    department_id = db.Column( db.Integer,db.ForeignKey("department.id"), nullable=True,index=True)
    is_active = db.Column( db.Boolean,nullable=False,default=True)
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    def __repr__(self):
        return f"<User {self.employee_number}>"