#!/usr/bin/env bash
set -euo pipefail

: "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL is required}"
backup_path="${1:?Usage: restore_postgres.sh /path/to/himma-postgres.dump}"

if ! command -v pg_restore >/dev/null 2>&1; then
  echo "pg_restore is required for PostgreSQL restores" >&2
  exit 2
fi

if [[ ! -s "$backup_path" ]]; then
  echo "Backup file does not exist or is empty: $backup_path" >&2
  exit 3
fi

if [[ -f "${backup_path}.sha256" ]]; then
  sha256sum --check "${backup_path}.sha256"
fi

# Restore intentionally targets a caller-provided database. The script never
# drops or creates a database, which keeps destructive lifecycle decisions out
# of the reusable restore primitive.
pg_restore \
  --dbname="$RESTORE_DATABASE_URL" \
  --no-owner \
  --no-privileges \
  --exit-on-error \
  "$backup_path"

echo "PostgreSQL restore completed into the configured restore database."
