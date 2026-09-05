# Himma Deployment Sandbox Source

This sandbox `main` mirrors the current approved development state from:

- Source repository: `7eaur/himma-`
- Source branch: `recovery/ui-media-admin-overhaul`
- Source commit: `e1cb0bb3ec10087a4032d189cf1d2bbf54c47163`
- Source Quality Gate: GitHub Actions run `33980741084` — SUCCESS
- Synced on: 2026-09-05

Sandbox-only deployment integration files are intentionally retained:

- `deploy/railway-api.Dockerfile`
- `apps/web/.env.production`
- `DEPLOYMENT_ARCHITECTURE.md`
- `DEPLOYMENT_STATUS.md`
- `ENVIRONMENT_VARIABLES.md`
- `.github/workflows/` temporarily retained from the sandbox because the Actions token cannot rewrite workflow files during the mirror job; workflow parity is reconciled separately through the GitHub connector.

The previous sandbox main is preserved at branch `archive/pre-official-sync-2026-09-05`.
