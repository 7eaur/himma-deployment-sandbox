# Delivery protocol

## Read small, then drill down

At the start of a session read only: `STATUS.md`, `progress.json`, the current roadmap stage, relevant acceptance rows, and changed files. Open large source references only for the current requirement. Never re-summarize the entire project in chat.

## Stage discipline

1. Work on one roadmap stage and one vertical slice at a time.
2. Before coding, record the slice, affected acceptance IDs, plan, migration impact, and tests in `STATUS.md`.
3. Implement the smallest complete production slice across UI, API, database, audit, and tests.
4. Run targeted tests first, then the full stage gate.
5. Fix failures within the stage. Do not move failures to a future stage unless the blocker is external and explicitly recorded.
6. Update `STATUS.md`, `progress.json`, `DECISIONS.md`, and `OPEN_ITEMS.md` before reporting.
7. A stage is complete only after `/himma-gate` evidence and a green commit.

## Human checkpoints

Pause only for: approval of phase-0 architecture; a scope or research-rule change; secrets/accounts; irreversible deletion; production deployment; migration with data-loss risk; external publication; or a real contradiction that changes behavior.

Within an approved stage, proceed without asking for approval for ordinary file edits, dependency installation, migrations against disposable development data, tests, linting, local browser verification, or bug fixes.

## Communication budget

- Use task artifacts and repository files for progress, not repeated chat narration.
- Chat update only when the plan is ready, a blocker appears, a gate fails materially, or the stage completes.
- Completion report fields: Done; Acceptance IDs; Tests; Evidence; Risks/blockers; Next.
- Do not paste raw logs. Quote only the failing line and point to the artifact.

## Git safety

- Keep the default branch green. If this delivery was extracted without Git metadata, run `scripts/init-git.sh` once before creating a stage branch.
- Use one branch per stage (`stage/00-audit`, `stage/01-foundation`, etc.).
- Commit coherent vertical slices. The approved static instructional assets in `assets/audio/HIMMA_AUDIO_V1/` are repository assets and may be committed. Never commit child recordings, `.env`, credentials, real child data, database dumps, generated caches, or dependency directories.
- Inspect existing user changes before editing and never discard unrelated work.
