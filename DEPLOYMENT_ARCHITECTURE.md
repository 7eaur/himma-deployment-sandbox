# Himma Sandbox Deployment Architecture

Status: sandbox only. This document does not authorize production promotion or branch merging.

## Source
- Repository: `7eaur/himma-`
- Deployment branch: `deployment/platform-sandbox`
- Application remains the existing monorepo; no backend rewrite was performed.

## Runtime topology
- Vercel: Next.js frontend from `apps/web`.
- Railway Web Service: FastAPI/Uvicorn backend from the monorepo root using `deploy/railway-api.Dockerfile`.
- Railway Redis: runtime cache/queue dependency.
- Supabase PostgreSQL: sandbox relational database used through the existing SQLAlchemy/Alembic layer.
- Supabase Storage S3 protocol: object storage used through the existing boto3-compatible layer.

## Request flow
Browser -> Vercel Next.js -> `/api/*` proxy -> Railway FastAPI -> PostgreSQL / Redis / S3.

The frontend build receives `NEXT_PUBLIC_API_URL` pointing at the Railway sandbox API. Backend readiness is checked at `/ready`; process liveness remains `/health`.

## Database lifecycle
Railway pre-deploy command:
`python -m alembic upgrade head && python seed_all.py`

`seed_all.py` is idempotent and fails if the approved runtime counts are inconsistent. It validates 105 baseline items, 35 reinforcement items, 125 total approved runtime items, and Student Experience v2 projection on all 125 items.

## Railway service
- Source branch: `deployment/platform-sandbox`
- Root directory: `/`
- Dockerfile: `deploy/railway-api.Dockerfile`
- Healthcheck: `/ready`
- Port: `8000`
- Public API: `https://himma-sandbox-api-production.up.railway.app`

## Safety boundaries
- No source branch was merged or rewritten.
- No production database is used by this sandbox configuration.
- Secrets are stored in platform environment variables, not Git.
- `HIMMA_TEMP_AUDIO_SKIP=true` remains sandbox-only and must not be carried into trial/production.
- Academic content/scoring/adaptive rules were not changed for deployment convenience.

## Rollback
1. Keep source branches untouched.
2. Railway: redeploy a previously successful sandbox deployment or reconnect the sandbox branch to an earlier known-good sandbox commit.
3. Vercel: promote/redeploy the previous sandbox deployment.
4. Database: migrations must only be rolled back after reviewing migration reversibility and sandbox data impact.
