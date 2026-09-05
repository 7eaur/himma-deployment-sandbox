# Himma Sandbox Deployment Status

Last updated: 2026-09-05

## Scope
This is an isolated deployment/integration sandbox. It is not production approval and does not authorize merging into source branches.

## Continuous audit register
The authoritative living register for discovered defects, risks, verification gaps, resolutions, and release blockers is:

`docs/audit/HIMMA_CONTINUOUS_AUDIT_REGISTER_AR.md`

All new audit findings and later fix/reverification states should be recorded there instead of relying on chat history alone.

## Current services
- GitHub source: `7eaur/himma-deployment-sandbox` branch `main`.
- Railway project: `himma-sandbox`.
- Railway API: `himma-sandbox-api`.
- Railway PostgreSQL: managed `Postgres` service.
- Railway Redis: `himma-sandbox-redis`.
- Railway Storage Bucket: S3-compatible private audio bucket used by the API.
- Vercel project: `himma-deployment-sandbox`, Production deployment from `main`, Root Directory `apps/web`.

## Verified
- Railway source is `7eaur/himma-deployment-sandbox:main`.
- Railway deployment uses `deploy/railway-api.Dockerfile`.
- Docker image build succeeds.
- Alembic reaches the current head on Railway PostgreSQL.
- Railway pre-deploy runs `alembic upgrade head`, `seed_all.py`, and `python -m db.seed` during normal deployments.
- Approved runtime projection verifies 125 items: 30 pretest, 65 learning/reinforcement, and 30 posttest items.
- The legacy PostgreSQL dataset was copied into Railway PostgreSQL and row-count verified. The post-cutover audit showed the same application data plus one new Railway-side audit log generated after cutover.
- The legacy S3-compatible audio payload was copied into Railway Storage: 11 objects / 731,955 bytes, then verified by key presence and size.
- Railway Bucket CORS was applied and verified for the four configured trusted browser origins.
- The API now uses Railway PostgreSQL and Railway Storage through environment-variable references.
- Uvicorn starts on `0.0.0.0:8000`.
- Railway `/ready` succeeds after cutover and verifies config, database, approved content, approved audio, storage, and Redis.
- Authenticated researcher login was verified after cutover.
- Redis deployment is healthy.
- Student audio bypass code is removed; the stale `HIMMA_TEMP_AUDIO_SKIP` deployment variable is blank and no longer controls runtime behavior.

## Remaining infrastructure cleanup
- The obsolete `himma-verification` helper service has no public domain and should be deleted from Railway after final operator review.
- Four accidental Railway environments named `DATABASE_URL`, `S3_ENDPOINT`, `S3_ACCESS_KEY`, and `S3_SECRET_KEY` remain. The three S3-named environments contain no services; the `DATABASE_URL` environment contains obsolete sandbox deployments and should be deleted to avoid unnecessary resources.
- The legacy external database/storage must not be deleted until the owner accepts the Railway cutover. Rotate/decommission legacy credentials after acceptance.
- Credentials that appeared in private verification logs should be rotated before treating this sandbox as a long-lived environment.

## Rollback
Use previous successful Railway/Vercel sandbox deployments. Do not force-push, hard-reset, or modify the original source repository branches. The legacy external data source is intentionally retained temporarily as a rollback source until cutover acceptance.
