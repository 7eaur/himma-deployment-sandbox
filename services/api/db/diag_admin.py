"""Temporary safe sandbox auth diagnostics. Never returns credentials or hashes."""

import os
import bcrypt

from db.database import SessionLocal
from db.models import User


def _matches(password: str, user: User | None) -> bool:
    if not user or not password:
        return False
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            user.password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def collect_admin_diag() -> dict[str, object]:
    db = SessionLocal()
    try:
        username_raw = os.getenv("ADMIN_USERNAME", "")
        password_raw = os.getenv("ADMIN_PASSWORD", "")
        username = username_raw.strip()
        password = password_raw.strip()
        env_name = os.getenv("ENV", "").strip().lower()

        target = db.query(User).filter(User.username == username).first() if username else None
        literal_admin = db.query(User).filter(User.username == "admin").first()

        wrapped_in_quotes = bool(
            len(password_raw) >= 2
            and password_raw[0] in {"'", '"'}
            and password_raw[-1] == password_raw[0]
        )

        return {
            "env": env_name,
            "env_is_sandbox": env_name == "sandbox",
            "username_present": bool(username_raw),
            "username_is_admin": username == "admin",
            "username_had_outer_whitespace": username_raw != username,
            "password_present": bool(password_raw),
            "password_raw_length": len(password_raw),
            "password_trimmed_length": len(password),
            "password_had_outer_whitespace": password_raw != password,
            "password_wrapped_in_quotes": wrapped_in_quotes,
            "target_found": bool(target),
            "target_active": getattr(target, "is_active", None),
            "target_role": getattr(target, "role", None),
            "target_matches_env_password": _matches(password, target),
            "literal_admin_found": bool(literal_admin),
            "literal_admin_active": getattr(literal_admin, "is_active", None),
            "literal_admin_role": getattr(literal_admin, "role", None),
            "literal_admin_matches_env_password": _matches(password, literal_admin),
            "user_count": db.query(User).count(),
        }
    finally:
        db.close()
