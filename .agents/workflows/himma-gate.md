---
description: Independently verify the current Himma stage against acceptance criteria before it can be closed
---

Act as independent `@qa` and `@security`. Prefer a fresh conversation or separate review agent that did not implement the stage.

1. Read the current stage report, mapped acceptance rows, code diff since the previous green stage, migrations, and test changes.
2. Use the `himma-quality-gate` skill. If installed, also use gstack `review` and `qa`; use `plan-design-review` only for a material UI change.
3. Attempt to falsify completion: wrong-role access, boundary values, duplicate submits, reconnects, low-confidence audio, worker outage, stale sessions, malformed content, and mobile RTL.
4. Run the full mandatory check set. Verify skipped/disabled tests and mock/demo markers.
5. Browser-test the actual user journey and attach screenshots/recording plus reproducible steps.
6. Write `docs/ops/gate-stage-XX.md` with PASS/FAIL per acceptance ID, commands/results, defects, and evidence paths.
7. On FAIL: update `progress.json.failed_gates`, keep the current stage, and return defects to implementation.
8. On PASS: record the green commit, mark the stage completed, set the next stage to READY, and update status. Do not deploy production unless separately approved.

