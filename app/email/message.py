# app/email/message.py
"""
The Email value object callers construct and hand to send().

Immutable by design: once built, an Email cannot be
mutated. This removes a class of "the message changed
between when it was queued and when it was sent" bugs
and makes the object safe to log, cache, or pass across
function boundaries.

Address syntax is NOT validated here. That is a
form-layer concern. This module only enforces structural
completeness sufficient to attempt delivery.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Email:
    """A single outbound email."""

    to: tuple[str, ...]
    subject: str
    body: str = ""
    html: str | None = None
    cc: tuple[str, ...] = field(default_factory=tuple)
    bcc: tuple[str, ...] = field(default_factory=tuple)
    reply_to: str | None = None

    def __post_init__(self):
        # Structural completeness. If either is missing the
        # caller has a bug — fail at the call site, not inside
        # Flask-Mail where the traceback is unhelpful.
        if not self.to:
            raise ValueError("Email.to must contain at least one recipient")
        if not self.subject:
            raise ValueError("Email.subject is required")
