# STATUS — Himma Platform

**Last updated:** 2026-08-31  
**Repository:** `7eaur/himma-`  
**Current branch:** `recovery/ui-media-admin-overhaul`  
**Current program:** Full Maintenance / Recovery + R1→R4 corrections  
**Current focus:** M09 full-journey UAT / release closure while M08 remains external-gated

## Read this first

Canonical continuity handoff:

`docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-08-31_AR.md`

The handoff is deliberately more detailed than this status file and must be read before continuing in a new conversation.

## Latest verified executable baseline

`9f4389d83f751910daf605e1c37b4232b5b3ae93`

Commit:

`feat(m09): add backup restore release gate`

Evidence for this exact implementation SHA:

- Main Quality Gate #496 — run `33344517705`: backend ✅ frontend ✅ integration/Playwright ✅
- M09 Release Readiness Gate #1 — run `33344517713`: ✅ SUCCESS
- M09 evidence: `docs/ops/M09_RELEASE_READINESS_EVIDENCE_2026-08-31.md`

Relevant responsive evidence:

- Responsive Visual Gate #95 — run `33344062713` on `a5545a1425cc99891972e2ec55b290198cb98034`: ✅ SUCCESS
- The following `9f4389d...` commit changes operational scripts/workflow/runbook only; no UI files changed.

Documentation-only commits after the verified executable SHA may move branch HEAD. Inspect the current HEAD and its Actions before starting new code.

## Current runtime truth

- Original approved catalog: 105 items.
- Reinforcement additions: +20 total.
- Runtime total: **125**.
- Reinforcement total: **35**.
- Skills: 44.
- Original source semantics remain preserved.

## Current academic/adaptive contract

Placement:

- 100 points = 20 readiness + 40 word building/reading + 40 fluency/comprehension.
- readiness <12/20 forces L1.
- total <50 → L1.
- 50..<80 → L2 subject to reading gates.
- L3 requires total/gates; do not invent an unresolved text-accuracy threshold.

Learning activity bands:

- >=80 PASS.
- 70..<80 GUIDED_RETRY.
- <70 WEAKNESS_EVENT / targeted reinforcement.

Mastery evidence: newest three valid attempts only, weighted 50/30/20.

### R1 current promotion policy

The current branch intentionally supports early promotion in L1/L2 when all current gates pass:

- minimum 6 completed Core activities;
- mastery >=85;
- critical-skill floor >=70;
- required critical-skill coverage complete;
- no unresolved reinforcement/review blockers;
- promote by one level only.

Automatic demotion remains disabled; repeated low evidence produces support on the same level.

L3 still requires full evidence before journey completion/posttest readiness.

This replaces older documentation that said all promotions must wait for 10/10 Core. Do not silently restore the old rule.

## Reinforcement lifecycle

Durable flow is implemented:

`weakness → mapped reinforcement → reinforcement completion → reopen source core → verify failed source steps → verified/escalated → continue`.

No random/cross-level reinforcement. Neutral media/audio skips are not failure evidence.

## R2 active session transition

`services/api/activities_v4.py` bridges `/activities/session/{id}/next` so early promotion cannot return an item bound to a just-closed session. The response’s active `session_id` is authoritative when a promotion creates a new level session.

## R3 assessment retake history

Supervisor-authorized pre/post retake history/index behavior is implemented on the current lineage. Recent commits scoped assessment uniqueness correctly while keeping Core sessions outside retake uniqueness, then aligned DB indexes with ORM. Regression coverage exists. Inspect migrations/models/tests before extending the behavior.

## Student UX / QX

Closed baseline:

- child-clear non-generic instructions;
- answers under the question;
- contextual learning hints/success/error;
- formal assessment neutral per item;
- subtle student sound/reward effects with mute/reduced-motion;
- no permanent side mascot rail;
- responsive touch targets;
- source-grounded option repairs;
- browser E2E question-experience coverage.

QX historical closure SHA: `d6bab135e46ed93de3ac98236c5aa78e804c27ab`.

## Educational media

- Ten generated sequence scenes are checked in and wired.
- IDs: `HIMMA-GEN-SEQ-001..010`.
- Visual plan `generate` list is empty.
- Browser fidelity coverage requests assets through the real media route.

## Audio / M08

Static audio:

- existing: 50;
- missing: `موز`, `سَا`;
- target: 52.

`HIMMA_TEMP_AUDIO_SKIP` is testing-only and academically neutral. Trial/production startup now fails closed if that bypass is enabled.

Target architecture: Reference-Guided Arabic Reading Analysis = ASR + reference alignment + C/D/I/S + phonemic helper evidence.

M08 remains **PENDING / EXTERNAL-GATED** because provider, calibration, privacy/retention, and production policy are not complete. Do not claim production speech analysis complete.

## Reports / M07

Implemented:

- persisted pre/post summaries and improvement metrics;
- level/time/attempt/reinforcement summaries;
- cohort reports;
- XLSX/PDF exports + audit logging;
- per-skill descriptive summary from persisted graded evidence;
- supervisor UI wiring.

Per-skill reporting remains descriptive and must not silently become a mastery/adaptation rule.

## M09 Release / UAT

Closed internal infrastructure slices:

- `/health` retained as liveness and `/ready` added for critical configuration + PostgreSQL + Redis + private S3/MinIO readiness;
- sanitized readiness output without raw dependency exceptions/secrets;
- trial/production fail-closed guard for temporary audio bypass and short API secret;
- executable PostgreSQL backup/restore + integrity/count verification;
- executable private object-store backup/isolated restore + SHA-256 verification;
- dedicated `Himma M09 — Release Readiness Gate` green on run `33344517713`;
- release/UAT runbook added at `docs/ops/M09_RELEASE_UAT_RUNBOOK.md`.

M09 is **not closed**. Remaining internal work centers on a complete single-candidate UAT journey, monitoring/request correlation/support readiness, final privacy/retention approval, rollback/release checklist, and final acceptance evidence.

## Stage status

- M00 Restore Green — CLOSED.
- M01 Placement — CLOSED baseline.
- M02 Adaptation state machine — CLOSED baseline, later refined by R1.
- M03 Reinforcement — CLOSED baseline + gap closure.
- M04 Student Product UI — CLOSED baseline + QX corrections.
- M05 Supervisor Product UX — CLOSED baseline.
- M06 Responsive/Accessibility/Design QA — CLOSED baseline.
- M07 Research Reports — IMPLEMENTED/CLOSED baseline.
- M08 Real Speech Analysis — PENDING / EXTERNAL-GATED.
- M09 Release/UAT — IN PROGRESS; infrastructure readiness/backup slice GREEN, full-journey UAT NEXT.

## Next action

1. Inspect current branch HEAD and Actions after any documentation-only commit.
2. Continue M09 with the first still-unproven internal requirement: full single-candidate journey UAT from supervisor/student setup through pretest, learning/reinforcement/level transitions, L3 completion, posttest, reports and exports.
3. Do not duplicate scenarios already proved by the same-SHA Quality Gate; extend coverage only where the end-to-end transition is missing.
4. Keep M08 separate until external provider/calibration/privacy decisions are available.
5. Acquire/add only the exact missing static audio `موز` and `سَا` from an approved source; do not fake/substitute them.
6. Run final visual review after substantial UI/runtime changes.

## Governance reminder

Do not modify accepted base branches directly, do not force/reset destructively, do not declare PASS without exact SHA/run evidence, and do not launch/merge production without explicit user approval.
