"""
Test-only configuration.

Passed to create_app() by the app fixture in conftest.py.

Inherits from the production Config so that every setting
not explicitly overridden here (MAIL_*, CACHE_*, SECRET_KEY
fallback, ALLOWED_IMAGE_EXTENSIONS, ...) is identical to
production. This means a new config key added to Config
automatically becomes available in tests — no risk of a
test passing in isolation but failing against the real
config shape.

Overrides applied here are limited to changes that are
strictly about *how tests run*, not *what the app does*:

- SQLALCHEMY_DATABASE_URI  → in-memory SQLite, not Postgres
- SQLALCHEMY_TRACK_MODIFICATIONS → silenced, faster teardown
- TESTING                  → Flask propagates exceptions
- WTF_CSRF_ENABLED         → disabled so POST forms work
- UPLOAD_FOLDER            → temp directory per test session
- SECRET_KEY               → fixed, known value
"""

import tempfile

from config import Config


class TestConfig(Config):
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False

    # Temporary uploads folder — re-created per app instance.
    UPLOAD_FOLDER = tempfile.mkdtemp(prefix="iems-test-uploads-")
