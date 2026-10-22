"""
Test-only configuration.

Passed to create_app() by the app fixture in conftest.py.

Inherits from the production Config so that every setting
not explicitly overridden here is identical to production.

Cache is disabled at the config level so that stale
lookup entries cannot leak between tests. If a specific
test needs the cache on (test_cache_dashboard.py), it can
opt in via a fixture that sets app.config["CACHE_ENABLED"]
= True and rebuilds the client.
"""

import tempfile

from sqlalchemy.pool import StaticPool

from config import Config


class TestConfig(Config):
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False

    # SQLite :memory: databases are per-connection. StaticPool
    # pins one connection for the lifetime of the engine, so
    # every checkout returns the same underlying SQLite
    # connection and every test sees one database.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }

    # Cache is off by default in tests. The conftest app
    # fixture also clears the four known lookup keys as a
    # second layer of defence — belt and braces.
    CACHE_ENABLED = False

    # Temporary uploads folder — re-created per app instance.
    UPLOAD_FOLDER = tempfile.mkdtemp(prefix="iems-test-uploads-")
