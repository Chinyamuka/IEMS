from . import dashboard, departments
from .auth import auth_bp
from .categories import categories_bp
from .dashboard import dashboard_bp
from .departments import departments_bp
from .equipment import  equipment_bp
from .assignment import assignment_bp
from .locations import locations_bp
from .profile import profile_bp
from .users import users_bp

def register_routes(app):
    app.register_blueprint(equipment_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(categories_bp)