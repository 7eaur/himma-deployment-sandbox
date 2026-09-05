# STATUS — Himma Platform

**Last updated:** 2026-09-05  
**Repository:** `7eaur/himma-`  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Program:** Full Maintenance / Recovery  
**Current state:** `RECOVERY A–I CLOSED — READY_FOR_USER_DECISION`

## Final executable candidate

`976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb`

جميع بوابات الإغلاق المطلوبة نجحت على **هذا SHA نفسه**:

- Himma CI — Quality Gate: run `33979846641` — **SUCCESS**.
- Himma M04 — Responsive Visual Gate: run `33979846639` — **SUCCESS**.
- Himma M09 — Release Readiness Gate: run `33979846640` — **SUCCESS**.

أي commits لاحقة لتحديث وثائق التشغيل هي docs-only ولا تستبدل مرشح التنفيذ المثبت أعلاه. إذا تغير الكود التنفيذي بعده، يجب اختيار SHA تنفيذي جديد وإعادة الإثبات على نفس SHA قبل إعلان PASS جديد.

## Final quality evidence

على المرشح النهائي:

- Backend: **755 passed**؛ تحذيران deprecation من طبقة الاختبار فقط.
- Approved content catalog: **PASS — 105 original items, 44 canonical skills, 0 explicit V1 media gaps**.
- Alembic `upgrade -> downgrade -> upgrade`: SUCCESS.
- Alembic model drift: لا توجد upgrade operations جديدة.
- Seed idempotency: SUCCESS.
- TypeScript: SUCCESS.
- ESLint: SUCCESS.
- Frontend unit tests: SUCCESS.
- Next.js production build: SUCCESS.
- PostgreSQL + Redis + pinned MinIO + FastAPI + Next.js integration: SUCCESS.
- Playwright E2E: SUCCESS.
- Python dependency audit: no known vulnerabilities.
- npm audit عند مستوى high: no known vulnerabilities.
- Gitleaks current-tree scan: SUCCESS.
- Production placeholder/fake-delay guard: SUCCESS.
- Disabled/skipped test guard: SUCCESS.
- M09 live readiness + backup/restore PostgreSQL/Object Storage: SUCCESS.

## Phase status

- Phase A — Audio Review Vertical Slice Recovery: **CLOSED**.
- Phase B — Runtime Bypass Closure Audit: **CLOSED**.
- Phase C — Approved Audio Binary Contract: **CLOSED**.
- Phase D — Deterministic Structured Projection: **CLOSED**.
- Phase E — Runtime Readiness Hardening: **CLOSED**.
- Phase F — Student Path Regression Closure: **CLOSED**.
- Phase G — Supervisor Audio/Admin UX Closure: **CLOSED**.
- Phase H — Proven-Dead Legacy Cleanup: **CLOSED CONSERVATIVELY**.
- Phase I — Final Single-Candidate Closure: **CLOSED EXACT-SHA GREEN**.

تفاصيل إغلاق F–I:

`docs/ops/HIMMA_PHASE_F_I_CLOSURE_2026-09-05_AR.md`

فهرس الأدلة:

`docs/ops/EVIDENCE_INDEX.md`

## Active academic contract

### Initial placement — ADR-014

بعد اكتمال الاختبار القبلي:

- أقل من 50% → المستوى الأول.
- من 50% إلى أقل من 80% → المستوى الثاني.
- من 80% إلى 100% → المستوى الثالث.

بوابة readiness القديمة `12/20` والبوابات الرقمية الإضافية التجريبية لـL3 **ليست جزءًا من قرار التوزيع النشط**.

### Learning/adaptation V4

- Activity `>=80` → نجاح.
- Activity `70..<80` → إعادة موجهة.
- Activity `<70` → تقوية موجهة.
- L1/L2 early promotion: >=6 Core + mastery >=85 + critical coverage + critical floor >=70 + no unresolved reinforcement/audio/supervisor blocker.
- الترقية مستوى واحد فقط.
- لا يوجد خفض تلقائي.
- L3 لا يكتمل إلا بعد 10 Core، ولا يوجد L4.
- أحدث ثلاثة أدلة Core صالحة من الجلسة النشطة فقط تدخل قرار mastery بأوزان 50/30/20.

## Audio contract

Static approved audio:

- Approved IDs: **54**.
- WAV: **54**.
- MP3: **54**.
- Required static audio gaps: **0**.

Current student-reading authority:

`record -> persist/upload -> supervisor review -> graded / rerecord_required -> continue`

- `uploaded` = انتظار مراجعة، وليس نجاحًا أو درجة أو إتقانًا.
- `rerecord_required` = إعادة فتح نفس موضع القراءة.
- `graded` فقط يسمح باستكمال الدليل الأكاديمي.
- لا يوجد learner audio bypass نشط.
- ASR الحقيقي/التلقائي ما يزال مسارًا مستقبليًا مستقلًا ولا يملك سلطة أكاديمية حاليًا.

Authoritative audio contract:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

## Architecture/runtime truth

- Original approved content: 105 items.
- Runtime total: 125.
- Learning runtime: 65 items.
- Reinforcement total: 35.
- Pretest: 30.
- Posttest: 30.
- Skills: 44.
- Projection contract: `structured_db_runtime_v1`.
- Runtime architecture: `approved_versioned_source -> deterministic_structured_projection -> postgres_runtime -> structured_api -> deterministic_renderer`.
- Reports are descriptive read models and do not manufacture mastery evidence.
- Seeds remain version-aware, idempotent and non-destructive.

## Security hardening completed

- Replaced vulnerable legacy `python-jose` dependency with maintained `joserfc==1.7.5`.
- JWT signing/validation uses explicit HS256 allowlisting and expiry validation.
- Tampered, malformed and non-allowlisted-algorithm tokens are regression tested.
- CI now includes Python and Node dependency audits, Gitleaks, unfinished production marker guard, fake-delay guard and skipped-test guard.
- Deterministic catalog `stable_key` UUIDs are the only narrow Gitleaks path/rule exception introduced for the known false-positive class.

## Remaining external / production gates

Recovery is closed, but production is not automatically authorized. `docs/ops/OPEN_ITEMS.md` remains authoritative for unresolved external items, especially:

- OI-02 / OI-03: production ASR provider and calibration before automatic speech decisions.
- OI-04: intervention/session duration before study activation.
- OI-05: child-recording retention policy — blocks real-child production data.
- OI-06: domain/hosting — blocks deployment.
- OI-07: supervising organization details/logo before final report signoff.
- OI-08: rotate any real credentials that may have appeared historically — blocks production/deployment.

OI-10 is **CLOSED**: approved `WRD-29`, `SYL-13`, `INS-01`, and `INS-02` are present in the active audio contract.

## Decision boundary

No merge, release, or deployment has been performed.

The next action requires explicit owner authorization. Until then, preserve `976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb` as the final executable Recovery evidence candidate.