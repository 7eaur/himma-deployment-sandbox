"""Idempotent seed script — relies on Alembic migrations for schema."""

import os
import sys
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.database import SessionLocal
from db.models import User, Student


def seed():
    """Seed the initial researcher and optional synthetic demo students.

    IMPORTANT: Tables must already exist via `alembic upgrade head`.
    This script does NOT call Base.metadata.create_all().
    """
    db = SessionLocal()

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError(
            "ADMIN_PASSWORD environment variable is required for seeding. "
            "Do not commit a default password."
        )
    if not db.query(User).filter(User.username == admin_username).first():
        hashed = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db.add(User(username=admin_username, password_hash=hashed, role="researcher"))

    if os.getenv("SEED_DEMO_STUDENTS", "false").lower() == "true":
        for i in range(1, 16):
            code = f"TST-{i:04d}"
            if not db.query(Student).filter(Student.access_code == code).first():
                db.add(Student(access_code=code, name=f"طالب تجريبي {i}"))

    db.commit()
    db.close()
    print("Seeding completed successfully.")


if __name__ == "__main__":
    seed()
