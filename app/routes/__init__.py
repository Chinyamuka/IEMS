from .equipment import  equipment_bp
def register_routes(app):
    app.register_blueprint(equipment_bp)