"""Operational readiness checks for trial/release environments.

`/health` remains a cheap liveness probe. This module backs `/ready`, which
verifies the external services and the exact approved runtime-content/media
contract the API needs before it should receive traffic. A failed dependency,
stale content projection, or missing approved media keeps readiness closed.
The public report intentionally exposes only component status, never secrets
or raw dependency exceptions.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import redis
from sqlalchemy import text
from sqlalchemy.orm import selectinload

from db.database import SessionLocal, engine
from db.models import ContentItem
from storage import S3_BUCKET_NAME, s3_client


_REQUIRED_CONFIG = (
    "DATABASE_URL",
    "API_SECRET_KEY",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
    "S3_BUCKET_NAME",
    "REDIS_URL",
)
_EXPECTED_TOTAL_ITEMS = 125
_EXPECTED_REINFORCEMENT_ITEMS = 35
_STUDENT_EXPERIENCE_VERSION = "HIMMA-STUDENT-EXPERIENCE-2.0"
_DB_RUNTIME_VERSION = "HIMMA-DB-RUNTIME-1.0"
_PRETEST_VERSION = "HIMMA-PRETEST-2026-09-01"
_LEARNING_VERSION = "HIMMA-LEARNING-2026-09-01-R2"
_POSTTEST_VERSION = "HIMMA-POSTTEST-2026-09-01"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AUDIO_ROOT = _REPO_ROOT / "assets" / "audio" / "HIMMA_AUDIO_V1"
_AUDIO_MANIFEST = _AUDIO_ROOT / "manifest.csv"
_REQUIRED_APPROVED_AUDIO = {
    "LET-01": "مَ",
    "SYL-13": "سَا",
    "WRD-29": "موز",
    "INS-01": "قصة ليان في المزرعة",
    "INS-02": "قصة نادر في الشاطئ",
}


def _config_ready() -> bool:
    return all(bool(os.getenv(name, "").strip()) for name in _REQUIRED_CONFIG)


def _database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _content_ready() -> bool:
    """Fail closed when PostgreSQL contains a stale/incomplete projection."""
    db = SessionLocal()
    try:
        # Eager-load steps in one additional query instead of issuing one remote
        # PostgreSQL query per learning item during every readiness probe.
        items = db.query(ContentItem).options(selectinload(ContentItem.steps)).all()
        if len(items) != _EXPECTED_TOTAL_ITEMS:
            return False
        if sum(item.kind == "reinforcement_activity" for item in items) != _EXPECTED_REINFORCEMENT_ITEMS:
            return False

        for item in items:
            template = item.template_data or {}
            if template.get("student_experience_version") != _STUDENT_EXPERIENCE_VERSION:
                return False
            if (template.get("db_runtime") or {}).get("version") != _DB_RUNTIME_VERSION:
                return False

        pretest = [item for item in items if item.kind == "pretest_question"]
        learning = [item for item in items if item.kind in {"core_activity", "reinforcement_activity"}]
        posttest = [item for item in items if item.kind == "posttest_question"]
        if len(pretest) != 30 or len(learning) != 65 or len(posttest) != 30:
            return False

        for item in pretest:
            template = item.template_data or {}
            if template.get("pretest_experience_version") != _PRETEST_VERSION:
                return False
            if (template.get("pretest_experience") or {}).get("version") != _PRETEST_VERSION:
                return False

        for item in learning:
            template = item.template_data or {}
            if template.get("learning_experience_version") != _LEARNING_VERSION:
                return False
            experience = template.get("learning_experience") or {}
            if experience.get("version") != _LEARNING_VERSION:
                return False
            if len(experience.get("rounds") or []) != len(item.steps):
                return False

        for item in posttest:
            template = item.template_data or {}
            if template.get("posttest_experience_version") != _POSTTEST_VERSION:
                return False
            if (template.get("posttest_experience") or {}).get("version") != _POSTTEST_VERSION:
                return False
        return True
    except Exception:
        return False
    finally:
        db.close()


def _approved_audio_ready() -> bool:
    """Verify the five corrective approved assets and both binary variants.

    This is an operational readiness check, not a student content loader. The
    student runtime remains DB-driven; this probe only proves that the static
    approved media contract shipped with the release is physically deployable.
    """
    try:
        with _AUDIO_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = {
                str(row.get("id") or "").strip(): row
                for row in csv.DictReader(handle)
                if str(row.get("status") or "").strip() == "approved"
            }
        for asset_id, semantic_text in _REQUIRED_APPROVED_AUDIO.items():
            row = rows.get(asset_id)
            if row is None or str(row.get("text_ar") or "").strip() != semantic_text:
                return False
            wav_name = str(row.get("filename_wav") or "").strip()
            mp3_name = str(row.get("filename_mp3") or "").strip()
            if wav_name != f"{asset_id}.wav" or mp3_name != f"{asset_id}.mp3":
                return False
            if not (_AUDIO_ROOT / "wav_master" / wav_name).is_file():
                return False
            if not (_AUDIO_ROOT / "web_mp3" / mp3_name).is_file():
                return False
        return "SYL-15" not in rows
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
        "content": _content_ready(),
        "approved_audio": _approved_audio_ready(),
        "storage": _storage_ready(),
        "redis": _redis_ready(),
    }
    ready = all(checks.values())
    return {
        "status": "ready" if ready else "not_ready",
        "service": "himma-api",
        "checks": {name: "ok" if passed else "unavailable" for name, passed in checks.items()},
    }
