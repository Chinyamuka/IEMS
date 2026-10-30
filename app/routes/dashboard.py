"""
IEMS Dashboard Routes

The dashboard is available to every authenticated IEMS
user. Stats are cached in Redis with a 60s TTL to avoid
recomputing on every page load. Mutating routes clear
the cache when equipment changes.
"""

from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
)

from app.extensions import db
from app.models import Equipment, ActivityLog, EquipmentAssignment
from app.utils.cache import (
    cache_get,
    cache_set,
)


# =========================================================
# BLUEPRINT
# =========================================================

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
)


# =========================================================
# CACHE KEY
# =========================================================
#
# Single key for the computed stats. Invalidation
# happens by cache_delete(CACHE_KEY_DASHBOARD_STATS)
# in the mutating routes.

CACHE_KEY_DASHBOARD_STATS = "dashboard:stats"


# =========================================================
# DASHBOARD
# =========================================================

@dashboard_bp.route("/")
def index():
    """Display the IEMS dashboard."""

    if not session.get("user_id"):
        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # CACHED STATS
    # -----------------------------------------------------

    stats = cache_get(CACHE_KEY_DASHBOARD_STATS)

    if stats is None:
        stats = _compute_stats()
        cache_set(
            CACHE_KEY_DASHBOARD_STATS,
            stats,
            ttl=60,
        )

    # -----------------------------------------------------
    # RECENT ACTIVITY (never cached — always fresh)
    # -----------------------------------------------------

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

        total_equipment=stats["total_equipment"],
        in_stock=stats["in_stock"],
        assigned=stats["assigned"],
        under_repair=stats["under_repair"],
        retired=stats["retired"],

        category_statistics=stats["category_statistics"],
        status_statistics=stats["status_statistics"],

        recent_equipment=stats["recent_equipment"],

        assignments_over_time=stats["assignments_over_time"],

        recent_activity=recent_activity,
    )


# =========================================================
# STATS COMPUTATION
# =========================================================
#
# This is the expensive part. Runs only on cache miss.

def _compute_stats():
    """
    Compute dashboard statistics. Returns a dict that
    can be JSON-serialized for the cache.

    The recent_equipment list stores plain primitives
    (id, asset_tag, etc.) rather than ORM objects, so
    the dict survives the JSON round-trip through Redis.
    """

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
        count for status, count in status_counter.items()
        if status.lower() == "in stock"
    )

    assigned = sum(
        count for status, count in status_counter.items()
        if status.lower() == "assigned"
    )

    under_repair = sum(
        count for status, count in status_counter.items()
        if status.lower() in {
            "under repair",
            "under maintenance",
            "maintenance",
        }
    )

    retired = sum(
        count for status, count in status_counter.items()
        if status.lower() in {"retired", "disposed"}
    )

    # -----------------------------------------------------
    # CATEGORY COUNTS
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
        key=lambda row: row[0].lower(),
    )

    status_statistics = sorted(
        status_counter.items(),
        key=lambda row: row[0].lower(),
    )

    # -----------------------------------------------------
    # RECENT EQUIPMENT
    # -----------------------------------------------------
    #
    # Serialized to plain dicts so the whole stats
    # object survives JSON serialization in Redis.

    recent_equipment_orm = equipment[:5]
    recent_equipment = [
        {
            "id": eq.id,
            "asset_tag": eq.asset_tag,
            "manufacturer": eq.manufacturer,
            "model": eq.model,
            "status": eq.status,
            "category_name": (
                eq.category.name if eq.category else None
            ),
        }
        for eq in recent_equipment_orm
    ]

    # -----------------------------------------------------
    # ASSIGNMENTS OVER TIME — last 6 calendar months
    # -----------------------------------------------------
    #
    # Portable approach: fetch only the assigned_at
    # timestamps for the last ~6 months, then bucket
    # them by month in Python. This works on every
    # SQLAlchemy dialect — Postgres, SQLite, MySQL —
    # with no database-specific SQL functions.
    #
    # Chart.js wants (labels[], values[]) aligned. We
    # build a zero-filled 6-bucket series so months with
    # no assignments still appear on the line, then
    # overlay the real counts.

    today = date.today()

    # First day of this month, minus 5 months = 6 buckets
    first_bucket = (
        today.replace(day=1) - timedelta(days=150)
    ).replace(day=1)

    # Fetch only the timestamps we need. On an IEMS-scale
    # inventory this is at most a few thousand rows — the
    # cost of the query is dominated by the index scan,
    # not the row payload.
    timestamp_rows = (
        db.session.query(EquipmentAssignment.assigned_at)
        .filter(EquipmentAssignment.assigned_at >= first_bucket)
        .all()
    )

    # Build the fixed 6-bucket month series first, so
    # months with no assignments are rendered as 0.
    months = OrderedDict()
    cursor = first_bucket
    while cursor <= today:
        months[cursor.strftime("%Y-%m")] = 0
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    # Overlay real counts.
    for (assigned_at,) in timestamp_rows:
        if assigned_at is None:
            continue
        month_key = assigned_at.strftime("%Y-%m")
        if month_key in months:
            months[month_key] += 1

    assignments_over_time = {
        "labels": [
            datetime.strptime(m, "%Y-%m").strftime("%b %Y")
            for m in months.keys()
        ],
        "values": list(months.values()),
    }

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

    return {
        "total_equipment": total_equipment,
        "in_stock": in_stock,
        "assigned": assigned,
        "under_repair": under_repair,
        "retired": retired,
        "category_statistics": category_statistics,
        "status_statistics": status_statistics,
        "recent_equipment": recent_equipment,
        "assignments_over_time": assignments_over_time,
    }