"""
IEMS Activity Log Helper

Single function for writing audit entries. Called
from routes that mutate data.

Important: this helper does NOT commit. It adds the
log entry to the current SQLAlchemy session and lets
the caller's existing commit flush both the primary
change and the log row in one transaction. If the
primary change fails and rolls back, the log entry
rolls back with it — no orphan log entries.

Usage inside a route:

    equipment = Equipment(...)
    db.session.add(equipment)
    db.session.flush()  # optional — needed only if you
                        # reference equipment.id in the
                        # summary

    log_activity(
        "create",
        "Equipment",
        equipment.id,
        f"Registered equipment {equipment.asset_tag}",
    )

    db.session.commit()

The user is read from g.current_user, which is
populated by load_current_user() on every request.
"""

from flask import g

from app.extensions import db
from app.models import ActivityLog


def log_activity(action, entity_type, entity_id, summary):
    """
    Queue an audit entry.

    Parameters
    ----------
    action : str
        Short verb: "create", "update", "delete",
        "login", "logout", "return", etc.
    entity_type : str
        Model name: "Equipment", "User", "Department",
        "Location", "Category", "EquipmentAssignment".
    entity_id : int | None
        Primary key of the affected row, or None for
        events that are not tied to a single entity
        (e.g. login).
    summary : str
        Human-readable one-liner. Keep under 255 chars
        to match the schema.
    """

    user_id = None

    current_user = g.get("current_user")
    if current_user is not None:
        user_id = current_user.id

    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
    )

    db.session.add(log)
