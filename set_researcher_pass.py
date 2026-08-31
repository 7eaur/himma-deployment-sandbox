import os
from urllib.parse import urlparse

import bcrypt
import psycopg2

username = os.environ.get("ADMIN_USERNAME", "admin")
password = os.environ.get("ADMIN_PASSWORD")
database_url = os.environ.get("DATABASE_URL")
if not password or not database_url:
    raise RuntimeError("ADMIN_PASSWORD and DATABASE_URL are required")

hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
p = urlparse(database_url)
conn = psycopg2.connect(
    host=p.hostname,
    port=p.port or 5432,
    dbname=p.path.lstrip("/"),
    user=p.username,
    password=p.password,
)
cur = conn.cursor()

cur.execute(
    "UPDATE users SET password_hash=%s, is_active=true WHERE username=%s",
    (hashed, username),
)
if cur.rowcount != 1:
    conn.rollback()
    raise RuntimeError("Researcher account was not found")

conn.commit()
conn.close()
print(f"Updated researcher account: {username}")
