#!/usr/bin/env python3
"""Safely audit/copy Himma's public PostgreSQL schema from the legacy DB to Railway.

This utility is intentionally conservative:
- never mutates the source database;
- never prints credentials;
- audit mode is read-only;
- migrate mode initializes the target with Alembic, requires the target to be empty
  (apart from alembic_version), copies rows table-by-table, resets sequences, and
  verifies source/target row counts before reporting success.

Environment:
  SOURCE_DATABASE_URL  legacy/source PostgreSQL URL
  TARGET_DATABASE_URL  Railway PostgreSQL URL
  MIGRATION_MODE        audit | migrate   (default: audit)
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Sequence, Tuple

import psycopg2
from psycopg2 import sql

MODE = os.getenv("MIGRATION_MODE", "audit").strip().lower()
SOURCE_URL = os.getenv("SOURCE_DATABASE_URL", "").strip()
TARGET_URL = os.getenv("TARGET_DATABASE_URL", "").strip()

if MODE not in {"audit", "migrate"}:
    raise SystemExit("MIGRATION_MODE must be 'audit' or 'migrate'")
if not SOURCE_URL or not TARGET_URL:
    raise SystemExit("SOURCE_DATABASE_URL and TARGET_DATABASE_URL are required")


def connect(url: str):
    return psycopg2.connect(url, connect_timeout=15)


def public_tables(conn) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        return [row[0] for row in cur.fetchall()]


def table_count(conn, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT count(*)::bigint FROM public.{}").format(sql.Identifier(table))
        )
        return int(cur.fetchone()[0])


def table_counts(conn, tables: Iterable[str]) -> Dict[str, int]:
    return {table: table_count(conn, table) for table in tables}


def print_summary(label: str, counts: Dict[str, int]) -> None:
    total = sum(counts.values())
    print(f"{label}_TABLES={len(counts)}")
    print(f"{label}_ROWS={total}")
    for table in sorted(counts):
        print(f"{label}_COUNT {table}={counts[table]}")


def same_database(source_conn, target_conn) -> bool:
    s = source_conn.get_dsn_parameters()
    t = target_conn.get_dsn_parameters()
    return (s.get("host"), s.get("port"), s.get("dbname")) == (
        t.get("host"),
        t.get("port"),
        t.get("dbname"),
    )


def run_target_migrations() -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = TARGET_URL
    print("TARGET_ALEMBIC_UPGRADE_BEGIN")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd="/app/services/api",
        env=env,
        check=True,
    )
    print("TARGET_ALEMBIC_UPGRADE_OK")


def copyable_columns(conn, table: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND is_generated = 'NEVER'
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def fk_edges(conn, tables: Sequence[str]) -> List[Tuple[str, str]]:
    allowed = set(tables)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT child.relname AS child_table, parent.relname AS parent_table
            FROM pg_constraint c
            JOIN pg_class child ON child.oid = c.conrelid
            JOIN pg_namespace child_ns ON child_ns.oid = child.relnamespace
            JOIN pg_class parent ON parent.oid = c.confrelid
            JOIN pg_namespace parent_ns ON parent_ns.oid = parent.relnamespace
            WHERE c.contype = 'f'
              AND child_ns.nspname = 'public'
              AND parent_ns.nspname = 'public'
            """
        )
        edges = []
        for child, parent in cur.fetchall():
            if child in allowed and parent in allowed and child != parent:
                edges.append((child, parent))
        return edges


def topological_table_order(conn, tables: Sequence[str]) -> List[str]:
    tables = list(tables)
    deps = defaultdict(set)
    children = defaultdict(set)
    indegree = {t: 0 for t in tables}
    for child, parent in fk_edges(conn, tables):
        if parent not in deps[child]:
            deps[child].add(parent)
            children[parent].add(child)
            indegree[child] += 1

    queue = deque(sorted(t for t, degree in indegree.items() if degree == 0))
    order: List[str] = []
    while queue:
        parent = queue.popleft()
        order.append(parent)
        for child in sorted(children[parent]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    if len(order) != len(tables):
        remaining = sorted(set(tables) - set(order))
        raise RuntimeError(
            "Foreign-key cycle detected and replication-role bypass was unavailable: "
            + ", ".join(remaining)
        )
    return order


def try_disable_triggers(target_conn) -> bool:
    try:
        with target_conn.cursor() as cur:
            cur.execute("SET session_replication_role = replica")
        return True
    except psycopg2.Error:
        target_conn.rollback()
        return False


def enable_triggers(target_conn) -> None:
    with target_conn.cursor() as cur:
        cur.execute("SET session_replication_role = origin")


def copy_table(source_conn, target_conn, table: str) -> int:
    source_cols = copyable_columns(source_conn, table)
    target_cols = copyable_columns(target_conn, table)
    if source_cols != target_cols:
        raise RuntimeError(
            f"Column mismatch for {table}: source={source_cols!r}, target={target_cols!r}"
        )
    if not source_cols:
        return 0

    buffer = io.StringIO()
    columns_sql = sql.SQL(", ").join(sql.Identifier(c) for c in source_cols)
    source_copy = sql.SQL(
        "COPY (SELECT {} FROM public.{}) TO STDOUT WITH (FORMAT CSV, NULL '\\N')"
    ).format(columns_sql, sql.Identifier(table))
    target_copy = sql.SQL(
        "COPY public.{} ({}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
    ).format(sql.Identifier(table), columns_sql)

    with source_conn.cursor() as src_cur:
        src_cur.copy_expert(source_copy.as_string(source_conn), buffer)
    buffer.seek(0)
    with target_conn.cursor() as tgt_cur:
        tgt_cur.copy_expert(target_copy.as_string(target_conn), buffer)
    return table_count(source_conn, table)


def reset_sequences(target_conn, tables: Sequence[str]) -> None:
    allowed = set(tables)
    with target_conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name, column_name,
                   pg_get_serial_sequence(format('public.%I', table_name), column_name)
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (column_default LIKE 'nextval%%' OR is_identity = 'YES')
            ORDER BY table_name, ordinal_position
            """
        )
        sequence_rows = cur.fetchall()

    for table, column, sequence_name in sequence_rows:
        if table not in allowed or not sequence_name:
            continue
        with target_conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT max({}) FROM public.{}").format(
                    sql.Identifier(column), sql.Identifier(table)
                )
            )
            max_value = cur.fetchone()[0]
            if max_value is None:
                cur.execute("SELECT setval(%s::regclass, 1, false)", (sequence_name,))
            else:
                cur.execute(
                    "SELECT setval(%s::regclass, %s, true)",
                    (sequence_name, int(max_value)),
                )


def main() -> None:
    source = connect(SOURCE_URL)
    target = connect(TARGET_URL)
    try:
        if same_database(source, target):
            raise RuntimeError("Source and target resolve to the same PostgreSQL database")

        source_tables = public_tables(source)
        target_tables = public_tables(target)
        source_counts = table_counts(source, source_tables)
        target_counts = table_counts(target, target_tables)
        print_summary("SOURCE", source_counts)
        print_summary("TARGET", target_counts)

        if MODE == "audit":
            print("DB_AUDIT_OK")
            return

        target.close()
        run_target_migrations()
        target = connect(TARGET_URL)

        target_tables = public_tables(target)
        target_counts = table_counts(target, target_tables)
        nonempty = {
            table: count
            for table, count in target_counts.items()
            if table != "alembic_version" and count > 0
        }
        if nonempty:
            details = ", ".join(f"{k}={v}" for k, v in sorted(nonempty.items()))
            raise RuntimeError(
                "Target is not empty; refusing destructive overwrite. Non-empty tables: "
                + details
            )

        source_copy_tables = [t for t in source_tables if t != "alembic_version"]
        missing_target = sorted(set(source_copy_tables) - set(target_tables))
        if missing_target:
            raise RuntimeError(
                "Target schema is missing source tables after Alembic upgrade: "
                + ", ".join(missing_target)
            )

        triggers_disabled = try_disable_triggers(target)
        if triggers_disabled:
            order = sorted(source_copy_tables)
            print("TARGET_CONSTRAINT_MODE=replica")
        else:
            order = topological_table_order(target, source_copy_tables)
            print("TARGET_CONSTRAINT_MODE=topological")

        print(f"COPY_TABLES={len(order)}")
        for table in order:
            copied = copy_table(source, target, table)
            print(f"COPIED {table}={copied}")

        reset_sequences(target, order)
        if triggers_disabled:
            enable_triggers(target)
        target.commit()

        final_source = table_counts(source, source_copy_tables)
        final_target = table_counts(target, source_copy_tables)
        mismatches = {
            table: (final_source[table], final_target[table])
            for table in source_copy_tables
            if final_source[table] != final_target[table]
        }
        if mismatches:
            raise RuntimeError(f"Row-count verification failed: {mismatches!r}")

        print_summary("FINAL_TARGET", final_target)
        print("DB_MIGRATION_COMPLETE")
    except Exception:
        try:
            target.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            source.close()
        except Exception:
            pass
        try:
            target.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
