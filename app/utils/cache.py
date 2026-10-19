"""
IEMS Redis cache helper.

A thin wrapper around redis-py that:

- Fails open: if Redis is unreachable or unconfigured,
  every operation becomes a no-op. The app always falls
  through to the database. Redis is a performance layer,
  never a dependency.
- Serializes values as JSON so callers cache Python
  objects, not strings.
- Applies a TTL to every write so nothing lives in Redis
  forever.

Keys follow a namespaced convention:

    dashboard:stats
    depts:all
    locs:all
    cats:all
    activity:recent:10

Invalidation is by key deletion (cache_delete) or by
prefix (cache_clear_pattern) after mutating routes.
"""

import json
import logging

from flask import current_app

logger = logging.getLogger(__name__)

_client = None
_client_initialized = False


# =========================================================
# CLIENT
# =========================================================

def _get_client():
    """
    Lazy-initialise the Redis client on first use.

    Returns None when:
    - CACHE_ENABLED is false
    - REDIS_URL is unset
    - redis-py is not installed
    - connection fails
    """
    global _client, _client_initialized

    if _client_initialized:
        return _client

    _client_initialized = True

    if not current_app.config.get("CACHE_ENABLED"):
        return None

    url = current_app.config.get("REDIS_URL")
    if not url:
        return None

    try:
        import redis
        _client = redis.from_url(url, decode_responses=True)

        # Sanity ping
        _client.ping()

        logger.info("Redis connected")
        return _client

    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        _client = None
        return None


# =========================================================
# PUBLIC API
# =========================================================

def cache_get(key):
    """Return the cached value, or None on miss/error."""
    client = _get_client()
    if client is None:
        return None

    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"cache_get failed for {key}: {e}")
        return None


def cache_set(key, value, ttl=None):
    """Store a value with a TTL (default from config)."""
    client = _get_client()
    if client is None:
        return

    if ttl is None:
        ttl = current_app.config.get("CACHE_TTL_SECONDS", 60)

    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"cache_set failed for {key}: {e}")


def cache_delete(*keys):
    """Delete one or more keys."""
    client = _get_client()
    if client is None:
        return

    if not keys:
        return

    try:
        client.delete(*keys)
    except Exception as e:
        logger.warning(f"cache_delete failed: {e}")


def cache_clear_pattern(pattern):
    """Delete every key matching a glob pattern (e.g. 'depts:*')."""
    client = _get_client()
    if client is None:
        return

    try:
        for key in client.scan_iter(match=pattern, count=100):
            client.delete(key)
    except Exception as e:
        logger.warning(f"cache_clear_pattern failed for {pattern}: {e}")


# =========================================================
# LOOKUP FETCHERS
# =========================================================
#
# Each fetcher caches a plain list of {"id", "name"} dicts.
# Invalidated by invalidate_* below.
#
# TTL is 5 minutes — lookups change rarely, and writes
# invalidate them explicitly, so the TTL is a safety net.

LOOKUP_TTL = 300


def get_cached_departments():
    """Return [{"id", "name"}, ...] for departments."""
    from app.models import Department

    cached = cache_get("depts:all")
    if cached is not None:
        return cached

    rows = Department.query.order_by(Department.name.asc()).all()
    data = [{"id": d.id, "name": d.name} for d in rows]
    cache_set("depts:all", data, ttl=LOOKUP_TTL)
    return data


def get_cached_locations():
    """Return [{"id", "name"}, ...] for locations."""
    from app.models import Location

    cached = cache_get("locs:all")
    if cached is not None:
        return cached

    rows = Location.query.order_by(Location.name.asc()).all()
    data = [{"id": l.id, "name": l.name} for l in rows]
    cache_set("locs:all", data, ttl=LOOKUP_TTL)
    return data


def get_cached_categories():
    """Return [{"id", "name"}, ...] for categories."""
    from app.models import Category

    cached = cache_get("cats:all")
    if cached is not None:
        return cached

    rows = Category.query.order_by(Category.name.asc()).all()
    data = [{"id": c.id, "name": c.name} for c in rows]
    cache_set("cats:all", data, ttl=LOOKUP_TTL)
    return data


# =========================================================
# LOOKUP INVALIDATORS
# =========================================================

def invalidate_departments():
    cache_delete("depts:all")


def invalidate_locations():
    cache_delete("locs:all")


def invalidate_categories():
    cache_delete("cats:all")