# app/email/bootstrap.py
"""
Bind mail configuration to the Flask app.

Pure wiring: config values are read from app.config. This
module only calls mail.init_app() and emits startup
diagnostics so misconfiguration is visible in the console
the moment the app boots, not hours later when someone
triggers a send.
"""
from __future__ import annotations

import logging

from flask import Flask

from app.extensions import mail

log = logging.getLogger(__name__)


def init_mail(app: Flask) -> None:
    """Initialize Flask-Mail against the given app."""
    enabled  = bool(app.config.get("MAIL_ENABLED"))
    server   = app.config.get("MAIL_SERVER")
    username = app.config.get("MAIL_USERNAME")
    password = app.config.get("MAIL_PASSWORD")

    # Keep the two kill-switches locked together so
    # MAIL_ENABLED=false always propagates to Flask-Mail,
    # regardless of what config produced.
    app.config["MAIL_SUPPRESS_SEND"] = not enabled

    if not enabled:
        log.warning(
            "Mail DISABLED (MAIL_ENABLED=false) — sends will be suppressed."
        )
    elif not (server and username and password):
        # Enabled but incomplete: every send will fail.
        # Surface it now, at startup, not on first request.
        log.error(
            "Mail ENABLED but server/username/password incomplete "
            "— sends will fail."
        )

    mail.init_app(app)
