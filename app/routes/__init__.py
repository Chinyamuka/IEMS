from . import dashboard
from .dashboard import dashboard_bp
from .equipment import  equipment_bp
def register_routes(app):
    app.register_blueprint(equipment_bp)
    app.register_blueprint(dashboard_bp)