# M09 — Release / UAT Runbook

**Status:** IN PROGRESS — internal release-readiness only.  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Production launch:** NOT AUTHORIZED by this document.

## 1. Purpose

This runbook defines the repeatable technical steps for a controlled Himma trial/release candidate without reopening completed academic or UX work. It complements the canonical continuity handoff and keeps M08 real speech analysis as a separate external gate.

## 2. Hard release blockers that remain external

A release candidate must not be described as production-complete while any of the following remains unresolved:

- M08 real speech provider / calibration / privacy-retention decisions.
- Any client/source decision explicitly recorded as open in the continuity handoff.

The approved static-audio catalog must validate with no declared media gaps. The former temporary student audio bypass has been deleted from the API and web application; no environment variable may restore it.

## 3. Environment contract

Required runtime configuration:

- `DATABASE_URL`
- `API_SECRET_KEY` (minimum 32 characters in trial/production)
- `S3_ENDPOINT`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET_NAME`
- `REDIS_URL`
- `CORS_ORIGINS`
- supervisor credentials only through the deployment secret store
- `ENV=trial` or `ENV=production`

Never commit real credentials, child data, recordings, database dumps, or production `.env` files.

## 4. Health and readiness

- `GET /health` is liveness only: the API process is running.
- `GET /ready` is traffic readiness: critical configuration, PostgreSQL, private object storage, and Redis must all report `ok`.
- A deployment should not receive user traffic until `/ready` returns HTTP 200.
- `/ready` intentionally returns sanitized component state only; raw dependency exceptions or secrets are not exposed.

## 5. Database migration and content order

For a release candidate:

1. Take a pre-deployment backup.
2. Validate the approved content catalog.
3. Run `alembic upgrade head`.
4. Run the canonical runtime seed commands used by CI.
5. Start API and verify `/health` then `/ready`.
6. Start web application.
7. Execute release smoke/UAT against synthetic accounts before study data is admitted.

Do not use `downgrade` on a live study database as a routine rollback technique. Application rollback and data rollback are separate decisions.

## 6. PostgreSQL backup and restore drill

Create a private custom-format dump:

```bash
DATABASE_URL='...' bash scripts/ops/backup_postgres.sh /private/backup/himma-postgres.dump
```

Restore only into an explicitly prepared empty recovery database:

```bash
RESTORE_DATABASE_URL='...' bash scripts/ops/restore_postgres.sh /private/backup/himma-postgres.dump
DATABASE_URL='...' RESTORE_DATABASE_URL='...' python scripts/ops/verify_backup_restore.py
```

The reusable restore script never drops or creates a database. The operator must deliberately prepare the restore target first. The backup and checksum must be stored outside the application host on encrypted/private storage according to the approved retention policy.

## 7. Private object-store backup and restore drill

For the current small research deployment, the repository includes a deterministic filesystem backup/restore utility for the private S3/MinIO bucket:

```bash
python scripts/ops/backup_object_store.py /private/backup/himma-objects
RESTORE_S3_BUCKET_NAME='himma-audio-restore-test' python scripts/ops/restore_object_store.py /private/backup/himma-objects
```

The restore utility verifies SHA-256 content integrity. Restore drills must target an isolated bucket. Never overwrite the active study bucket as part of a drill.

For future scale beyond this research deployment, move to provider-native bucket versioning/replication/snapshots rather than treating a filesystem copy as the long-term architecture.

## 8. UAT scenarios still required before M09 can close

M09 is not closed by health checks or backup tests alone. Final UAT evidence must cover at least:

1. supervisor login and student creation;
2. student code login;
3. full 30-item pretest with real browser recording upload and review;
4. placement into a starting level;
5. learning journey across required levels, including early-promotion rules where applicable;
6. targeted reinforcement, source-step verification, and escalation path;
7. posttest remains blocked until L3 journey completion;
8. supervisor enables and student completes the 30-item posttest;
9. reports, per-skill descriptive evidence, XLSX/PDF export and audit record;
10. refresh/resume, denied microphone, upload/network failure, stale session, unauthorized role/IDOR negative checks;
11. mobile and desktop smoke evidence on the approved responsive matrix.

Existing CI/E2E evidence may be reused when it proves the exact same contract on the exact candidate SHA. Do not rerun completed work solely for ceremony, but do not claim a missing end-to-end transition is covered by unrelated tests.

For adaptive-learning browser verification, `GET /learning-experience/session/{id}` is the authoritative payload for the interaction currently rendered to the student. `GET /activities/session/{id}/next` advances the session and reports transition status; its response must not be used as a substitute for the visible learning-experience contract.

## 9. Monitoring and incident minimums

Before a real trial, the deployment owner must have:

- HTTPS termination and valid certificate;
- process/service restart policy;
- PostgreSQL, Redis, and object-store availability monitoring;
- API error-rate and latency visibility;
- disk/capacity alerting for the recording store;
- application logs that do not expose student recordings, secrets, access tokens, or unnecessary child data;
- a documented contact owner for study-time incidents.

Request IDs / structured error correlation remain part of the M09 hardening backlog until implemented and evidenced.

## 10. Privacy and retention release checkpoint

No real child recording should be admitted until the researcher/client approves the retention/deletion policy. The release checklist must record:

- what student identifiers are stored;
- where recordings are stored;
- who can play/download them;
- retention duration;
- deletion/archive procedure at study end;
- backup retention and secure destruction;
- whether any external speech provider receives recordings and under what agreement.

M08 provider decisions and M09 release readiness meet at this checkpoint; neither should silently override the other.

## 11. Rollback policy

If a release candidate fails before study traffic begins:

1. stop routing traffic to the candidate;
2. redeploy the last verified application SHA;
3. restore data only when a documented migration/data incident requires it;
4. restore into isolation first and verify counts/integrity before any destructive production action;
5. record the incident, affected SHA, commands, evidence, and decision.

No force-reset or destructive branch rewrite is part of the release procedure.

## 12. Automated M09 infrastructure gate

`.github/workflows/m09-release-readiness.yml` verifies on a synthetic environment:

- the deleted temporary student audio-bypass route remains absent;
- `/ready` reaches PostgreSQL, Redis, and MinIO;
- approved catalog + migrations/seeds build successfully;
- PostgreSQL dump/restore preserves critical table counts;
- private object-store backup/restore preserves object SHA-256 integrity;
- backup files remain ephemeral and are not uploaded as CI artifacts.

Passing this gate closes only the infrastructure backup/readiness slice of M09. Full-journey UAT, monitoring/support/privacy decisions, M08 external gates, and final release approval remain separate.
