#!/usr/bin/env bash
set -euo pipefail

# Optional one-time migration/audit hooks used while moving the sandbox from
# external Supabase services to Railway-managed resources.  Audit modes are
# read-only.  Migration helpers never delete source data and verify the target
# before reporting success.  Leave both mode variables empty during normal
# deployments.
if [[ -n "${MIGRATION_MODE:-}" ]]; then
  case "${MIGRATION_MODE}" in
    audit|migrate)
      printf '%s\n' "[himma-sandbox] database ${MIGRATION_MODE} step..."
      python /app/deploy/migrate_supabase_to_railway.py
      ;;
    *)
      printf '%s\n' "[himma-sandbox] unsupported MIGRATION_MODE=${MIGRATION_MODE}" >&2
      exit 2
      ;;
  esac
fi

if [[ -n "${STORAGE_MIGRATION_MODE:-}" ]]; then
  case "${STORAGE_MIGRATION_MODE}" in
    audit|migrate)
      printf '%s\n' "[himma-sandbox] storage ${STORAGE_MIGRATION_MODE} step..."
      python /app/deploy/migrate_storage_to_railway.py
      ;;
    *)
      printf '%s\n' "[himma-sandbox] unsupported STORAGE_MIGRATION_MODE=${STORAGE_MIGRATION_MODE}" >&2
      exit 2
      ;;
  esac
fi

# Sandbox deployment preparation: keep schema and approved runtime projection aligned.
cd /app/services/api

printf '%s\n' '[himma-sandbox] applying Alembic migrations...'
python -m alembic upgrade head

printf '%s\n' '[himma-sandbox] projecting full approved runtime content...'
python seed_all.py

printf '%s\n' '[himma-sandbox] ensuring researcher seed exists...'
python -m db.seed

printf '%s\n' '[himma-sandbox] pre-deploy database preparation complete.'
