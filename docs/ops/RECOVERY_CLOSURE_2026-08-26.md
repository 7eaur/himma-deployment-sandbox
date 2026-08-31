# Corrective Recovery Closure — 2026-08-26

## Scope

Branch: `recovery/ui-media-admin-overhaul`  
Base: `d4bf7fff33bacf7ac02f4e0e81a72c659bf1a2ce`  
Implementation visual checkpoint: `7dbc52bcc70a5768c81cd04065be00f1949c429d`

This document closes only the corrective UI/media/supervisor/student recovery slice. It does not accept P07 real ASR.

## Defects corrected

| Area | Before | Corrective result |
|---|---|---|
| Assessment presentation | Canonical activities were flattened to generic choices | Runtime restores approved canonical interaction type and renders dedicated templates |
| Educational media | Approved images/audio could exist but resolve from the wrong package path | Real approved asset paths are served and byte-level regression-tested |
| Image questions | Text buttons instead of meaningful visual choices | Clickable approved image cards mapped to option IDs |
| Ordering/build-word | E2E could over-select disabled choices | Selection stops at the required answer count and confirms correctly |
| Recording | Inconsistent/basic handling | Student recording, stop, preview/re-record and submit states integrated |
| Adaptive reinforcement | Missing exact reinforcement could dead-end or invite unsafe fallback | No random fallback; student hold + supervisor approved same-level assignment + audit + resume |
| Adaptive concurrency | Duplicate reinforcement requests could roll back broader adaptive state | Nested/savepoint conflict handling preserves earlier state |
| Student hold UI | First implementation depended on utility classes not guaranteed in this app and leaked the underlying task visually | Scoped CSS module makes the hold state a real full-screen accessible dialog |
| Supervisor routes | Risk of rendering dashboard before auth check | Middleware/client verification redirect unauthenticated users to login before protected content |
| Terminology | Legacy researcher wording visible | Product UI uses `المشرف`; legacy `researcher` stays internal for compatibility |
| Student code | Legacy/non-simple code assumptions | Unique six-digit numeric auto/manual/edit/regenerate workflow |
| Supervisor settings | Incomplete management | Username, password and additional-supervisor workflows implemented |

## Evidence

Implementation gate: GitHub Actions #171 / run `32928214424` at SHA `7dbc52bcc70a5768c81cd04065be00f1949c429d`.

Result:

- Frontend: SUCCESS — TypeScript, ESLint, unit tests, Next.js production build.
- Backend: SUCCESS — approved catalog validation, migration upgrade/downgrade/upgrade, model drift, seed idempotency, backend tests.
- Integration: SUCCESS — PostgreSQL, Redis, pinned/checksummed MinIO, FastAPI, Next.js, Chromium.
- Playwright: SUCCESS — full vertical journey.

### Screenshot artifact inventory

1. Public child-focused landing.
2. Protected supervisor login.
3. Supervisor dashboard.
4. Student creation with six-digit code.
5. Student journey dashboard.
6. Real assessment image-choice media.
7. Assessment reading/recording UI.
8. Waiting for manual audio review.
9. Audio review queue cleared.
10. Assessment result.
11. First adaptive learning activity.
12. Adaptive activity with real media.
13. Adaptive reinforcement hold state.
14. Supervisor student-management state after ten core activities.
15. Supervisor reinforcement assignment success.
16. Student reinforcement resumed.
17. Supervisor live reports.

## Safety and data boundaries

- No fake production ASR provider.
- No automatic speech score is accepted merely because infrastructure exists.
- Unresolved/provider-failed/low-confidence speech remains human-review territory.
- Missing approved audio is not substituted with a similar word/syllable.
- Student reinforcement is never randomly selected when exact mapping is unavailable.
- Accepted Stage-2 and Stage-3 branches were not edited.

## Open blockers outside this closure

- OI-02 real ASR provider/privacy/cost/recording-transfer approval.
- Representative Arabic child-reading recordings.
- OI-03 confidence calibration/version.
- OI-05 production child-audio retention policy.
- OI-10 approved audio for `موز` and `سَا`.

## Closure rule

The recovery slice is closed only when the Quality Gate for the final documentation head is green. P07 remains `IN_PROGRESS / EXTERNALLY BLOCKED` regardless of this recovery closure.
