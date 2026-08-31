# Himma Sandbox Deployment Status

Last updated: 2026-08-31

## Scope
This is an isolated deployment/integration sandbox. It is not production approval and does not authorize merging into source branches.

## Current services
- GitHub source: `deployment/platform-sandbox`.
- Railway project: `himma-sandbox`.
- Railway API: `himma-sandbox-api`.
- Railway Redis: `himma-sandbox-redis`.
- Supabase: sandbox PostgreSQL + S3-compatible Storage.
- Vercel project: `himma`, sandbox branch deployment from `deployment/platform-sandbox`.

## Verified
- Railway source branch fixed to `deployment/platform-sandbox`.
- Railway deployment used sandbox commit `fa23a22cc84e91dbdd9ad0d1d031aa9f905c891f` and `deploy/railway-api.Dockerfile`.
- Docker image build succeeded.
- Alembic reached the current head on Supabase PostgreSQL.
- Railway pre-deploy command exits successfully; `seed_all.py` is part of that gate and fails closed if approved content counts are wrong.
- Uvicorn starts on `0.0.0.0:8000`.
- Railway `/ready` healthcheck succeeded.
- Redis deployment is healthy.
- Backend CORS includes the Himma Vercel origins.
- Vercel successfully built Next.js 16.3.0 from the sandbox branch, including student/admin/API routes.
- `apps/web/.env.production` points the sandbox frontend to the Railway sandbox API.

## Not yet production-ready
- Temporary audio bypass is deliberately enabled for sandbox (`HIMMA_TEMP_AUDIO_SKIP=true`).
- No real student data should be introduced without explicit approval.
- A full authenticated student/admin journey against the hosted sandbox still requires valid sandbox user records/codes; content seeding does not itself create user accounts.
- Vercel preview protection may require an authenticated/share session when testing the branch alias externally.

## Rollback
Use previous successful Railway/Vercel sandbox deployments. Do not force-push, hard-reset, or modify source branches. Database rollback requires a reviewed migration-specific plan.
