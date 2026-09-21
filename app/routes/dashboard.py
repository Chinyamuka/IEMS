
from flask import render_template, Blueprint
from app.models.equipment import Equipment

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
@dashboard_bp.route("/")
def index():
    total_equipment = Equipment.query.count()
    in_stock = Equipment.query.filter_by(status="In Stock" ).count()
    assigned = Equipment.query.filter_by( status="Assigned" ).count()
    under_repair = Equipment.query.filter_by( status="Under Repair").count()
    retired = Equipment.query.filter_by(status="Retired").count()
    return render_template("dashboard/index.html",
        total_equipment=total_equipment,
        in_stock=in_stock,
        assigned=assigned,
        under_repair=under_repair,
        retired=retired,
    )
