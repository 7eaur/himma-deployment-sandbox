# Himma — Final Maintenance & Trial Readiness Plan

Date: 2026-08-31
Branch: `recovery/ui-media-admin-overhaul`
Baseline before this plan: `4be998ab7c6d86d5cbb829ac37a97998ff675f11`

This plan merges the remaining maintenance work from the previous execution stream with the latest full-platform audit. It is the execution order for the final trial-readiness pass. It does not replace the approved academic content; it governs implementation, UX, reliability, and evidence.

## Non-negotiable invariants

- Runtime content remains 125 items: 30 pretest + 30 posttest + 30 core + 35 reinforcement.
- Formal pretest/posttest stays neutral during the assessment: no per-item correctness feedback, answer-revealing hints, stars, or rewards before completion.
- Learning activities use: `>=80 PASS`, `70–79 GUIDED_RETRY`, `<70 TARGETED_REINFORCEMENT`.
- Mastery trend uses the newest 3 valid evidences weighted 50/30/20.
- No random reinforcement.
- No automatic demotion.
- Invalid/incomplete/media-gap/unresolved-audio evidence is academically neutral and excluded.
- Manual override remains exceptional, reasoned, and auditable.
- Do not invent speech metrics or unresolved L3 thresholds as approved client facts.
- Existing accepted base branches remain untouched.
- No Docker requirement is introduced into this recovery stream.

## Phase R0 — Baseline and governance

Status: ACTIVE

1. Use the actual recovery-branch HEAD as the only implementation baseline.
2. Keep a single merged maintenance plan (this file) so later sessions do not regress to stale audit notes.
3. Update `STATUS.md`, `progress.json`, and content governance only after implementation evidence is green on the final SHA.
4. Preserve all historical attempts, decisions, reports, and audit trails during migrations.

Exit gate:
- branch/head confirmed;
- plan committed;
- no stale policy is treated as authoritative over current code + explicit latest decisions.

## Phase R1 — Adaptive Policy V4 (P0)

Status: NEXT

### R1.1 Remove automatic demotion

Current V3 behavior can demote after repeated low mastery. Replace with:

`weakness -> targeted reinforcement -> verification -> second targeted reinforcement if needed -> supervisor review hold`

No automatic `L2 -> L1` or `L3 -> L2` transition.

### R1.2 Promotion policy

Pilot/versioned policy for early promotion:

- at least 6 valid completed Core activities in the current level;
- mastery over newest three valid evidences >= 85 using 50/30/20;
- all configured critical skills have evidence;
- no configured critical skill below 70;
- no unresolved reinforcement cycle;
- no pending supervisor-review hold.

The numbers above are a trial policy to be calibrated after pilot evidence; they are not represented as a clinical or externally published diagnostic standard.

### R1.3 Critical skills are explicit

Do not treat every skill occurring in the 10 Core activities as automatically critical. Critical skills must come from explicit policy/content configuration. If a level has no explicit critical-skill configuration yet, fail safely rather than silently inventing one.

### R1.4 L3 pilot gate

Keep a separate, versioned pilot gate. Proposed operational values:

- pretest total >= 80;
- word-reading accuracy >= 80 when trustworthy evidence exists;
- connected-text reading accuracy >= 85 when trustworthy evidence exists;
- comprehension >= 70;
- no critical reading skill below 70.

If trustworthy audio evidence is unavailable, return an explicit unverified gate state rather than fabricating an accuracy value.

Exit gate:
- unit tests prove no automatic demotion;
- promotion cannot happen before minimum evidence/coverage;
- old 10/10-only promotion is removed from runtime decisioning;
- policy version is visible in persisted decision explanation.

## Phase R2 — Reinforcement and adaptive core selection (P0/P1)

Status: QUEUED

1. Bound reinforcement cycles to two intervention/verification rounds before supervisor review.
2. Keep supervisor hold authoritative after escalation; no infinite loop.
3. Select normal Core from eligible unused activities by:
   - prerequisites;
   - weakest or under-evidenced critical skill;
   - appropriate unused activity;
   - `order_index` only as a tie-breaker.
4. Preserve same-level reinforcement mapping and safe hold if no approved mapping exists.

Exit gate:
- deterministic tests for weak-skill prioritization;
- no cross-level/random reinforcement;
- escalation is finite and auditable.

## Phase R3 — Assessment retake, review, and comparison (P0/P1)

Status: QUEUED

### R3.1 Retake model

Support supervisor-authorized pre/post retakes without deleting history:

- attempt number;
- previous attempt link;
- authorized by;
- authorization reason;
- authorization time;
- official assessment attempt flag/reference.

Reports preserve initial, retake, and official values.

### R3.2 Review versus retake neutrality

- During pre/post: no correctness/answer key.
- After assessment while a retake remains possible: student gets skill-level summary, not a detailed answer key.
- Supervisor may inspect full item-level details.
- After retake is closed/final: student answer review may reveal correct answer and age-appropriate explanation.
- After final posttest: enable full answer review + pre/post comparison.

### R3.3 Student progress page

Add a child-friendly `تقدمي` view showing:

- before score/level;
- after score/level;
- absolute improvement;
- simple skill comparison;
- answer-review entry point when policy allows.

### R3.4 Supervisor test tab

Show pre/post attempts, dates, duration, scores, item errors, affected skills, retake controls, reasons, and comparison.

Exit gate:
- migration roundtrip + drift clean;
- old attempts remain readable;
- retake does not leak answer key before finality;
- reports explicitly identify the official attempt.

## Phase R4 — Student UX and visual safety gate (P0)

Status: QUEUED

1. Fix activity viewport behavior so the primary CTA can never be clipped.
2. Keep one-screen presentation when content fits; allow controlled internal/page scrolling when it does not.
3. Verify the assessment result primary CTA styling and contrast from current screenshots/artifacts.
4. Add browser assertions for:
   - primary CTA visible and fully inside viewport;
   - no horizontal overflow;
   - minimum 44x44 interactive targets;
   - no overlap of critical controls;
   - no unresolved CSS custom properties;
   - representative assessment/activity/reinforcement/retry states.
5. Re-check mobile and reduced-motion behavior.

Exit gate:
- screenshots visually reviewed;
- responsive gate checks usability, not merely page rendering.

## Phase R5 — Supervisor 360 and control design (P1)

Status: QUEUED

1. Keep current high-level tab structure.
2. Expand student detail into Student 360:
   - overview;
   - journey;
   - pre/post attempts and errors;
   - skills/evidence;
   - reinforcement/adaptation;
   - audio reviews;
   - reports;
   - account;
   - audit history.
3. Convert manual level override into a documented administrative exception:
   - confirmation;
   - mandatory reason;
   - impact explanation;
   - immutable previous decision history;
   - report badge for manual override.
4. Run a full control audit: KEEP / RESTYLE / MOVE / MERGE / REMOVE / ADD.
5. Dashboard prioritizes actionable queues, not only counts.

## Phase R6 — Audio and assessment completion architecture (P0/P1)

Status: QUEUED / EXTERNAL-GATED PARTLY

1. `HIMMA_TEMP_AUDIO_SKIP` must default to false for real trial/production.
2. Trial/production must fail startup if temporary audio skip is explicitly enabled.
3. Keep test-only neutral skip behavior available in controlled non-trial environments.
4. Consolidate assessment finish into one completion service; router registration order must not determine business rules.
5. Preserve no-fabricated-speech-metrics behavior.

External blockers retained:
- real ASR provider/calibration/privacy work;
- approved static audio gaps for `موز` and `سَا`.

Do not mark M08 or the entire platform complete while these remain unresolved.

## Phase R7 — Content runtime governance (P1)

Status: QUEUED

Current runtime is a projection of baseline + versioned additions + corrections + presentation overlays. Documentation must match reality.

Preferred design:
- preserve versioned source layers;
- deterministic compiler produces one validated runtime projection/catalog for runtime and QA;
- generated artifact records source versions/digest/counts;
- 125/35 invariants are tested.

## Phase R8 — Recording, auth, readiness, and operations (P1)

Status: QUEUED

1. Durable upload reservation tied to student/session/attempt/step/storage key, expiry, size, MIME, and consumed state.
2. Verify max upload size and MIME; sanitize storage errors.
3. Add login rate limiting/throttle and failed-login audit for student and supervisor flows.
4. Separate session lifetime policy for student and supervisor if needed.
5. Keep `/health` for liveness; add `/ready` for DB/storage/Redis/critical config.
6. Add structured request IDs/error tracking baseline.
7. Document backup procedure and perform a restore test before trial.
8. Lock/constraint backend dependency versions after functional P0/P1 changes stabilize.

## Phase R9 — Final governance and trial gate

Status: QUEUED

1. Update `STATUS.md`, `progress.json`, README/content governance to the exact final SHA and current 125/35 counts.
2. Protect the intended trial/release branch with required quality checks where repository policy allows.
3. Run full backend/frontend/integration/Playwright/responsive gates on the same SHA.
4. Download and visually review final Playwright/responsive artifacts.
5. Produce final closure report with SHA, run IDs, artifacts/digests, remaining external dependencies, and explicit UAT status.

## Priority summary

### P0 before real student trial

- Adaptive Policy V4; no automatic demotion.
- Early-promotion gates and explicit critical-skill policy.
- Bounded reinforcement/escalation.
- Retake foundation and review-neutrality rules.
- Activity/result CTA usability + stronger visual assertions.
- Trial fail-closed audio skip.
- Final same-SHA quality gate.

### P1 product/trial readiness

- Student answer review and pre/post comparison.
- Supervisor item-error/attempt/skill evidence views.
- Weakest-skill Core selection.
- Unified assessment completion service.
- Runtime content governance.
- Recording reservations.
- Auth throttling.
- Readiness/observability/backup baseline.
- Supervisor control/design audit.

### P2 after trial-critical closure

- Task-player/front-end refactor where evidence justifies it.
- Backend domain cleanup.
- Dependency locking/maintenance automation.
- Landing/performance refinement.
- Non-blocking technical-debt cleanup.

## Execution rule

Do not declare a phase complete from code inspection alone. Closure requires the implementation commit SHA plus the relevant tests/workflows on that same SHA. Green CI does not replace visual/UAT evidence for UX-critical screens.
