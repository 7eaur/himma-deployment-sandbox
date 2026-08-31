# M09 Release Readiness — Evidence 2026-08-31

## Scope

This evidence closes only the internal M09 infrastructure readiness / backup-restore slice. It does **not** close full M09 UAT and does not change M08 external-gated speech status.

## Verified implementation SHA

`9f4389d83f751910daf605e1c37b4232b5b3ae93`

Commit: `feat(m09): add backup restore release gate`

Parent readiness hardening SHA:

`a5545a1425cc99891972e2ec55b290198cb98034`

Commit: `feat(m09): add trial-safe readiness gate`

## Main Quality Gate

Workflow: `Himma CI — Quality Gate`  
Run number: `#496`  
Run ID: `33344517705`  
Head SHA: `9f4389d83f751910daf605e1c37b4232b5b3ae93`

Result:

- backend: SUCCESS
- frontend: SUCCESS
- integration: SUCCESS
- Playwright E2E: SUCCESS
- approved content validation: SUCCESS
- Alembic upgrade/downgrade/upgrade + drift check: SUCCESS
- seed idempotency: SUCCESS

## M09 Release Readiness Gate

Workflow: `Himma M09 — Release Readiness Gate`  
Run number: `#1`  
Run ID: `33344517713`  
Head SHA: `9f4389d83f751910daf605e1c37b4232b5b3ae93`

Result: SUCCESS.

Verified steps:

1. approved catalog + migrations + runtime seed build;
2. pinned MinIO startup and private synthetic test bucket;
3. trial startup fails closed if `HIMMA_TEMP_AUDIO_SKIP=true`;
4. `/health` liveness and `/ready` dependency readiness against PostgreSQL + Redis + MinIO;
5. PostgreSQL custom-format backup, isolated restore, and critical-table count comparison;
6. private object-store backup and isolated restore with SHA-256 integrity verification;
7. backup artifacts remain ephemeral in CI and are not uploaded.

## Responsive evidence

No UI files changed between the last responsive-tested readiness code and the M09 backup/runbook commit.

Latest relevant responsive run:

- Workflow: `Himma M04 — Responsive Visual Gate`
- Run number: `#95`
- Run ID: `33344062713`
- Head SHA: `a5545a1425cc99891972e2ec55b290198cb98034`
- Result: SUCCESS

The subsequent `9f4389d...` commit changes operational scripts/workflow/runbook only, so it does not invalidate the responsive visual evidence.

## Files introduced/changed in the closed slice

- `services/api/readiness.py`
- `services/api/runtime_flags.py`
- `services/api/main.py`
- `services/api/test_readiness.py`
- `scripts/ops/backup_postgres.sh`
- `scripts/ops/restore_postgres.sh`
- `scripts/ops/verify_backup_restore.py`
- `scripts/ops/backup_object_store.py`
- `scripts/ops/restore_object_store.py`
- `.github/workflows/m09-release-readiness.yml`
- `docs/ops/M09_RELEASE_UAT_RUNBOOK.md`

## What remains open

M09 remains `IN_PROGRESS`. The next internal item is full-journey UAT and release closure evidence, especially the missing single-candidate journey through pretest → learning levels/reinforcement → L3 completion → posttest → reports/exports. Monitoring/request correlation, study-time support, final privacy/retention approval, and final release checklist also remain open.

M08 real speech provider/calibration/privacy remains external-gated. Exact static audio `موز` and `سَا` remain missing and must not be synthesized/substituted without an approved source.
