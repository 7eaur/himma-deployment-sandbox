#!/usr/bin/env bash
set -euo pipefail

# Railway is the only active relational database/runtime storage backend for
# this sandbox. Deployment preparation is intentionally limited to schema and
# approved runtime-content projection; legacy cross-provider migration hooks
# are not part of normal runtime anymore.
cd /app/services/api

printf '%s\n' '[himma-sandbox] applying Alembic migrations...'
python -m alembic upgrade head

printf '%s\n' '[himma-sandbox] projecting full approved runtime content...'
python seed_all.py

printf '%s\n' '[himma-sandbox] ensuring researcher seed exists...'
python -m db.seed

printf '%s\n' '[himma-sandbox] pre-deploy database preparation complete.'
