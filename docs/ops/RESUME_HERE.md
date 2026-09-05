# RESUME HERE — Post-Recovery Decision Boundary

**Last updated:** 2026-09-05  
**Repository:** `7eaur/himma-`  
**Current branch:** `recovery/ui-media-admin-overhaul`  
**Recovery status:** `A–I CLOSED — READY_FOR_USER_DECISION`

## Final executable candidate

`976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb`

Exact-SHA evidence on that same candidate:

- Quality Gate `33979846641` — **SUCCESS**.
- M04 Responsive Visual Gate `33979846639` — **SUCCESS**.
- M09 Release Readiness Gate `33979846640` — **SUCCESS**.

Later commits may update documentation only. Do not confuse docs-only HEAD with the final executable candidate above. If executable code changes after `976b...`, require a new single-SHA Quality/M04/M09 cycle.

## What is closed

Recovery phases A through I are closed on the repository branch.

The closure includes:

1. Structured DB-driven student runtime and deterministic content projection.
2. 30-question pretest and 30-question posttest lifecycle.
3. Human-authoritative student audio review with `uploaded`, `graded`, and `rerecord_required` states.
4. No reachable student audio-completion bypass.
5. Approved static audio contract with 54 IDs / 54 WAV / 54 MP3 and no required static media gap.
6. Initial placement aligned to ADR-014.
7. V4 adaptive activity/reinforcement/promotion state machine.
8. Safe supervisor manual overrides with history preservation.
9. Targeted same-level reinforcement without random/cross-level fallback.
10. Reports/exports proven not to manufacture academic mastery state.
11. Security hardening: maintained JWT implementation, dependency audits, Gitleaks and CI production-quality guards.
12. Final same-SHA Quality/M04/M09 evidence.

Detailed closure:

`docs/ops/HIMMA_PHASE_F_I_CLOSURE_2026-09-05_AR.md`

Evidence index:

`docs/ops/EVIDENCE_INDEX.md`

## Active academic rules to preserve

### Initial placement

- `<50` → L1.
- `50..<80` → L2.
- `80..100` → L3.

The former readiness `12/20` condition and additional L3 numeric gates are superseded for active placement by ADR-014.

### Learning/adaptation

- Activity `>=80` → pass.
- `70..<80` → guided retry.
- `<70` → targeted reinforcement.
- L1/L2 early promotion requires at least 6 Core + mastery >=85 + critical coverage + critical floor >=70 + no unresolved reinforcement/audio/supervisor review blocker.
- Only one-level promotion.
- No automatic demotion.
- L3 requires all 10 Core before final learning completion.
- Latest three valid active-session Core evidences use weights 50/30/20.

## Audio contract to preserve

Current authority is:

`record -> persist/upload -> supervisor review -> graded / rerecord_required -> continue`

Do not add a fake score or silently let `uploaded` complete an assessment/activity. Automated ASR remains future work until its provider, privacy and calibration gates are approved.

Authoritative contract:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

## Open external/production items

Use `docs/ops/OPEN_ITEMS.md` as the current list. Important unresolved gates include:

- OI-02: real production ASR provider/module contract if automatic analysis is pursued.
- OI-03: confidence/calibration version before automatic speech decisions.
- OI-04: intervention/session duration before study activation.
- OI-05: child-audio retention policy before real-child production data.
- OI-06: domain/hosting before deployment.
- OI-07: supervising organization details/logo before final report signoff.
- OI-08: credential rotation before production/deployment if any historical value was actually used.

**OI-10 is CLOSED.** `WRD-29` («موز»), `SYL-13` («سَا»), `INS-01`, and `INS-02` are present in the approved audio contract. Do not reopen the old missing-audio statement.

## Next action

Stop at the owner decision boundary.

No merge, release, or deploy has been performed.

The next conversation should first read:

1. `docs/ops/STATUS.md`
2. `docs/ops/progress.json`
3. `docs/ops/EVIDENCE_INDEX.md`
4. `docs/ops/HIMMA_PHASE_F_I_CLOSURE_2026-09-05_AR.md`
5. `docs/ops/OPEN_ITEMS.md`
6. `docs/ops/DECISIONS.md` — especially ADR-014

Then continue only from the owner-selected next step: integration/release authorization, production external readiness, or future P07 automatic speech analysis.