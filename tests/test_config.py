"""
Test-only configuration.

Passed to create_app() by the app fixture in conftest.py.
Overrides the production values so tests do not touch the
real database, do not require CSRF tokens, and write any
uploads to a temporary folder.
"""

import tempfile


class TestConfig:
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False

    # Temporary uploads folder — re-created per app instance.
    UPLOAD_FOLDER = tempfile.mkdtemp(prefix="iems-test-uploads-")

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
