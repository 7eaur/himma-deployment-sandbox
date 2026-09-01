"""Sandbox-only runtime bootstrap.

Keeps the supervisor account synchronized and seeds the approved runtime catalog
when the sandbox database is incomplete or any student-facing content projection
is stale. A PostgreSQL advisory lock prevents parallel rollout containers from
running the catalog seed concurrently. No credentials are stored or logged here.
"""

import os

import bcrypt
from sqlalchemy import text

from db.database import SessionLocal
from db.models import ContentItem, Skill, User
from seed_all import _base_stable_keys, run_seed_all

_SANDBOX_SEED_LOCK_KEY = 481_663_202_608_31
_PRETEST_VERSION = "HIMMA-PRETEST-2026-09-01"
_LEARNING_VERSION = "HIMMA-LEARNING-2026-09-01"
_POSTTEST_VERSION = "HIMMA-POSTTEST-2026-09-01"


def _is_sandbox() -> bool:
    return os.getenv("ENV", "").strip().lower() == "sandbox"


def _catalog_is_complete(db) -> bool:
    base_keys = _base_stable_keys()
    all_items = db.query(ContentItem).all()
    total_items = len(all_items)
    base_items = db.query(ContentItem).filter(ContentItem.stable_key.in_(base_keys)).count()
    reinforcement_items = db.query(ContentItem).filter(ContentItem.kind == "reinforcement_activity").count()
    skills = db.query(Skill).count()
    v2_items = sum(1 for item in all_items if (item.template_data or {}).get("student_experience_version") == "HIMMA-STUDENT-EXPERIENCE-2.0")
    pretest_items = sum(1 for item in all_items if item.kind == "pretest_question" and (item.template_data or {}).get("pretest_experience_version") == _PRETEST_VERSION)
    learning_items = sum(1 for item in all_items if item.kind in {"core_activity", "reinforcement_activity"} and (item.template_data or {}).get("learning_experience_version") == _LEARNING_VERSION)
    posttest_items = sum(1 for item in all_items if item.kind == "posttest_question" and (item.template_data or {}).get("posttest_experience_version") == _POSTTEST_VERSION)
    return (
        total_items == 125
        and base_items == 105
        and reinforcement_items == 35
        and skills >= 44
        and v2_items == 125
        and pretest_items == 30
        and learning_items == 65
        and posttest_items == 30
    )


def ensure_sandbox_admin() -> None:
    if not _is_sandbox():
        return
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = (os.getenv("ADMIN_PASSWORD") or "").strip()
    if not username or not password:
        raise RuntimeError("Sandbox admin credentials are not configured")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user = User(username=username, password_hash=password_hash, role="researcher", is_active=True)
            db.add(user)
        else:
            try:
                matches = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
            except (ValueError, TypeError):
                matches = False
            if not matches:
                user.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user.role = "researcher"
            user.is_active = True
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ensure_sandbox_runtime() -> None:
    if not _is_sandbox():
        return
    lock_db = SessionLocal()
    lock_acquired = False
    try:
        is_postgres = lock_db.get_bind().dialect.name == "postgresql"
        if is_postgres:
            lock_db.execute(text("SELECT pg_advisory_lock(:lock_key)"), {"lock_key": _SANDBOX_SEED_LOCK_KEY})
            lock_acquired = True
        if not _catalog_is_complete(lock_db):
            run_seed_all()
            lock_db.expire_all()
            if not _catalog_is_complete(lock_db):
                raise RuntimeError("Sandbox runtime catalog is still incomplete after approved seed")
        ensure_sandbox_admin()
    finally:
        if lock_acquired:
            try:
                lock_db.execute(text("SELECT pg_advisory_unlock(:lock_key)"), {"lock_key": _SANDBOX_SEED_LOCK_KEY})
            except Exception:
                pass
        lock_db.close()
