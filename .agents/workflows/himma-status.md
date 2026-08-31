---
description: Return a compact evidence-based status for Himma without consuming context on a full recap
---

Read only `STATUS.md`, `progress.json`, `git status`, the current stage report, and the latest gate result.

Return exactly:

1. Stage/state.
2. Completed since the last green commit.
3. Tests: passed/failed/skipped.
4. Evidence paths.
5. Blocker requiring user action, or `None`.
6. Next action.

Do not restate project history, specifications, or future stages.

