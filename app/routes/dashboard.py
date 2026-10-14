"""
IEMS Dashboard Routes

The dashboard is available to every authenticated IEMS user.

RBAC is still enforced on operations such as:
- Creating equipment
- Editing equipment
- Deleting equipment
- Assigning equipment
- Managing employees/users

The dashboard itself is read-only.
"""

from collections import Counter

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
)

from app.models import Equipment, ActivityLog


# =========================================================
# BLUEPRINT
# =========================================================

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
)


# =========================================================
# DASHBOARD
# =========================================================

@dashboard_bp.route("/")
def index():
    """
    Display the IEMS dashboard.

    Any authenticated user may view the dashboard.
    RBAC is applied to sensitive operations elsewhere.
    """

    # -----------------------------------------------------
    # AUTHENTICATION CHECK
    # -----------------------------------------------------

    if not session.get("user_id"):
        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # LOAD EQUIPMENT
    # -----------------------------------------------------

    equipment = Equipment.query.order_by(
        Equipment.created_at.desc()
    ).all()

    total_equipment = len(equipment)

    # -----------------------------------------------------
    # STATUS COUNTS
    # -----------------------------------------------------

    status_counter = Counter()

    for item in equipment:

        status = (item.status or "Unknown").strip()

        status_counter[status] += 1

    in_stock = sum(
        count
        for status, count in status_counter.items()
        if status.lower() == "in stock"
    )

    assigned = sum(
        count
        for status, count in status_counter.items()
        if status.lower() == "assigned"
    )

    under_repair = sum(
        count
        for status, count in status_counter.items()
        if status.lower() in {
            "under repair",
            "under maintenance",
            "maintenance",
        }
    )

    retired = sum(
        count
        for status, count in status_counter.items()
        if status.lower() in {
            "retired",
            "disposed",
        }
    )

    # -----------------------------------------------------
    # EQUIPMENT BY CATEGORY
    # -----------------------------------------------------

    category_counter = Counter()

    for item in equipment:

        if item.category:
            category_name = item.category.name
        else:
            category_name = "Uncategorised"

        category_counter[category_name] += 1

    category_statistics = sorted(
        category_counter.items(),
        key=lambda row: row[0].lower()
    )

    # -----------------------------------------------------
    # EQUIPMENT BY STATUS
    # -----------------------------------------------------

    status_statistics = sorted(
        status_counter.items(),
        key=lambda row: row[0].lower()
    )

    # -----------------------------------------------------
    # RECENT EQUIPMENT
    # -----------------------------------------------------

    recent_equipment = equipment[:5]

    # -----------------------------------------------------
    # RECENT ACTIVITY
    # -----------------------------------------------------
    #
    # The latest audit-trail entries. Limited to 10 so the
    # dashboard stays compact; the full list is available
    # on /activity/ (E6).
    #
    # ordered by created_at DESC rather than id DESC so
    # the list reflects event time, not insertion order,
    # if the DB has been restored from a backup.
    #

    recent_activity = (
        ActivityLog.query
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render_template(
        "dashboard/index.html",

        # Summary
        total_equipment=total_equipment,
        in_stock=in_stock,
        assigned=assigned,
        under_repair=under_repair,
        retired=retired,

        # Breakdown
        category_statistics=category_statistics,
        status_statistics=status_statistics,

        # Recent records
        recent_equipment=recent_equipment,

        # Audit trail
        recent_activity=recent_activity,
    )