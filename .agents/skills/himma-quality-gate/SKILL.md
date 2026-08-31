---
name: himma-quality-gate
description: Verify a Himma stage with adversarial acceptance checks, automated tests, real-browser evidence, privacy/security review, mock detection, and a strict PASS/FAIL report.
---

# Himma quality gate

## Evidence order

1. Reproduce behavior through the public UI/API.
2. Run automated tests independently.
3. Inspect implementation and migration only after observing behavior.
4. Compare results with the mapped acceptance criteria and authoritative content.

## Required adversarial checks

- Student cannot access another student or researcher endpoints.
- Researcher-only actions reject student sessions.
- Boundary scores and weighted adaptation decisions match exact rules.
- Invalid/low-confidence audio never changes academic state.
- Repeated submits/uploads/queue deliveries do not duplicate records.
- Browser refresh, connection loss, and worker outage preserve recoverable state.
- Reports match database/board values and respect authorization.
- Child identifiers, transcripts, recording URLs, and secrets do not appear in public logs or artifacts.
- Mobile RTL, Arabic shaping/diacritics, touch targets, keyboard basics, and reduced motion are acceptable.

## Verdict

- PASS requires all mapped acceptance criteria and mandatory checks to pass with evidence.
- FAIL for any untested material path, disabled test, production mock, critical security/privacy issue, or unreconciled data mismatch.
- Do not lower an expectation or edit a test merely to obtain PASS.

