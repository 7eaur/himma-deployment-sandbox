#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"

output_path="${1:-./artifacts/backups/himma-postgres.dump}"
mkdir -p "$(dirname "$output_path")"
umask 077

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump is required for PostgreSQL backups" >&2
  exit 2
fi

pg_dump \
  --dbname="$DATABASE_URL" \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="$output_path"

if [[ ! -s "$output_path" ]]; then
  echo "Backup file is empty" >&2
  exit 3
fi

sha256sum "$output_path" > "${output_path}.sha256"
echo "PostgreSQL backup created: $output_path"
echo "Checksum: ${output_path}.sha256"
