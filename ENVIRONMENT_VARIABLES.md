# Himma Sandbox Environment Variables

No secret values belong in this file.

## Railway FastAPI
Required names:
- `DATABASE_URL` — Supabase PostgreSQL connection string.
- `API_SECRET_KEY` — private backend signing secret; minimum 32 characters.
- `REDIS_URL` — Railway Redis connection URL.
- `S3_ENDPOINT` — Supabase Storage S3 endpoint.
- `S3_ACCESS_KEY` — server-side S3 access key.
- `S3_SECRET_KEY` — server-side S3 secret key.
- `S3_BUCKET_NAME` — current sandbox value: `himma-audio`.
- `ENV` — current sandbox value: `sandbox`.
- `HIMMA_TEMP_AUDIO_SKIP` — current sandbox value: `true`; must be `false` for trial/production.
- `PORT` — current Railway value: `8000`.
- `CORS_ORIGINS` — comma-separated trusted Vercel origins.

Legacy Railpack helper variables may still exist from earlier deployment experiments (`PYTHONPATH`, `RAILPACK_PACKAGES`, `RAILPACK_PYTHON_VERSION`); the active deployment uses Dockerfile and does not rely on them.

## Vercel Next.js
- `NEXT_PUBLIC_API_URL` — sandbox API origin. On the deployment branch this non-secret value is provided by `apps/web/.env.production` and points to the Railway sandbox API.

## Secret-handling rules
- Never commit database passwords, API secret keys, Redis credentials, or S3 credentials.
- Store secrets in Railway/Supabase/Vercel secret managers.
- Rotate any secret that is accidentally exposed.
- Keep sandbox and future production values isolated.
