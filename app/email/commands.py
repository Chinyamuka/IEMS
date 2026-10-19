# app/email/commands.py
"""
Flask-CLI commands for the email feature.

Currently a single command — mail-test — used to prove
the SMTP pipeline end-to-end before any real feature
sends mail. Once N2 lands real senders, this stays as a
smoke test: something to run against Mailtrap in CI or
after rotating credentials, without spinning up the web
UI.
"""
import click
from flask.cli import with_appcontext

from app.email.message import Email
from app.email.service import send


def register_mail_commands(app) -> None:
    """Register mail-related CLI commands on the Flask app."""

    @app.cli.command("mail-test")
    @click.argument("to")
    @with_appcontext
    def mail_test(to: str) -> None:
        """Send a test email through the configured SMTP server."""
        ok = send(
            Email(
                to=(to,),
                subject="IEMS mail test",
                body=(
                    "If you see this in Mailtrap, the IEMS mail "
                    "pipeline is working."
                ),
                html=(
                    "<p>If you see this in <strong>Mailtrap</strong>, "
                    "the IEMS mail pipeline is working.</p>"
                ),
            )
        )
        click.echo("sent" if ok else "FAILED — see logs")
