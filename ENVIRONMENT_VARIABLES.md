# Himma Sandbox Environment Variables

No secret values belong in this file.

## Railway FastAPI
Required runtime names:
- `DATABASE_URL` — Railway PostgreSQL connection reference.
- `API_SECRET_KEY` — private backend signing secret; minimum 32 characters in protected environments.
- `REDIS_URL` — Railway Redis connection reference.
- `S3_ENDPOINT` — Railway Storage S3 endpoint reference.
- `S3_ACCESS_KEY` — server-side Railway Storage access-key reference.
- `S3_SECRET_KEY` — server-side Railway Storage secret-key reference.
- `S3_BUCKET_NAME` — Railway Storage API bucket-name reference.
- `ENV` — runtime environment marker.
- `PORT` — Railway application port.
- `CORS_ORIGINS` — comma-separated trusted frontend origins.

`HIMMA_TEMP_AUDIO_SKIP` is no longer a supported runtime feature. The legacy deployment variable may remain present as an empty value only until platform cleanup; application code does not use an audio bypass.

## Railway reference aliases
During the infrastructure migration the API was wired through non-secret aliases so the final runtime values can follow Railway-managed resources:
- `TARGET_DATABASE_URL` -> Railway `Postgres.DATABASE_URL`.
- `TARGET_S3_ENDPOINT`, `TARGET_S3_ACCESS_KEY`, `TARGET_S3_SECRET_KEY`, `TARGET_S3_BUCKET_NAME` -> Railway Storage credentials supplied to the API.

The production-facing `DATABASE_URL` and `S3_*` variables resolve through those target references. Legacy source variables are not required during normal runtime.

## One-time migration controls
These variables must be empty/disabled during normal deployments:
- `MIGRATION_MODE` — `audit` or `migrate` only for reviewed database migration work.
- `STORAGE_MIGRATION_MODE` — `audit` or `migrate` only for reviewed object-storage migration work.
- `BUCKET_CORS_MODE` — `apply` only when intentionally applying/verifying bucket CORS.
- `DEPLOYMENT_MAINTENANCE_MODE` — `true` only for short migration/diagnostic deployments that must skip the normal content seed.

## Vercel Next.js
- `NEXT_PUBLIC_API_URL` — sandbox API origin. The deployed frontend points to the Railway sandbox API.

## Legacy helper variables
Railpack helper variables may still exist from earlier deployment experiments (`PYTHONPATH`, `RAILPACK_PACKAGES`, `RAILPACK_PYTHON_VERSION`); the active API deployment uses the Dockerfile and does not rely on them.

## Secret-handling rules
- Never commit database passwords, API secret keys, Redis credentials, or S3 credentials.
- Store secrets only in platform-managed environment variables/references.
- Rotate any credential that appears in logs or other unintended output.
- Keep sandbox and future production values isolated.
- Delete/decommission legacy external credentials only after the Railway cutover is accepted and rollback requirements are closed.
