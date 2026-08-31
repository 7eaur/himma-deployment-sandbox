---
description: Execute the currently approved Himma roadmap stage through implementation, tests, browser verification, and evidence
---

Execute exactly the current stage from `docs/ops/progress.json` using `@lead` and the `himma-stage-execution` skill.

1. Confirm phase 0 plan approval exists before writing production code.
2. Read only the current stage, its active acceptance IDs, relevant specifications, current diff, and directly related source files.
3. Create or switch to the stage branch without discarding existing work.
4. Break the stage into vertical slices. For each slice:
   - state behavior and acceptance IDs;
   - implement UI/API/data/audit changes as applicable;
   - add/update migrations and idempotent seed data;
   - add tests before declaring the slice done;
   - run targeted tests and fix failures;
   - update status and commit a coherent green slice.
5. Use relevant skills only: `careful` for risky migrations/auth/destructive operations; `plan-design-review` before a new child-facing pattern; `review` after code changes; `qa` for real-browser verification. If these names are unavailable, perform the equivalent checklist locally.
6. Continue autonomously within the approved stage. Pause only for a gate listed in `10-delivery-protocol.md`.
7. At the end, run the full stage gate through `himma-quality-gate`. Do not advance `current_stage` if it fails.
8. Produce `docs/ops/stage-XX-report.md`, evidence artifacts, and a concise user report.

