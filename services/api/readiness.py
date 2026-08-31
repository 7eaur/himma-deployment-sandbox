"""Operational readiness checks for trial/release environments.

`/health` remains a cheap liveness probe.  This module backs `/ready`, which
verifies the external services the API needs before it should receive traffic.
The public report intentionally exposes only component status, never secrets or
raw dependency exceptions.
"""

from __future__ import annotations

import os

import redis
from sqlalchemy import text

from db.database import engine
from storage import S3_BUCKET_NAME, s3_client


_REQUIRED_CONFIG = (
    "DATABASE_URL",
    "API_SECRET_KEY",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
    "S3_BUCKET_NAME",
    "REDIS_URL",
)


def _config_ready() -> bool:
    return all(bool(os.getenv(name, "").strip()) for name in _REQUIRED_CONFIG)


def _database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _storage_ready() -> bool:
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        return True
    except Exception:
        return False


def _redis_ready() -> bool:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return False
    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=False,
        )
        return bool(client.ping())
    except Exception:
        return False


def readiness_report() -> dict[str, object]:
    """Return a sanitized readiness report suitable for an unauthenticated probe."""

    checks = {
        "config": _config_ready(),
        "database": _database_ready(),
        "storage": _storage_ready(),
        "redis": _redis_ready(),
    }
    ready = all(checks.values())
    return {
        "status": "ready" if ready else "not_ready",
        "service": "himma-api",
        "checks": {name: "ok" if passed else "unavailable" for name, passed in checks.items()},
    }
