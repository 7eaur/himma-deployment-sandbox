# Himma Sandbox Deployment Architecture

Status: sandbox only. This document does not authorize production promotion or branch merging.

## Source
- Repository: `7eaur/himma-deployment-sandbox`.
- Deployment branch: `main`.
- Application remains the existing monorepo; no backend rewrite was performed for the infrastructure migration.

## Runtime topology
- Vercel: Next.js frontend from `apps/web`.
- Railway Web Service: FastAPI/Uvicorn backend from the monorepo root using `deploy/railway-api.Dockerfile`.
- Railway PostgreSQL: relational database used through the existing SQLAlchemy/Alembic layer.
- Railway Redis: runtime cache/queue dependency.
- Railway Storage Bucket: private S3-compatible object storage used through the existing boto3 layer and presigned URLs.

## Request flow
Browser -> Vercel Next.js -> `/api/*` proxy -> Railway FastAPI -> Railway PostgreSQL / Railway Redis / Railway Storage.

The frontend build receives `NEXT_PUBLIC_API_URL` pointing at the Railway sandbox API. Backend readiness is checked at `/ready`; process liveness remains `/health`.

## Database lifecycle
Normal Railway pre-deploy command is implemented by `deploy/railway-predeploy.sh` and performs:
1. `python -m alembic upgrade head`
2. `python seed_all.py`
3. `python -m db.seed`

`seed_all.py` is idempotent and fails if the approved runtime projection is inconsistent. The current readiness contract verifies 125 runtime items: 30 pretest, 65 learning/reinforcement, and 30 posttest items.

One-time migration helpers remain in `deploy/` for auditable rollback/recovery work:
- `migrate_supabase_to_railway.py`
- `migrate_storage_to_railway.py`
- `configure_railway_bucket_cors.py`

They are inactive during normal deployments unless their explicit mode variables are set.

## Railway API service
- Source branch: `main`.
- Root directory: `/`.
- Dockerfile: `deploy/railway-api.Dockerfile`.
- Healthcheck: `/ready`.
- Port: `8000`.
- Public API: `https://himma-sandbox-api-production.up.railway.app`.

## Data cutover state
- PostgreSQL data was migrated from the legacy external sandbox to Railway PostgreSQL and row-count verified.
- Audio/object data was migrated to Railway Storage and verified by object presence and byte size.
- Browser upload CORS for the Railway bucket was applied and verified against the configured trusted origins.
- Runtime `DATABASE_URL` and `S3_*` variables now resolve to Railway-managed resources.
- The legacy external source is retained temporarily only for rollback until the owner accepts the cutover.

## Safety boundaries
- No original source branch was merged or rewritten by the infrastructure cutover.
- Secrets remain in platform environment variables, not Git.
- Student recording bypass code is removed; submitted recordings continue through the approved review path until automatic speech analysis is integrated.
- Academic content, scoring, and adaptive rules were not changed for deployment convenience.
- Do not delete the legacy data source until final cutover acceptance and credential rotation are complete.

## Rollback
1. Keep original source branches untouched.
2. Railway: redeploy a previously successful sandbox deployment if the application release itself must be rolled back.
3. Vercel: promote/redeploy the previous sandbox deployment if needed.
4. Data: until cutover acceptance, the retained legacy external source is the recovery reference; do not attempt destructive reverse migration without a reviewed plan.
