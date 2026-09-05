#!/usr/bin/env bash
set -euo pipefail

cd /app/services/api

printf '%s\n' '[himma-sandbox] applying Alembic migrations...'
python -m alembic upgrade head

printf '%s\n' '[himma-sandbox] projecting full approved runtime content...'
python seed_all.py

printf '%s\n' '[himma-sandbox] ensuring researcher seed exists...'
python -m db.seed

printf '%s\n' '[himma-sandbox] pre-deploy database preparation complete.'
