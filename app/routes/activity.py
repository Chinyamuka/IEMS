"""
IEMS Activity Log Routes

Administrator-only view of the audit trail. Provides
filtering by user, entity type, action and date range,
with pagination.
"""

from datetime import datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    request,
)

from app.extensions import db
from app.models import ActivityLog, User
from app.auth.decorators import login_required
from app.utils.permissions import role_required


# =========================================================
# BLUEPRINT
# =========================================================

activity_bp = Blueprint(
    "activity",
    __name__,
    url_prefix="/activity",
)


# =========================================================
# FILTER OPTIONS
# =========================================================

ENTITY_TYPES = [
    "Equipment",
    "EquipmentAssignment",
    "User",
    "Department",
    "Location",
    "Category",
]

ACTIONS = [
    "create",
    "update",
    "delete",
    "assign",
    "return",
    "deactivate",
    "activate",
    "password_change",
]


# =========================================================
# LIST
# =========================================================

@activity_bp.route("/")
@login_required
@role_required("Administrator")
def index():
    """
    Display the activity log with optional filters.

    Query params:
        user_id      integer
        entity_type  string
        action       string
        from         YYYY-MM-DD
        to           YYYY-MM-DD
        page         integer
    """

    user_id = request.args.get("user_id", type=int)
    entity_type = request.args.get("entity_type", "").strip()
    action = request.args.get("action", "").strip()
    from_date = request.args.get("from", "").strip()
    to_date = request.args.get("to", "").strip()
    page = request.args.get("page", 1, type=int)

    # -----------------------------------------------------
    # BASE QUERY
    # -----------------------------------------------------

    query = ActivityLog.query

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)

    if entity_type:
        query = query.filter(
            ActivityLog.entity_type == entity_type
        )

    if action:
        query = query.filter(ActivityLog.action == action)

    if from_date:
        try:
            dt = datetime.strptime(from_date, "%Y-%m-%d")
            query = query.filter(ActivityLog.created_at >= dt)
        except ValueError:
            pass

    if to_date:
        try:
            dt = datetime.strptime(to_date, "%Y-%m-%d")
            dt = dt + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < dt)
        except ValueError:
            pass

    # -----------------------------------------------------
    # PAGINATE
    # -----------------------------------------------------

    pagination = query.order_by(
        ActivityLog.created_at.desc()
    ).paginate(
        page=page,
        per_page=50,
        error_out=False,
    )

    # -----------------------------------------------------
    # FILTER DROPDOWN DATA
    # -----------------------------------------------------

    users = User.query.order_by(
        User.first_name.asc(),
        User.last_name.asc(),
    ).all()

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render_template(
        "activity/index.html",
        pagination=pagination,
        logs=pagination.items,
        users=users,
        entity_types=ENTITY_TYPES,
        actions=ACTIONS,
        selected_user=user_id,
        selected_entity=entity_type,
        selected_action=action,
        selected_from=from_date,
        selected_to=to_date,
    )