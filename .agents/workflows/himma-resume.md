---
description: Resume Himma work from repository state without restating or re-reading the entire project
---

Resume from durable state.

1. Read `docs/ops/STATUS.md`, `docs/ops/progress.json`, `git status`, the latest stage report, and the current branch log.
2. Inspect uncommitted changes before editing. Determine whether they belong to the active slice and preserve unrelated user work.
3. Run the smallest relevant health/test command to verify the recorded checkpoint.
4. If state and repository agree, continue the `next_action` through `/himma-stage` behavior.
5. If they disagree, stop implementation, reconcile status from Git/test evidence, record the discrepancy, and then continue.
6. Do not summarize old stages or reopen settled decisions unless current evidence contradicts them.

Report in at most six bullets: resumed stage; last green point; current slice; verification; blocker; next action.

