"""
IEMS Dashboard Routes

The dashboard is available to every authenticated IEMS
user. Stats are cached in Redis with a 60s TTL to avoid
recomputing on every page load. Mutating routes clear
the cache when equipment changes.
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
    }