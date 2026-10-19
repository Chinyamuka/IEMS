"""
IEMS Configuration

This file contains configuration settings for the application.
"""

import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Base directory of the project

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY","development-secret-key",)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app","static", "uploads") # Directory to store uploaded files
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif","webp"} # Image file extensions allowed
    # -----------------------------------------------------
    # CACHE (Redis / Upstash)
    # -----------------------------------------------------
    #
    # CACHE_ENABLED must be true for any caching to
    # happen. When false, cache_* functions are no-ops
    # and the app falls through to the database.

    REDIS_URL = os.getenv("REDIS_URL")
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "false").lower() == "true"
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))

    # =========================================================
    # MAIL
    # =========================================================
    #
    # MAIL_ENABLED is the master kill-switch. When false,
    # sends are short-circuited twice: Flask-Mail's own
    # MAIL_SUPPRESS_SEND, and an early return in
    # app/email/service.py (which logs which message was
    # skipped — useful when debugging).
    #
    # MAIL_USERNAME for the Mailtrap sandbox is the hex
    # string from the SMTP settings page, NOT an email
    # address. Flask-Mail does not care.

    MAIL_ENABLED = os.getenv("MAIL_ENABLED", default=False)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "2525"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD") or None
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", default=True)
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", default=False)
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@iems.local")
    MAIL_TIMEOUT = int(os.getenv("MAIL_TIMEOUT", "10"))

    # Keep locked to MAIL_ENABLED. Do not set independently.
    MAIL_SUPPRESS_SEND = not MAIL_ENABLED
