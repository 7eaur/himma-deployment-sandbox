#!/usr/bin/env python3
"""Compare critical Himma table counts after a PostgreSQL restore test."""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text


TABLES = (
    "users",
    "students",
    "skills",
    "content_releases",
    "content_items",
    "content_steps",
    "content_options",
    "content_asset_links",
    "scoring_policies",
    "scoring_rules",
    "assessment_sessions",
    "audit_logs",
)


def _counts(url: str) -> dict[str, int]:
    engine = create_engine(url)
    result: dict[str, int] = {}
    with engine.connect() as connection:
        for table in TABLES:
            result[table] = int(connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one())
    engine.dispose()
    return result


def main() -> int:
    source_url = os.getenv("DATABASE_URL", "").strip()
    restore_url = os.getenv("RESTORE_DATABASE_URL", "").strip()
    if not source_url or not restore_url:
        print("DATABASE_URL and RESTORE_DATABASE_URL are required", file=sys.stderr)
        return 2

    source = _counts(source_url)
    restored = _counts(restore_url)
    mismatches = {
        table: {"source": source[table], "restored": restored[table]}
        for table in TABLES
        if source[table] != restored[table]
    }
    if mismatches:
        print(f"Backup/restore mismatch: {mismatches}", file=sys.stderr)
        return 1

    print("PostgreSQL restore verification passed.")
    for table in TABLES:
        print(f"  {table}: {source[table]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
