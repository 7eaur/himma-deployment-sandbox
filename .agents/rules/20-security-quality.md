# Security and quality gates

## Child-data protection

- Use pseudonymous student codes and minimal profile data.
- Encrypt transport with HTTPS; hash researcher passwords using a modern memory-hard password hash; use secure, HTTP-only, same-site session cookies.
- Enforce authorization server-side on every researcher/student resource. Never trust route hiding in the UI.
- Audio and reports are private objects. Use protected access or short-lived signed URLs; never public bucket paths.
- Redact secrets, tokens, student identifiers, transcripts, and recording URLs from logs and screenshots.
- Do not upload code, artifacts, recordings, or datasets to external services or skill-sync systems without explicit approval.

## Reliability

- Use idempotency keys for answer submission, activity completion, recording upload, analysis enqueue, and exports.
- Preserve the last safe checkpoint and resume after interruption without duplicate attempts.
- Model audio as an explicit state machine. Service outages retain the recording as pending; they do not mark academic failure.
- Study settings that affect comparison are versioned and locked after study activation; overrides are audited.
- Migrations must have forward and rollback/restore notes. Backups must be tested by restoration, not merely created.

## Definition of done

A feature is done only when all apply:

- Production code is reachable through the real user flow.
- Persistence and authorization are real; no mock data, hard-coded result, fake timer, or placeholder adapter is presented as complete.
- Unit and integration tests cover domain rules and failure paths.
- Browser E2E verifies the main happy path and at least one failure/recovery path.
- Arabic RTL, keyboard basics, touch targets, responsive layout, and accessible labels are checked.
- Migrations, seed content, API contract, and operational notes are updated.
- Screenshots/recordings or test reports provide evidence.

## Mandatory checks before a stage closes

- Format/lint/type-check.
- Backend unit and integration tests.
- Frontend component tests.
- Contract/schema validation.
- E2E tests in a real browser.
- Dependency and secret scan.
- Search for `TODO`, `FIXME`, `mock`, `demo`, fake delays, disabled tests, and skipped tests in production paths; any intentional occurrence must be documented.
- Independent review against the mapped acceptance IDs.

