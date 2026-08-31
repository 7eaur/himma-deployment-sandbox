import os

import psycopg2
from psycopg2 import sql


def create():
    admin_dsn = os.environ.get("PG_ADMIN_DSN")
    db_user = os.environ.get("DB_USER", "himma")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME", "himma_db")
    if not admin_dsn or not db_password:
        raise RuntimeError("PG_ADMIN_DSN and DB_PASSWORD are required")

    try:
        conn = psycopg2.connect(admin_dsn)
        conn.autocommit = True
        cur = conn.cursor()

        try:
            cur.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)),
                (db_password,),
            )
            print(f"Created database role {db_user}")
        except psycopg2.errors.DuplicateObject:
            cur.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)),
                (db_password,),
            )
            print(f"Updated database role {db_user}")

        try:
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(db_name),
                    sql.Identifier(db_user),
                )
            )
            print(f"Created database {db_name}")
        except psycopg2.errors.DuplicateDatabase:
            print(f"Database {db_name} already exists")

        cur.close()
        conn.close()
    except Exception as exc:
        raise RuntimeError("Database bootstrap failed") from exc


if __name__ == "__main__":
    create()
