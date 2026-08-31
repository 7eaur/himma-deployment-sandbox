# خطة الصيانة والتحسين الشاملة — هِمّة — حالة تنفيذية 2026-08-28

**الحالة:** ACTIVE MAINTENANCE PROGRAM  
**الفرع:** `recovery/ui-media-admin-overhaul`

## المبدأ

نثبت الحقيقة بالكود والاختبارات، ثم الأكاديمي، ثم المحتوى والتقوية، ثم تجربة الطالب والمشرف، ثم responsive/accessibility، ثم التقارير والصوت والإطلاق. لا نغلق مرحلة بمجرد جمال الواجهة، ولا نغير قاعدة أكاديمية لتمرير اختبار.

---

## M00 — استعادة HEAD أخضر — ✅ CLOSED

أُصلح lineage الأحمر القديم واستعيد Quality Gate أخضر. تقرير الإغلاق: `docs/ops/M00_CLOSURE_2026-08-28_AR.md`.

---

## M01 — Placement Scoring & Gates — ✅ CLOSED

نُفذ/ثُبت:

- scoring section-based 20/40/40 بدل equal-weight 30-item percentage.
- readiness gate: أقل من 12/20 ⇒ L1.
- عدم اختراع threshold غير معتمد لبوابات القراءة/الصوت.
- TEMP_AUDIO_SKIP لا يتحول إلى خطأ أكاديمي.
- placement الذي يعتمد دليلًا غير متاح يمكن أن يكون provisional بدل اختلاق evidence.

تقرير: `docs/ops/M01_CLOSURE_2026-08-28_AR.md`.

---

## M02 — Adaptation State Machine — ✅ CLOSED

ثُبت:

- Placement منفصل مفهوميًا عن ongoing learning adaptation.
- `>=80` pass.
- `70–<80` guided retry.
- `<70` weakness + reinforcement path.
- mastery 50/30/20 كـtrend/profile وليس shortcut لإكمال المستوى.
- 10/10 core gate.
- upward journey من starting level إلى L3.
- Posttest بعد L3 فقط.
- level transitions تحتفظ بتاريخ المستويات بدل مسحها.

تقرير: `docs/ops/M02_CLOSURE_2026-08-28_AR.md`.

**قرار ما يزال مفتوحًا:** Automatic Demotion في المسار العادي. لا يُحذف صامتًا؛ الاتجاه المقترح support داخل المستوى + documented supervisor override.

---

## M03 — Reinforcement Content & Mapping — 🟡 IMPLEMENTED WITH EXPLICIT RESIDUAL GAPS

تم:

- الحفاظ على 15 تقوية أصلية.
- إضافة 18 تقوية versioned معتمدة: L1 +7، L2 +6، L3 +5.
- total reinforcement = 33.
- full seed = 123 items.
- Skill → Skill Family → Reinforcement mapping.
- no random fallback / no cross-level fallback.
- durable `ReinforcementCycle` + migration `0008_reinforcement_cycles`.
- ضعف → تقوية → رجوع للنشاط الأساسي → verification → continue.
- bounded verification attempts ثم supervisor intervention.

### 3 فجوات باقية لا يجوز إخفاؤها

1. L2 قراءة كلمات السكون.
2. L3 الفهم المباشر.
3. L3 بناء الجملة.

مرجع: `docs/ops/M03_RESIDUAL_CONTENT_GAPS_2026-08-28_AR.md`.

**Gate المتبقي أكاديميًا لهذه الثلاث:** اعتماد mapping مباشر أو Micro-Reinforcement جديد. إلى ذلك الحين Safe Hold للمشرف.

---

## M04 — Student Product UI — ✅ REBUILT / ACCEPTED BASELINE

تم:

- Full-screen / `100dvh` Learning Stage.
- إعادة بناء نشاط الطالب لاستغلال الشاشة بدل Card ضيقة وفراغات كبيرة.
- إبراز الشخصية التعليمية + instruction bubble.
- تحسين image/text/sequence/read/record interactions.
- توحيد assessment shell بصريًا مع learning stage.
- responsive phone/tablet/desktop rules.
- reduced-motion support.
- five-size Responsive Visual Gate.
- visual/runtime regression coverage مع vertical slice.

**مبدأ ثابت:** لا نعدل الـ105 الأصلية أثناء UI work.

---

## M05 — Supervisor Product UX — ✅ REBUILT / ACCEPTED BASELINE

تم:

- Admin IA / Shell جديدان.
- إصلاح ظهور mobile/desktop navigation المتداخل تاريخيًا.
- Dashboard نحو Action Center: ما يحتاج انتباه المشرف أولًا ثم الإحصاءات.
- Student Profile تحول إلى workspace tabs بدل صفحة واحدة طويلة.
- reinforcement review أصبح focused expandable alert.
- settings قسمت إلى Account / Security / Supervisors.
- vertical slice عُدل للتنقل الجديد ونجح على آخر implementation run حتى نقطة M06.

مرجع جديد: `docs/ops/M05_HANDOFF_2026-08-28_AR.md`.

---

## M06 — Responsive / Accessibility / Design QA — 🔵 ACTIVE

### المنجز

- global focus-visible safeguards.
- reduced-motion safeguards.
- contrast tokens محسنة.
- Responsive Visual Gate على:
  - 360×800.
  - 390×844.
  - 768×1024.
  - 1024×768.
  - 1440×900.
- Accessibility integration checks لـRTL/keyboard/overflow/zoom/contrast/technical-language.

### آخر دليل

Implementation HEAD: `98fdc638737bdb8ab9be4937cff6155865998d1f`.

Responsive Visual Gate Run `33202256450`: **SUCCESS**.

Main Quality Gate #298 / `33202256449`:

- Backend SUCCESS.
- Frontend SUCCESS.
- Integration FAILURE.

الفشل الحالي الوحيد: mobile supervisor navigation test يبحث داخل dialog عن class `a.sidebar-nav-item` ولا يجدها. الـdialog نفسه visible، وVertical Slice وبقية accessibility tests نجحت.

### المهمة الحالية

إصلاح selector/markup contract بشكل semantic دون خفض شرط touch target 44px، ثم إعادة Quality Gate حتى الأخضر الكامل.

### Gate M06 النهائي

- no horizontal overflow على المقاسات الخمسة.
- Touch >=44px.
- Focus visible.
- Keyboard admin navigation.
- 200% zoom usable.
- normal-text contrast acceptable.
- RTL/shaping صحيح.
- reduced motion.
- no implementation vocabulary child-facing.
- screenshots reviewed visually، لا automation فقط.

مرجع: `docs/ops/M06_PROGRESS_2026-08-28_AR.md`.

---

## M07 — Research Reports — ⏳ PENDING

المطلوب:

- Pre/Post comparison.
- absolute + percentage improvement.
- per-skill errors.
- reading C/D/I/S حيث يوجد valid evidence.
- time/attempts.
- starting/final level.
- reinforcement history.
- filters + individual/aggregate views.
- Excel multi-sheet.
- PDF individual + aggregate.
- export audit log.

Gate: UI/Excel/PDF تتفق مع DB ولا تختلق metric من صوت غير محلل.

---

## M08 — Real Speech Analysis — ⏳ PENDING / EXTERNAL-GATED

الهدف: **Reference-Guided Arabic Reading Analysis**.

البنية الأساسية موجودة، لكن لا إغلاق حقيقي قبل:

- representative recordings.
- provider selection/connection.
- privacy/cost/transfer decision.
- confidence calibration/versioning.
- retention policy.
- sample evaluation + manual review fallback.

لا تدعِ أن ASR مكتمل.

---

## M09 — Release / UAT — ⏳ PENDING

- complete E2E scenarios.
- network/microphone/service failure cases.
- security/privacy review.
- backup + restore drill.
- production domain/HTTPS.
- monitoring/logging.
- synthetic-data UAT أولًا.
- final manuals/handoff.

Gate: accepted ACs أو written exemptions فقط.

---

## ثوابت البرنامج

- لا reset/hard rollback للتخلص من Regression.
- لا تعديل tests لتخفيض التوقعات.
- لا fake score للصوت.
- لا وسائط مختلقة بدل gap معلن.
- لا random reinforcement.
- لا قواعد أكاديمية بصمت.
- لا Posttest بعد L1/L2 فقط.
- لا خلط بين نجاح CI واكتمال المنتج.
- لا Docker محليًا لهِمّة.

## ترتيب الاستئناف الآن

**M06 current red integration test → Green Quality Gate → M06 closure → M07 → M08 (بعد external gates) → M09.**
