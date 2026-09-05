# EVIDENCE INDEX — Himma Recovery

**Updated:** 2026-09-05  
**Branch:** `recovery/ui-media-admin-overhaul`  
**Final executable candidate:** `976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb`

هذه الصفحة هي فهرس مختصر للدليل النهائي. لا تستبدل المواصفات أو سجل القرارات، ولا تعني أن الفرع دُمج أو نُشر.

## Exact-SHA release-readiness evidence

| Evidence | Identifier | Status |
|---|---|---|
| Quality Gate | GitHub Actions run `33979846641` | SUCCESS |
| Responsive Visual Gate | GitHub Actions run `33979846639` | SUCCESS |
| Release Readiness Gate | GitHub Actions run `33979846640` | SUCCESS |

جميعها تخص SHA واحدًا: `976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb`.

## Quality evidence on the final candidate

- Backend: **755 passed**؛ تحذيران deprecation غير وظيفيين فقط.
- Approved catalog validation: **PASS — 105 original items, 44 canonical skills, 0 explicit V1 media gaps**.
- Alembic: upgrade/downgrade/upgrade ناجح، ثم `alembic check` بلا drift جديد.
- Seed idempotency: البذر الثاني لم ينشئ عناصر أو مهارات إضافية.
- Frontend: TypeScript + ESLint + unit tests + Next.js production build = SUCCESS.
- Integration: PostgreSQL + Redis + pinned MinIO + FastAPI + Next.js + Playwright E2E = SUCCESS.
- Python dependency audit = no known vulnerabilities.
- npm audit = no known vulnerabilities at configured high threshold.
- Gitleaks current-tree scan = SUCCESS مع allowlist ضيق لمعرّفات catalog `stable_key` الحتمية فقط.
- Production placeholder guard = SUCCESS.
- Disabled/skipped test guard = SUCCESS.

## Academic / adaptive authority

- `docs/ops/DECISIONS.md` — خصوصًا **ADR-014** للتوزيع القبلي والتكيف V4.
- `docs/specs/SOURCE_OF_TRUTH.md` — خريطة المصدر التنفيذي الحالية.
- `docs/specs/ACCEPTANCE_MATRIX.md` — معايير القبول المتوافقة مع ADR-014.
- `services/api/placement_scoring.py` — التوزيع `<50 / 50..<80 / 80..100` مع حماية دقة الحدود.
- `services/api/learning_state_machine.py` و`services/api/adaptation.py` — 80/70 للنشاط، و6 Core + 85 mastery + 70 critical floor للترقية المبكرة، بدون خفض تلقائي.

## Audio authority

- `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`
- الحزمة الثابتة: 54 approved IDs، و54 WAV، و54 MP3.
- الطالب: `uploaded -> supervisor review -> graded / rerecord_required`.
- لا يوجد bypass نشط لتسجيل الطالب ولا score آلي مزيف.
- ASR الحقيقي مستقبل مستقل ولا يغيّر سلطة المراجعة البشرية الحالية دون قرار واعتماد جديد.

## Key regression evidence

- `services/api/test_assessment_pending_audio_navigation.py`
- `services/api/test_profile_audio_review_state.py`
- `services/api/test_manual_override_session_integrity.py`
- `services/api/test_placement_scoring.py`
- `services/api/test_student_adaptation_scenario_matrix.py`
- `services/api/test_jwt_security.py`
- `services/api/test_readiness.py`
- `services/api/test_m09_full_single_candidate_journey.py`
- `apps/web/tests/e2e/vertical-slice.spec.ts`
- `apps/web/tests/e2e/accessibility-integration.spec.ts`
- `apps/web/tests/e2e/media-fidelity.spec.ts`
- `apps/web/tests/e2e/question-experience.spec.ts`
- `apps/web/tests/e2e/admin-responsive.spec.ts`

## Closure records

- `docs/ops/HIMMA_PHASE_F_I_CLOSURE_2026-09-05_AR.md` — الإغلاق التنفيذي للمراحل F–I.
- `docs/ops/STATUS.md` — الحالة الحالية المختصرة.
- `docs/ops/progress.json` — الحالة المقروءة آليًا.
- `docs/ops/RESUME_HERE.md` — نقطة الاستئناف التالية.
- `docs/ops/OPEN_ITEMS.md` — البنود الخارجية/الإنتاجية التي لم تُغلق ضمن Recovery.

## Current boundary

Recovery A–I مغلق فنيًا على المرشح المثبت. الحالة التالية هي `READY_FOR_USER_DECISION`.

لا يوجد حتى الآن:

- Merge إلى الفرع الأساسي.
- Release إنتاجي.
- Deploy.

أي خطوة من هذه تحتاج اعتمادًا صريحًا من مالك المشروع.