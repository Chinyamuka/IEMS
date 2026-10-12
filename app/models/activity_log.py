"""
IEMS Activity Log Model

One row per meaningful change in the system. Provides
an audit trail: who did what, to which entity, and when.

The log is written in the SAME transaction as the change
it describes (see app/utils/activity.py). If the change
rolls back, the log entry rolls back too — no orphan
entries.
"""

from datetime import datetime

from app.extensions import db


class ActivityLog(db.Model):
    """A single audit-trail entry."""

    __tablename__ = "activity_log"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # -----------------------------------------------------
    # WHO
    # -----------------------------------------------------
    #
    # Nullable: an event may have no logged-in user
    # (system action, or the user was deleted). We keep
    # the row rather than lose the audit record.
    #
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True,
        index=True,
    )

    # -----------------------------------------------------
    # WHAT
    # -----------------------------------------------------
    #
    # action is a short verb: "create", "update",
    # "delete", "login", "logout", "return", etc.
    #
    # entity_type names the model involved:
    # "Equipment", "User", "Department", "Location",
    # "Category", "EquipmentAssignment".
    #
    # entity_id is the primary key of the affected row,
    # when applicable. Nullable for events with no single
    # entity (e.g. login).
    #
    # summary is a human-readable one-liner. Pre-rendered
    # at write time because reconstructing it later would
    # require joining back to the entity — which fails if
    # the entity has been deleted (exactly when you most
    # want the log).
    #

    action = db.Column(
        db.String(50),
        nullable=False,
    )

    entity_type = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    )

    entity_id = db.Column(
        db.Integer,
        nullable=True,
    )

    summary = db.Column(
        db.String(255),
        nullable=False,
    )

    # -----------------------------------------------------
    # WHEN
    # -----------------------------------------------------
    #
    # Indexed because every listing query sorts by
    # created_at DESC.
    #
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # -----------------------------------------------------
    # RELATIONSHIP
    # -----------------------------------------------------

    user = db.relationship(
        "User",
        backref=db.backref(
            "activity_logs",
            lazy=True,
        ),
    )

    def __repr__(self):
        return (
            f"<ActivityLog {self.id} "
            f"{self.action} {self.entity_type}>"
        )
