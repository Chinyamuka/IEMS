
from flask import Blueprint,render_template
from app.extensions import db
from app.models.equipment import Equipment
from app.models.category import Category

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
@dashboard_bp.route("/")
def index():
    total_equipment = Equipment.query.count()
    in_stock = Equipment.query.filter_by( status="In Stock").count()
    assigned = Equipment.query.filter_by(status="Assigned" ).count()
    under_repair = Equipment.query.filter_by( status="Under Repair").count()
    retired = Equipment.query.filter_by( status="Retired" ).count()
    category_statistics = ( db.session.query(Category.name,  db.func.count(Equipment.id))
                            .join(Equipment,Equipment.category_id == Category.id).group_by( Category.id, Category.name)
                            .order_by(
                            db.func.count(Equipment.id).desc()).all())
    return render_template(
        "dashboard/index.html",
        total_equipment=total_equipment,
        in_stock=in_stock,
        assigned=assigned,
        under_repair=under_repair,
        retired=retired,
        category_statistics=category_statistics,
    )

