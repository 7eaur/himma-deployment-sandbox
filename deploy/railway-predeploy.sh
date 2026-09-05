#!/usr/bin/env bash
set -euo pipefail

# Maintenance mode is used only while migrating the sandbox infrastructure.
# It deliberately skips the normal schema/content seed so a diagnostic or copy
# run can start quickly while the currently healthy deployment remains live.
if [[ "${DEPLOYMENT_MAINTENANCE_MODE:-false}" == "true" ]]; then
  printf '%s\n' '[himma-sandbox] maintenance pre-deploy: normal seed skipped.'
  exit 0
fi

# Optional one-time migration/audit hooks used while moving the sandbox from
# external Supabase services to Railway-managed resources. Audit modes are
# read-only. Migration helpers never delete source data and verify the target
# before reporting success. Leave both mode variables empty during normal
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
