# P07 Charter — التحليل الصوتي المساعد الحقيقي

**Branch:** `b04/asr-pipeline`

**Base checkpoint:** `53666a0a67d19586ed1ea792b93d5c102dcb7883` (accepted B03 documentation handoff)

**Roadmap status:** `IN_PROGRESS` for infrastructure only. **P07 may not be accepted** until OI-02 is resolved and a real provider is verified with representative Arabic recordings.

## Source constraints

P07 follows the approved Himma requirements:

- asynchronous processing so the child UI does not freeze;
- private audio storage;
- replaceable ASR adapter inside a worker;
- documented queue states, retries and dead-letter behavior;
- reference-guided alignment against the text shown to the child;
- correct/deletion/insertion/substitution outputs;
- confidence and timing where the approved provider supports them;
- low-confidence cases remain human-review decisions;
- no fake production adapter;
- the confidence threshold is calibrated from representative samples, not chosen theoretically.

## Infrastructure slice allowed before recordings/provider approval

This branch may prepare provider-neutral infrastructure without claiming ASR completion:

1. durable speech-analysis job and result schema;
2. reversible Alembic migration;
3. provider Protocol/Adapter boundary that fails closed when unconfigured;
4. DB-backed asynchronous worker and queue discovery;
5. retry/backoff/dead-letter states;
6. reference-guided Arabic word alignment;
7. researcher queue/status/retry API;
8. tests proving no provider => no fake analysis and no academic score mutation;
9. calibration gate that keeps results in human review until a real threshold/version is configured.

## Explicitly blocked until sample recordings arrive

- selecting/approving the production ASR provider;
- accepting vendor contract/privacy/cost/recording-transfer policy (OI-02);
- measuring Arabic child-reading accuracy;
- deciding a production confidence threshold;
- validating provider word timestamps/confidence on Himma material;
- enabling any automatic academic acceptance based on ASR;
- pronunciation/phoneme/haraka scoring beyond evidence proven by calibration.

## Gate to close P07

P07 can move to `READY_FOR_GATE` only after all of the following are true:

- real provider adapter, no production fake/mock;
- representative recordings evaluated against known reference texts;
- documented provider/model/version/privacy/retention/cost decision;
- calibrated confidence policy with human fallback;
- integration tests through private MinIO audio -> worker -> provider -> alignment -> persisted result;
- deletion/insertion/substitution and provider-supported timing/confidence verified;
- failure/retry/dead-letter behavior verified;
- researcher can inspect the machine result and retain manual authority;
- backend/frontend/integration CI green with evidence.

## Non-goals

- P08 reporting/export;
- final deployment/release hardening;
- diagnosing a child or inferring unsupported pronunciation deficits;
- changing accepted B03 adaptive rules.
