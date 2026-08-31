# هِمّة — Master Continuity Handoff — تحديث شامل 2026-08-28

> هذا الملف هو المرجع التنفيذي الأشمل لاستئناف المشروع في محادثة/مودل جديد. ابدأ أيضًا من `docs/handoff/READ_FIRST_2026-08-28_AR.md`. عند أي تعارض: **المصدر الأكاديمي المعتمد > القرارات الموثقة الأحدث > الكود الحالي > CI الفعلي > هذا النص التاريخي**. وافحص HEAD قبل العمل دائمًا.

---

# 1) هوية المشروع والهدف

هِمّة منصة تعليمية عربية RTL موجهة لطلاب الصف الثالث ممن لديهم صعوبات في القراءة. المسار المنتجّي المستهدف:

`دخول بكود → اختبار قبلي → تحليل/تصنيف نقطة البداية → أنشطة المستوى → تقوية موجهة عند الضعف → صعود للمستوى التالي → L3 → اختبار بعدي → تقارير المشرف`

المستخدم يريد منتجًا حقيقيًا أنيقًا وسلسًا، لا مجرد صفحات تعمل تقنيًا. يجب الحكم على السيناريو، التعليمات، الرسائل، سهولة التنقل، الإدارة، responsive، accessibility، والاتساق البصري.

---

# 2) Git / Branch / قواعد التنفيذ

المستودع: `7eaur/himma-`

الفرع التنفيذي الحالي:

`recovery/ui-media-admin-overhaul`

آخر Implementation HEAD قبل دفعة التوثيق الحالية:

`98fdc638737bdb8ab9be4937cff6155865998d1f`

لا تعدّل الفروع الأساسية. لا تعمل Reset/Hard rollback لإخفاء Regression. لا تنشئ repo/project/folder بديلًا عند الاستئناف. لا تحذف تغييرات موجودة لمجرد أن اختبارًا فشل.

**قيد محلي:** لا Docker في تطوير هِمّة المحلي. GitHub Actions قد يستخدم containers داخل runner؛ هذا لا يغير القيد المحلي.

---

# 3) الحالة التنفيذية المختصرة

- M00 — Restore Green Baseline: CLOSED.
- M01 — Placement Scoring & Gates: CLOSED.
- M02 — Adaptation State Machine: CLOSED.
- M03 — Reinforcement Mapping/Content: IMPLEMENTED، مع 3 فجوات محتوى معلنة.
- M04 — Student Product UI: REBUILT / accepted baseline.
- M05 — Supervisor Product UX: REBUILT / accepted baseline.
- **M06 — Responsive/Accessibility/Design QA: ACTIVE.**
- M07 — Research Reports: PENDING.
- M08 — Real Speech Analysis: PENDING / external gates.
- M09 — Release/UAT: PENDING.

---

# 4) آخر CI حقيقي ونقطة الاستئناف

على Implementation HEAD `98fdc638...`:

## Responsive Visual Gate

Run #18 / ID `33202256450`: **SUCCESS**.

## Main Quality Gate

Run #298 / ID `33202256449`:

- Backend: SUCCESS.
- Frontend: SUCCESS.
- Integration/Playwright: FAILURE.

الفشل الحالي الوحيد:

`apps/web/tests/e2e/accessibility-integration.spec.ts`

سيناريو:

`mobile supervisor navigation keeps touch targets and layout intact`

Log يثبت:

- dialog `قائمة لوحة المشرف` visible.
- الاختبار يبحث عن `a.sidebar-nav-item` داخل dialog.
- العنصر بهذا selector غير موجود.
- الفشل يحدث قبل قياس height >=44px.
- بقية اختبارات M06 نجحت.
- Vertical Slice الكامل نجح.

**أول مهمة:** أصلح contract بين test selector والـmobile nav markup بطريقة semantic/stable، مع الحفاظ على شرط touch target >=44px وعدم خفض الاختبار، ثم أعد Main Quality Gate حتى يصبح كاملًا أخضر.

---

# 5) المحتوى الأكاديمي الأصلي

المحتوى الأصلي المعتمد لا يُعدل بصمت:

- 30 سؤال اختبار قبلي.
- 30 سؤال اختبار بعدي.
- 3 مستويات.
- لكل مستوى 10 أنشطة أساسية.
- لكل مستوى 5 تقويات أصلية.
- 30 core + 15 reinforcement.
- الإجمالي الأصلي: **105 عنصرًا**.
- عدد المهارات في الكتالوج: **44**.

Full runtime seed بعد M03:

- baseline 105.
- +18 reinforcement additions.
- total = **123**.
- reinforcement total = **33**.

المراجع:

- `المحتوى المعتمد من العميل.txt` / المصدر المعتمد للمحتوى.
- `docs/specs/REINFORCEMENT_CONTENT_ADDITIONS_2026-08-28_AR.md`.

---

# 6) Placement — العقد الحالي

الاختبار القبلي يحدد **نقطة البداية فقط**.

المسارات:

- placement L1: `Pretest → L1 → L2 → L3 → Posttest`.
- placement L2: `Pretest → L2 → L3 → Posttest`.
- placement L3: `Pretest → L3 → Posttest`.

Scoring المعتمد في الصيانة:

- readiness = 20.
- word building/reading = 40.
- fluency/comprehension = 40.
- readiness أقل من `12/20` يفرض L1 حتى لو total أعلى.

L3 لا يجب أن يعتمد على total >=80 وحده إذا كانت بوابة دقة القراءة/النص مطلوبة. لا تختلق threshold صوتي غير معتمد. عند غياب evidence لازم بسبب TEMP Audio Skip، استخدم provisional/neutral contract بدل تحويل الغياب إلى خطأ.

---

# 7) Learning Adaptation — العقد الحالي

Performance bands:

- `>=80%` = Pass.
- `70–<80%` = Guided Retry للجزء الضعيف/غير الصحيح.
- `<70%` = Weakness event + targeted reinforcement candidate.

Skill mastery profile:

- آخر 3 محاولات صالحة: 50% / 30% / 20%.
- هذا trend/evidence وليس سببًا لتخطي بقية المستوى.

Level completion:

- يجب إكمال 10/10 core activities.
- لا unresolved reinforcement gap.
- لا detected weakness غير معالج ضمن العقد.
- Posttest لا يفتح بعد L1 أو L2 فقط.

### Automatic Demotion

هذا القرار **غير محسوم نهائيًا**. الوثائق القديمة تسمح بالخفض بعد قرارين منخفضين، بينما مراجعة المنتج الجديدة تفضل عدم الهبوط التلقائي بعد placement، واستخدام support داخل المستوى + supervisor override للحالات الاستثنائية. لا تحذف أو تعتمد demotion صامتًا قبل قرار نهائي.

---

# 8) M03 Reinforcement — ما نُفذ

تم الانتقال من exact `skill_id` فقط إلى:

`Skill → Skill Family → Approved Reinforcement Candidates`

ثوابت:

- no random reinforcement.
- no cross-level random fallback.
- reinforcement ليست مستوى رابعًا.
- التقوية تعالج weakness ثم يرجع الطالب إلى core verification.

الدورة:

`Weakness → Reinforcement → Complete → Return to Core → Verification → Continue`

إذا استمر الضعف بعد محاولات bounded: supervisor support required بدل loop لا نهائي.

Database/runtime:

- durable `ReinforcementCycle`.
- migration: `0008_reinforcement_cycles`.
- `seed_all.py` يزرع full catalog idempotently.

## 18 إضافة معتمدة

- L1: +7.
- L2: +6.
- L3: +5.

## 3 فجوات باقية — لا تختلق لها علاجًا

1. L2 — قراءة كلمات السكون (`sukoon_word_reading`).
2. L3 — الفهم المباشر (`literal_comprehension`).
3. L3 — بناء الجملة (`sentence_building`).

حتى اعتماد علاج: Safe Hold + supervisor path موثق.

مرجع: `docs/ops/M03_RESIDUAL_CONTENT_GAPS_2026-08-28_AR.md`.

---

# 9) TEMP Audio Skip

Feature flag:

`HIMMA_TEMP_AUDIO_SKIP=true`

الغرض: تجربة المنصة بينما التسجيل/ASR الحقيقي غير جاهز بالكامل.

عند Voice-required task يظهر «تخطي مؤقتًا» مع لغة مناسبة للطالب.

الـskip:

- لا يطلب mic permission.
- لا ينشئ fake audio.
- لا يرفع MinIO.
- لا ينشئ AudioSubmission.
- لا يدخل review queue.
- لا يعطي Correct/Incorrect.
- لا نجوم/Badge.
- لا mastery/weakest_skill/adaptation evidence.
- لا reinforcement بسبب skip.
- في assessment يستبعد من denominator.

إطفاء flag يعيد recording requirement.

---

# 10) Audio Inventory

حزمة الصوت الثابت الحالية:

- 50 أصلًا موجودًا، مع WAV master + MP3 web.
- الفجوتان المؤكدتان فقط: **«موز»** و**«سَا»**.
- target fixed assets = 52.
- «موزة» لا تعوض «موز» إذا النشاط يحتاج الكلمة نفسها.

التقويات الـ18 الجديدة تعيد استخدام الأصوات الحالية ولا تضيف gaps ثابتة أخرى معروفة فوق «سَا» الموجودة أصلًا.

المستخدم سيوفر لاحقًا الصوتين فقط. الصور الناقصة للتقويات ستُولد داخليًا لاحقًا بهوية هِمّة.

مرجع: `docs/specs/AUDIO_INVENTORY_AND_GAPS_2026-08-28_AR.md`.

---

# 11) Real Speech Analysis / ASR

الهدف المعماري:

**Reference-Guided Arabic Reading Analysis**

وليس Whisper-only generic transcription.

البنية الموجودة:

- queue.
- worker.
- retries/dead-letter.
- provider Adapter abstraction.
- reference-guided alignment.
- Correct / Deletion / Insertion / Substitution representation.
- confidence/manual review fallback infrastructure.
- migrations/tests.

غير المنجز:

- real provider selection/connection.
- representative-recording evaluation.
- confidence calibration/version.
- privacy/cost/transfer decision.
- recording retention/deletion policy.

لا تدعِ أن ASR مكتمل.

---

# 12) M04 Student Product UI — ما تغير

المراجعة المنتجية السابقة حكمت أن UI القديمة Functional Recovery Baseline وليست Final Product UI. M04 أعادت بناء منطقة الطالب:

- Learning Stage full-screen باستخدام `100dvh`.
- مساحة أوسع بدل Card صغيرة وسط فراغ كبير.
- character/companion بارزة على desktop بدل أيقونة صغيرة.
- instruction bubble مرتبطة بالمهمة.
- image/text/sequence/build/read/record controls محسنة.
- assessment/pre/post shell أقرب لنفس لغة الأنشطة والتقوية.
- mobile/tablet/desktop breakpoints.
- short-landscape handling.
- focus states + reduced motion.
- result/reward presentation أفضل.

القاعدة: الطفل يجب أن يشعر أنه داخل **جلسة تعليمية** لا يتصفح موقعًا إداريًا.

---

# 13) M05 Supervisor Product UX — ما تغير

أكبر فجوة منتج كانت Admin UI/IA. تم تنفيذ baseline جديد:

## Admin Shell / IA

- فصل desktop sidebar عن mobile navigation بشكل أوضح.
- تنظيم navigation إلى مجموعات منطقية بدل قائمة مسطحة مزدحمة.

## Dashboard

تحول من مجرد أرقام ومساحة تحميل إلى اتجاه Action Center:

- ما يحتاج انتباه المشرف أولًا.
- ثم summary/stats.
- ثم recent students / navigation actions.
- Loading أصبح أقرب لـskeleton بدل فراغ/spinner فقط.

## Student Profile

الصفحة القديمة كانت تجمع الحساب والرمز والتقوية والتكيف والاختبار البعدي والسجل كلها عموديًا.

أصبحت Workspace tabs، منها:

- نظرة عامة.
- المسار والتقدم.
- الاختبارات.
- التسجيلات.
- التقوية والتكيف.
- الحساب.
- السجل.

ويستمر دعم:

- edit name.
- access code copy/regenerate/manual set.
- activate/deactivate.
- posttest access.
- manual adaptation override + reason.
- rewards/stars/badges.
- adaptation decision history.

## Reinforcement Review

أصبح compact alert: «يحتاج قرار تقوية» + «مراجعة القرار»، ثم expandable details/form بدل block ضخم دائم أعلى ملف الطالب.

## Settings

قسمت إلى:

- Account.
- Security.
- Supervisors.

## Test updates

Vertical Slice عُدل ليتبع tabs الجديدة، ونجح في Run #298.

---

# 14) M06 Responsive / Accessibility — المنجز

Commits بارزة:

- `fafbcbc8...` global accessibility motion/focus safeguards.
- `0c974aaf...` load safeguards globally.
- `770df955...` accessible primary/success contrast tokens.
- `225bff55...` responsive accessibility integration gate.
- `76baa3f3...` run accessibility gate with vertical slice.
- `98fdc638...` target visible dashboard heading across responsive layouts.

Checks مضافة/ناجحة حاليًا باستثناء الاختبار الواحد:

- RTL workspace.
- keyboard/focus.
- horizontal overflow safety.
- reduced motion.
- 200% zoom equivalent usability.
- contrast token checks.
- child-facing no implementation vocabulary.

Responsive Visual Gate يغطي:

- 360×800.
- 390×844.
- 768×1024.
- 1024×768.
- 1440×900.

### M06 current failure

Mobile supervisor dialog visible، لكن test selector `a.sidebar-nav-item` لا يطابق العنصر الحقيقي. أصلح selector/markup semantic contract، لا تحذف check ولا تخفض 44px.

---

# 15) M07 — ما سيأتي بعد M06

Research Reports المطلوبة:

- pre/post score comparison.
- absolute improvement.
- percentage improvement حيث mathematically valid.
- skills/errors.
- reading error categories فقط عندما evidence الصوت صالح.
- time/attempts.
- starting/final level.
- reinforcement history.
- individual + aggregate views.
- filters.
- Excel multi-sheet.
- PDF individual + aggregate.
- export audit log.

Gate: UI + Excel + PDF تتفق مع DB.

---

# 16) M08 — شروط قبل Real Speech sign-off

- representative recordings.
- provider decision.
- privacy/cost/transfer.
- confidence calibration.
- retention policy.
- sample accuracy review.
- low-confidence manual review.
- لا claims فونيمية/حركية غير مدعومة.

---

# 17) M09 — Release/UAT

- full UC/E2E scenarios.
- network/microphone/service failure handling.
- security/privacy pass.
- backup + restore drill.
- hosting/domain/HTTPS.
- monitoring/logging.
- synthetic-data UAT أولًا.
- manuals/final handoff.

---

# 18) المنتج — معايير غير قابلة للتنازل

Student:

- RTL عربي واضح.
- مهمة واحدة واضحة في الشاشة.
- الشخصية التعليمية لها وظيفة وليس زينة.
- التعليمات contextual.
- لا مصطلحات تقنية للطفل.
- لا score fake للصوت.
- no horizontal overflow.
- touch targets كبيرة.

Supervisor:

- يعرف «ما الذي يحتاج انتباهي؟» بسرعة.
- navigation وIA منطقية.
- student state مفهومة بلا raw IDs/technical explanation.
- technical details قابلة للتوسع للمشرف لا تملأ الشاشة افتراضيًا.

General:

- Touch >=44px.
- focus visible.
- contrast >=4.5:1 للنص العادي قدر الإمكان ضمن النظام.
- reduced motion.
- keyboard usable.
- 200% zoom.
- screenshot review حقيقي قبل sign-off.

---

# 19) البنية والخدمات

Backend: FastAPI / SQLAlchemy / Alembic / PostgreSQL.  
Storage: MinIO/S3-compatible.  
Queue/support: Redis.  
Frontend: Next.js + React/TS، مع Tailwind/PostCSS وتنسيقات CSS الموجودة.  
Tests: backend pytest + frontend TS/ESLint/unit/build + Playwright integration/visual gates.

لا تستبدل PostgreSQL بـSQLite كحل إنتاجي، ولا MinIO بstorage وهمي.

---

# 20) ملفات يجب قراءتها مع هذا الملف

- `docs/handoff/READ_FIRST_2026-08-28_AR.md`
- `docs/ops/CURRENT_STATE_2026-08-28_AR.md`
- `docs/ops/M05_HANDOFF_2026-08-28_AR.md`
- `docs/ops/M06_PROGRESS_2026-08-28_AR.md`
- `docs/ops/FULL_MAINTENANCE_PLAN_2026-08-28_AR.md`
- `docs/ops/OPEN_ITEMS_2026-08-28_AR.md`
- `docs/ops/progress_2026-08-28.json`
- `docs/specs/ADAPTATION_REINFORCEMENT_REDESIGN_2026-08-28_AR.md`
- `docs/specs/REINFORCEMENT_CONTENT_ADDITIONS_2026-08-28_AR.md`
- `docs/specs/AUDIO_INVENTORY_AND_GAPS_2026-08-28_AR.md`
- `docs/design/PRODUCT_UX_REBUILD_PLAN_2026-08-28_AR.md`
- `docs/ops/M03_RESIDUAL_CONTENT_GAPS_2026-08-28_AR.md`

---

# 21) نقطة الاستئناف الدقيقة

**الآن لا تبدأ M07.**

1. افتح HEAD الفعلي على `recovery/ui-media-admin-overhaul`.
2. استند إلى Implementation HEAD `98fdc638...` عند تشخيص Run #298 حتى لو docs commits أحدث.
3. أصلح M06 mobile supervisor navigation test/markup mismatch.
4. حافظ على `>=44px` وعلى dialog semantic behavior وعلى no-horizontal-overflow.
5. أعد Main Quality Gate حتى الثلاث jobs خضراء.
6. راجع screenshots/Responsive Visual Gate.
7. وثق M06 closure.
8. بعدها ابدأ M07 Research Reports.

أي مودل جديد يتبع هذه النقطة يجب أن يكون قادرًا على المتابعة دون الرجوع إلى المحادثة السابقة.
