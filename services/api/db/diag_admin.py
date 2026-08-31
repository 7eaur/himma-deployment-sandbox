"""Safe sandbox authentication diagnostics. Never prints credentials or hashes."""

import os
import sys
import bcrypt

from db.database import SessionLocal
from db.models import User


def main() -> None:
    db = SessionLocal()
    try:
        username_raw = os.getenv("ADMIN_USERNAME", "")
        password_raw = os.getenv("ADMIN_PASSWORD", "")
        username = username_raw.strip()
        password = password_raw.strip()
        env_name = os.getenv("ENV", "").strip().lower()

        target = db.query(User).filter(User.username == username).first()
        literal_admin = db.query(User).filter(User.username == "admin").first()

        def check(user):
            return bool(
                user
                and password
                and bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
            )

        wrapped_in_quotes = bool(
            len(password_raw) >= 2
            and password_raw[0] in {"'", '"'}
            and password_raw[-1] == password_raw[0]
        )

        print(
            "ADMIN_DIAG "
            f"env={env_name!r} "
            f"username_raw={username_raw!r} "
            f"username_normalized={username!r} "
            f"pwd_raw_len={len(password_raw)} "
            f"pwd_trimmed_len={len(password)} "
            f"pwd_had_outer_whitespace={password_raw != password} "
            f"pwd_wrapped_in_quotes={wrapped_in_quotes} "
            f"target_found={bool(target)} "
            f"target_active={getattr(target, 'is_active', None)!r} "
            f"target_role={getattr(target, 'role', None)!r} "
            f"target_match={check(target)} "
            f"literal_admin_found={bool(literal_admin)} "
            f"literal_admin_active={getattr(literal_admin, 'is_active', None)!r} "
            f"literal_admin_role={getattr(literal_admin, 'role', None)!r} "
            f"literal_admin_match={check(literal_admin)}",
            file=sys.stderr,
            flush=True,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
