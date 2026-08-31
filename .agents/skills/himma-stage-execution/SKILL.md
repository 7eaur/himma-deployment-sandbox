---
name: himma-stage-execution
description: Implement one approved Himma roadmap stage as small production vertical slices with durable status, tests, migrations, content validation, commits, and concise evidence.
---

# Stage execution

## Before coding

- Confirm the active stage and approved plan.
- Map the slice to acceptance IDs and user scenarios.
- Identify data migration, privacy, failure, and rollback impact.
- Make a concrete test list.

## Build loop

1. Write or update a failing test/specification for the behavior.
2. Implement the smallest complete domain behavior.
3. Expose it through API and UI only as needed for the slice.
4. Add audit and authorization checks.
5. Validate Arabic content/asset IDs and seed idempotency.
6. Run targeted tests, then type/lint/contract checks.
7. Verify the user flow in a real browser when UI is affected.
8. Update durable status and commit only when green.

## Stop conditions

- A destructive or irreversible action.
- A required external credential/account.
- A contradiction in research logic.
- A requested scope expansion.
- A data migration that may lose persistent data.

Ordinary errors are not stop conditions; diagnose, fix, retest, and continue.

