# HIMMA MASTER CONTINUITY HANDOFF — 2026-09-05

> هذا هو مرجع الاستمرارية الرئيسي لمنصة **هِمّة | HIMMA** بعد إغلاق برنامج Recovery. لا تبدأ من Phase F ولا تعيد اكتشاف المراحل A–I من الصفر. اقرأ الحالة والأدلة الحالية ثم تابع فقط من قرار مالك المشروع التالي.

---

# 0) نقطة الاستئناف الحالية

**المستودع:** `7eaur/himma-`  
**الفرع:** `recovery/ui-media-admin-overhaul`  
**الحالة:** `RECOVERY A–I CLOSED — READY_FOR_USER_DECISION`

مرشح التنفيذ النهائي المثبت:

`976b7c2ed8b9c6f1535a22a0b3a94b2c233f75eb`

جميع البوابات الرئيسية نجحت على **هذا SHA نفسه**:

- Quality Gate run `33979846641` — SUCCESS.
- M04 Responsive Visual Gate run `33979846639` — SUCCESS.
- M09 Release Readiness Gate run `33979846640` — SUCCESS.

أي HEAD أحدث بعد ذلك قد يكون توثيقًا فقط. لا تستبدل المرشح التنفيذي المثبت بdocs-only SHA، ولا تعتبر أي تغيير تنفيذي لاحق PASS قبل دورة exact-SHA جديدة.

لم يتم Merge أو Release أو Deploy.

---

# 1) ملفات البداية الإلزامية

في محادثة جديدة، اقرأ بالترتيب:

1. `AGENTS.md`
2. `.agents/rules/00-himma-core.md`
3. `.agents/rules/10-delivery-protocol.md`
4. `.agents/rules/20-security-quality.md`
5. `docs/specs/SOURCE_OF_TRUTH.md`
6. `docs/specs/ACCEPTANCE_MATRIX.md`
7. `docs/ops/STATUS.md`
8. `docs/ops/progress.json`
9. `docs/ops/EVIDENCE_INDEX.md`
10. `docs/ops/HIMMA_PHASE_F_I_CLOSURE_2026-09-05_AR.md`
11. `docs/ops/DECISIONS.md`
12. `docs/ops/OPEN_ITEMS.md`
13. `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`
14. هذا الملف.

ثم اجلب HEAD الحالي من GitHub قبل أي write.

---

# 2) تعريف المشروع والمسار الحالي

هِمّة منصة تعليمية عربية لطلاب الصف الثالث ممن لديهم صعوبات في القراءة.

المسار الأساسي:

`دخول بكود -> اختبار قبلي -> مراجعة التسجيلات -> تصنيف -> أنشطة المستوى -> تقوية موجهة -> متابعة تكيفية -> إكمال L3 -> اختبار بعدي -> تقارير المشرف`

الأرقام الحالية:

- الأصل الأكاديمي المعتمد: **105** عناصر.
- Pretest: **30**.
- Posttest: **30**.
- Runtime total: **125**.
- Learning runtime: **65**.
- Reinforcement total: **35**.
- Skills: **44**.
- Projection contract: `structured_db_runtime_v1`.

المعمارية التنفيذية:

`approved_versioned_source -> deterministic_structured_projection -> postgres_runtime -> structured_api -> deterministic_renderer`

---

# 3) قرار التوزيع القبلي المعتمد — ADR-014

بعد اكتمال الاختبار القبلي:

- score `<50` -> L1.
- `50 <= score < 80` -> L2.
- `80 <= score <= 100` -> L3.

مهم:

- بوابة readiness القديمة `12/20` **ملغاة من قرار التوزيع النشط**.
- البوابات الرقمية الإضافية القديمة لـL3 **ملغاة من قرار التوزيع النشط**.
- الدرجات الدقيقة تجمع أولًا، ثم تقرّب النتيجة النهائية مرة واحدة لحماية حدود 50 و80.

---

# 4) عقد التكيف V4

## Activity outcome

- `>=80` -> pass.
- `70..<80` -> guided retry.
- `<70` -> targeted reinforcement.

## L1/L2 early promotion

لا ترقية إلا مع تحقق الجميع:

- 6 Core على الأقل.
- mastery >=85.
- critical skill coverage مكتملة.
- critical skill floor >=70.
- لا unresolved reinforcement blocker.
- لا pending audio/supervisor review blocker.
- ترقية مستوى واحد فقط.

لا يوجد automatic demotion.

## L3

- لا Journey completion قبل إكمال 10 Core.
- لا L4.

## Mastery evidence

أحدث ثلاثة أدلة Core صالحة من الجلسة النشطة فقط تدخل القرار، بأوزان:

`50 / 30 / 20` من الأحدث إلى الأقدم.

## Reinforcement

- targeted only.
- same-level approved candidates only.
- no random fallback.
- no cross-level fallback.
- عند فجوة الربط يبقى المسار fail-safe ويحتاج اختيار المشرف المعتمد بدل اختراع محتوى.

---

# 5) عقد الصوت الحالي

## Static approved audio

- Approved IDs: **54**.
- WAV: **54**.
- MP3: **54**.
- Required static gaps: **0**.

الأصول المصححة تشمل:

- `LET-01` = `مَ` مع stable runtime ID.
- `SYL-13` = `سَا`.
- `WRD-29` = `موز`.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.

OI-10 مغلق ولا يجوز إعادة وصف هذه الأصول بأنها مفقودة.

## Student recording authority

العقد الحالي:

`record -> persist/upload -> supervisor review -> graded / rerecord_required -> continue`

- `uploaded` = انتظار مراجعة فقط.
- `uploaded` لا يعني success/completion/mastery.
- `rerecord_required` يعيد نفس موضع القراءة.
- `graded` فقط يسمح باستكمال الدليل حسب قرار المراجعة.
- المشرف البشري هو السلطة الأكاديمية الحالية.
- لا يوجد learner audio bypass نشط.
- لا fake ASR score.

المرجع:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

---

# 6) ASR المستقبلي

المعمارية المستهدفة عند اعتماد P07 الآلي مستقبلًا:

**Reference-Guided Arabic Reading Analysis**

`ASR -> reference alignment -> Correct/Deletion/Insertion/Substitution -> phonemic helper evidence`

لكن هذا ليس جزءًا من السلطة الأكاديمية الحالية، ولا يوقف إغلاق Recovery.

لا تضف provider إنتاجيًا أو confidence threshold أو automatic academic decision قبل إغلاق OI-02/OI-03 واعتماد الخصوصية والمعايرة.

---

# 7) التقارير وإعادة الاختبارات

## Reports

التقارير read models فقط. لا يجوز أن تنشئ أو تعدل:

- mastery.
- activity completion.
- student level.
- academic evidence.
- official reporting attempt.

يوجد regression يثبت أن report reads/exports لا تغير الحالة الأكاديمية.

## Retakes

- canonical assessment completion فقط.
- المحاولات القديمة محفوظة.
- exactly one `official_for_reporting` بعد اكتمال المحاولة الرسمية الأحدث.
- لا حذف للتاريخ لتبسيط السيناريو.

---

# 8) الأمان والجودة بعد Recovery

تم استبدال `python-jose` بـ:

`joserfc==1.7.5`

وتثبيت:

- explicit HS256 allowlist.
- expiry validation.
- tampered-token rejection.
- malformed-token rejection.
- non-allowlisted algorithm rejection.

Quality Gate الحالي يشمل أيضًا:

- `pip-audit`.
- `npm audit --audit-level=high`.
- pinned/checksummed Gitleaks.
- TODO/FIXME/mock/demo production guard.
- hard-coded fake-delay guard.
- disabled/skipped test guard.

على المرشح النهائي:

- Python dependency audit: no known vulnerabilities.
- npm audit: no known vulnerabilities عند threshold الحالي.
- Gitleaks: PASS.
- Backend: **755 passed**، وتحذاران deprecation من طبقة الاختبار فقط.
- Frontend/Build/Integration/Playwright: SUCCESS.

---

# 9) حالة مراحل Recovery

- A — CLOSED.
- B — CLOSED.
- C — CLOSED.
- D — CLOSED.
- E — CLOSED.
- F — CLOSED.
- G — CLOSED.
- H — CLOSED CONSERVATIVELY.
- I — CLOSED EXACT-SHA GREEN.

Phase H اتبع قاعدة proven-dead only. حُذف diagnostic E2E المتقاعد `apps/web/tests/e2e/debug-login.spec.ts`، بينما بقيت إشارات التوافق التاريخي اللازمة لقراءة السجلات القديمة. لا تحذف legacy markers لمجرد الاسم.

تقرير الإغلاق:

`docs/ops/HIMMA_PHASE_F_I_CLOSURE_2026-09-05_AR.md`

فهرس الأدلة:

`docs/ops/EVIDENCE_INDEX.md`

---

# 10) البنود التي ما تزال خارج Recovery

ارجع إلى `docs/ops/OPEN_ITEMS.md`، وبالأخص:

- OI-02: عقد مزود/وحدة ASR الحقيقي إذا تقرر P07 الآلي.
- OI-03: confidence threshold وإصدار المعايرة.
- OI-04: مدة التدخل وعدد/مدة الجلسات قبل الدراسة.
- OI-05: retention policy لتسجيلات الأطفال — يوقف الإنتاج ببيانات أطفال حقيقية.
- OI-06: domain/hosting — يوقف deployment.
- OI-07: بيانات/شعار الجهة المشرفة قبل اعتماد التقارير النهائية.
- OI-08: credential rotation لأي قيم حقيقية ربما استخدمت تاريخيًا — يوقف production/deploy حتى الإتمام.

---

# 11) قواعد GitHub والتنفيذ التي لا تتغير

- لا Docker محليًا.
- لا force push.
- لا reset/clean مدمر.
- لا حذف history أو بيانات أكاديمية محفوظة.
- لا تعديل accepted stage branches مباشرة دون قرار واضح.
- قبل **كل write**: fetch branch HEAD مجددًا.
- إذا تحرك HEAD بشكل غير متوقع، افحص الفرق قبل الكتابة.
- PASS التنفيذي يتطلب exact-SHA evidence.
- docs-only HEAD لا يلغي executable evidence المثبت.
- لا Merge/Release/Deploy بدون موافقة المستخدم الصريحة.

---

# 12) نقطة القرار التالية

Recovery نفسه **منتهٍ فنيًا**.

لا تبدأ Phase F أو G أو H أو I مرة أخرى.

الخيارات التالية فقط حسب قرار مالك المشروع:

1. تجهيز/اعتماد خطوة التكامل أو الدمج، مع بقاء merge نفسه مشروطًا بموافقته الصريحة.
2. إغلاق متطلبات الإنتاج الخارجية OI-04/OI-05/OI-06/OI-07/OI-08.
3. بدء P07 التحليل الصوتي الآلي بعد اعتماد OI-02/OI-03 ومدخلات الخصوصية/المعايرة.

إذا لم يصدر قرار واضح، توقف عند `READY_FOR_USER_DECISION` ولا تنفذ Merge أو Release أو Deploy تلقائيًا.