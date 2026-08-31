"""Sandbox-only runtime bootstrap for the supervisor account.

This module never contains or logs credentials. It only reads them from the
service environment and is a no-op outside ENV=sandbox.
"""

import os
import bcrypt

from db.database import SessionLocal
from db.models import User


def ensure_sandbox_admin() -> None:
    if os.getenv("ENV", "").strip().lower() != "sandbox":
        return

    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = (os.getenv("ADMIN_PASSWORD") or "").strip()
    if not username or not password:
        raise RuntimeError("Sandbox admin credentials are not configured")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            user = User(
                username=username,
                password_hash=password_hash,
                role="researcher",
                is_active=True,
            )
            db.add(user)
        else:
            try:
                matches = bcrypt.checkpw(
                    password.encode("utf-8"),
                    user.password_hash.encode("utf-8"),
                )
            except (ValueError, TypeError):
                matches = False
            if not matches:
                user.password_hash = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
            user.role = "researcher"
            user.is_active = True
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
