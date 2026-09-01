# Himma Sandbox Deployment Status

Last updated: 2026-09-01

## Scope
This is an isolated deployment/integration sandbox. It is not production approval and does not authorize merging into source branches.

## Continuous audit register
The authoritative living register for discovered defects, risks, verification gaps, resolutions, and release blockers is:

`docs/audit/HIMMA_CONTINUOUS_AUDIT_REGISTER_AR.md`

All new audit findings and all later fix/reverification states should be recorded there instead of relying on chat history alone.

## Current services
- GitHub source: `7eaur/himma-deployment-sandbox` branch `main`.
- Railway project: `himma-sandbox`.
- Railway API: `himma-sandbox-api`.
- Railway Redis: `himma-sandbox-redis`.
- Supabase: sandbox PostgreSQL + S3-compatible Storage.
- Vercel project: `himma-deployment-sandbox`, Production deployment from `main`, Root Directory `apps/web`.

## Verified
- Sandbox snapshot was migrated from the approved deployment branch into the isolated repository without changing application logic.
- Railway source is now `7eaur/himma-deployment-sandbox:main`.
- Railway deployment uses `deploy/railway-api.Dockerfile`.
- Docker image build succeeded.
- Alembic reached the current head on Supabase PostgreSQL.
- Railway pre-deploy runs `alembic upgrade head`, `seed_all.py`, and `python -m db.seed`.
- Uvicorn starts on `0.0.0.0:8000`.
- Railway `/ready` healthcheck succeeded.
- Redis deployment is healthy.
- Backend CORS is scoped to the new Himma deployment sandbox Vercel domains plus localhost development.
- Vercel project is connected to the isolated repository and configured to build from `apps/web`.
- `apps/web/.env.production` points the sandbox frontend to the Railway sandbox API.

## Not yet production-ready
- Temporary audio bypass is deliberately enabled for sandbox (`HIMMA_TEMP_AUDIO_SKIP=true`).
- No real student data should be introduced without explicit approval.
- Final hosted browser journey verification is still required.
- Open and investigating release blockers are tracked in `docs/audit/HIMMA_CONTINUOUS_AUDIT_REGISTER_AR.md`.

## Rollback
Use previous successful Railway/Vercel sandbox deployments. Do not force-push, hard-reset, or modify the original source repository branches. Database rollback requires a reviewed migration-specific plan.
