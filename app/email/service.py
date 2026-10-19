# app/email/service.py
"""
Send logic + the MAIL_ENABLED kill-switch.

Every outbound email in IEMS goes through send(). This
module is the single choke point where retries, outbox
handling, and audit logging will be added in later tasks
without touching any caller.

Design rules:

    - send() never raises. A mail failure must not break
      the request that triggered it.

    - Callers never touch flask_mail.Message. The
      private _to_flask_message adapter is the only
      place that knows Flask-Mail exists.

    - The kill-switch is two-layered: Flask-Mail's own
      MAIL_SUPPRESS_SEND stops the wire, and our early
      return logs which message was skipped. This makes
      "mail is off" distinguishable from "SMTP rejected
      it" when debugging delivery.
"""
from __future__ import annotations

import logging
from typing import Iterable

from flask import current_app
from flask_mail import Message

from app.extensions import mail
from app.email.message import Email

log = logging.getLogger(__name__)


def _to_flask_message(email: Email) -> Message:
    """
    Adapt our Email value object to a Flask-Mail Message.

    Private on purpose: if the transport ever changes
    (outbox, SES, Postmark), only this function is
    rewritten. Callers stay on app.email.Email.
    """
    return Message(
        subject=email.subject,
        recipients=list(email.to),
        cc=list(email.cc) or None,
        bcc=list(email.bcc) or None,
        reply_to=email.reply_to,
        body=email.body or None,
        html=email.html,
    )


def send(email: Email) -> bool:
    """
    Send one email.

    Returns True if the SMTP server accepted the message
    (or the send was suppressed by MAIL_ENABLED=false).
    Returns False if the message could not be delivered.

    Never raises. A mail failure is logged with full
    traceback and reported via return value so the caller
    can decide whether to surface a warning.
    """
    if not current_app.config.get("MAIL_SERVER"):
        log.info("send(): MAIL_SERVER unset; skipping %r", email.subject)
        return False

    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        log.info(
            "send(): suppressed (MAIL_ENABLED=false) subject=%r to=%s",
            email.subject,
            email.to,
        )
        return True

    try:
        mail.send(_to_flask_message(email))
        log.info("send(): ok subject=%r to=%s", email.subject, email.to)
        return True

    except Exception:   # noqa: BLE001
        # Deliberately broad. The only other alternative is
        # enumerating every SMTP error subclass Flask-Mail
        # and smtplib can raise, which would still miss
        # socket-level errors (DNS, TCP, TLS). A mail
        # outage must never propagate into the caller.
        log.exception(
            "send(): failed subject=%r to=%s",
            email.subject,
            email.to,
        )
        return False


def send_many(emails: Iterable[Email]) -> list[bool]:
    """
    Send several emails, one at a time.

    Sequential rather than concurrent: Mailtrap's sandbox
    rate-limits and concurrency buys nothing at IEMS
    scale. If N4 needs throughput, batching happens there.
    """
    return [send(e) for e in emails]
