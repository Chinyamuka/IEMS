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


# =========================================================
# TEMPLATE RENDERING
# =========================================================

def render(
    template_name: str,
    *,
    subject: str,
    to: tuple[str, ...],
    cc: tuple[str, ...] = (),
    bcc: tuple[str, ...] = (),
    reply_to: str | None = None,
    **context,
) -> Email:
    """
    Render an email template into a ready-to-send Email.

    Parameters
    ----------
    template_name : str
        Base name (no extension). Two files must exist
        under MAIL_TEMPLATE_DIR: <name>.html and <name>.txt.
    subject : str
        Set by the caller, not by the template. One
        template can be reused with different subjects
        (e.g. the same shell for password_reset and
        password_reset_reminder).
    to, cc, bcc, reply_to
        Recipients. Passed straight through to Email.
    **context
        Variables made available to both templates.

    Returns
    -------
    Email
        A complete Email with both .html and .body set.

    Raises
    ------
    FileNotFoundError
        If either sibling is missing. Deliberately strict:
        silently falling back to HTML-only would let
        future authors forget the .txt version and only
        discover it when a corporate gateway mangles the
        message.
    RuntimeError
        If Jinja rendering fails (syntax error, missing
        variable, etc.).
    """
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound

    template_dir = current_app.config["MAIL_TEMPLATE_DIR"]
    autoescape = bool(current_app.config.get("MAIL_TEMPLATE_AUTOESCAPE", True))

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=autoescape,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    try:
        html_source = env.get_template(f"{template_name}.html")
        text_source = env.get_template(f"{template_name}.txt")
    except TemplateNotFound as exc:
        raise FileNotFoundError(
            f"Email template {template_name!r} is incomplete: "
            f"{exc.name} not found under {template_dir}. "
            f"Both .html and .txt siblings are required."
        ) from exc

    try:
        html_body = html_source.render(**context)
        text_body = text_source.render(**context)
    except Exception as exc:        # noqa: BLE001 — Jinja errors are opaque
        raise RuntimeError(
            f"Failed to render email template {template_name!r}: {exc}"
        ) from exc

    return Email(
        to=to,
        subject=subject,
        body=text_body,
        html=html_body,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
    )
