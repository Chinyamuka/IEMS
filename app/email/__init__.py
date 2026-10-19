# app/email/__init__.py
"""
Public surface of the IEMS email feature.

Callers should use:

    from app.email import Email, send, send_many, init_mail

Never import from app.email.service or app.email.message
directly. Internal module layout is free to change; this
package surface is the contract.
"""
from app.email.message import Email
from app.email.service import send, send_many
from app.email.bootstrap import init_mail

__all__ = ["Email", "send", "send_many", "init_mail"]
