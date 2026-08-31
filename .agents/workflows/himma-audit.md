---
description: Audit the Himma repository and produce the phase-0 implementation plan without writing production code
---

Run the phase-0 audit as `@architect` and `@security`.

1. Read the three workspace rules, `PROJECT_STATE.md`, `ROADMAP.md`, `REFERENCE_INVENTORY.md`, `ARCHITECTURE_BASELINE.md`, and current status.
2. Inventory skill names/descriptions from `.agents/skills/`, `.gbrain/skills/`, and global scope without loading every body. If the installed gstack `investigate` skill exists, use it for evidence gathering. If `plan-eng-review` exists, use it to challenge architecture and test planning. Do not invoke unrelated skills.
3. Inspect Git state, actual source files, manifests, assets, tests, dependency files, migrations, environment templates, and CI. Never print secret values.
4. Distinguish: production-ready, partial, mock/demo, documentation-only, missing, conflicting.
5. Verify asset counts and record paths/baseline hashes or manifest versions. Resolve the 50-vs-60 audio discrepancy from files; if binary audio is absent, record a blocker rather than guessing.
6. Create/update:
   - `docs/ops/REPO_AUDIT.md`
   - `docs/ops/IMPLEMENTATION_PLAN.md`
   - `docs/ops/STATUS.md`
   - `docs/ops/progress.json`
   - material ADRs in `DECISIONS.md`
7. Do not write application code, install a production dependency, migrate a persistent database, deploy, or modify `reference/`.
8. Stop for one human approval of the implementation plan.

Report only: inventory result; critical gaps; architecture recommendation; test strategy; files written; decision requested.
