from . import dashboard
from .auth import auth_bp
from .dashboard import dashboard_bp
from .equipment import  equipment_bp
from .assignment import assignment_bp
from .users import users_bp

def register_routes(app):
    app.register_blueprint(equipment_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
