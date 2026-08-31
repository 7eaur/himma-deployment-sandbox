# سجل التغييرات — مراجعة وصيانة هِمّة — 2026-08-28

هذا السجل يلخص انتقال المشروع من Recovery Baseline إلى برنامج الصيانة المنتجية/الأكاديمية M00→M09.

## 1. بداية برنامج الصيانة

المراجعة أثبتت أن نجاح Recovery القديم لا يكفي كتسليم منتج نهائي. أُنشئت خطة شاملة تشمل:

- صحة Placement.
- Adaptation State Machine.
- Reinforcement Mapping/Content.
- Student Product UI.
- Supervisor Product UX.
- Responsive/Accessibility QA.
- Research Reports.
- Real Speech Analysis.
- Release/UAT.

---

## 2. M00 — Restore Green Baseline

- شُخصت سلسلة CI الحمراء بعد Recovery.
- لم يتم rollback للإصلاحات الحديثة.
- أعيد Quality Gate إلى الأخضر وأُغلق M00.
- مرجع: `M00_CLOSURE_2026-08-28_AR.md`.

---

## 3. M01 — Placement Scoring

تم الانتقال من تصور equal-weight 30 سؤالًا إلى scoring الأقسام المعتمد:

- 20 readiness.
- 40 word building/reading.
- 40 fluency/comprehension.
- readiness <12/20 forces L1.
- عدم اختراع L3 audio/text threshold غير معتمد.
- TEMP audio skip لا يتحول إلى academic failure.

أُغلق M01 بعد tests/CI.

---

## 4. M02 — Learning Adaptation State Machine

ثبتت قواعد:

- placement = starting level.
- L1→L2→L3 journey.
- >=80 pass.
- 70–<80 guided retry.
- <70 reinforcement path.
- 10/10 core gate.
- mastery 50/30/20 trend وليس promotion shortcut.
- Posttest بعد L3 فقط.

أُغلق M02 بعد regression coverage.

Automatic Demotion بقي قرارًا مفتوحًا ولم يُحذف بصمت.

---

## 5. M03 — Reinforcement System

### Content

- 15 تقوية أصلية محفوظة.
- 18 إضافة versioned معتمدة:
  - L1 +7.
  - L2 +6.
  - L3 +5.
- reinforcement total = 33.
- full runtime catalog = 123 item.
- skills = 44.

### Runtime

- Skill → Skill Family → Approved Reinforcement.
- no random fallback.
- no cross-level random fallback.
- durable ReinforcementCycle.
- migration `0008_reinforcement_cycles`.
- weakness → reinforcement → return-to-core → verification → continue.
- bounded retries ثم supervisor.

### Residual gaps

بقيت 3 فجوات موثقة لا يتم تغطيتها بالحدس:

- L2 sukoon word reading.
- L3 literal comprehension.
- L3 sentence building.

مرجع: `M03_RESIDUAL_CONTENT_GAPS_2026-08-28_AR.md`.

---

## 6. Audio Inventory

- 50 fixed audio assets موجودة.
- ينقص فقط «موز» و«سَا» حسب الجرد المعروف.
- target = 52.
- 18 reinforcement additions لا تخلق فجوات ثابتة أخرى معروفة.
- TEMP Audio Skip بقي feature-flagged ومحايدًا أكاديميًا.

---

## 7. M04 — Student Product UI

أُعيد بناء تجربة الطالب من Card تقليدية إلى Learning Stage:

- `100dvh` full-screen approach.
- مساحة تعلم أوسع.
- شخصية تعليمية بارزة + contextual helper bubble.
- تحسين image/options/sequence/build/read/record interactions.
- توحيد assessment styling مع activity styling.
- responsive phone/tablet/desktop rules.
- reduced motion / focus states.
- five-size visual workflow.

الهدف أصبح أن يشعر الطفل أنه داخل جلسة تعلم لا داخل موقع إداري.

---

## 8. M05 — Supervisor Product UX

أعيد بناء أضعف منطقة منتجية:

- Admin IA / Sidebar groups.
- Dashboard نحو Action Center.
- Student Profile → Workspace Tabs.
- Reinforcement Review → compact expandable alert.
- Settings → Account / Security / Supervisors.
- Vertical Slice عُدل ليتبع tabs الجديدة.

مرجع: `M05_HANDOFF_2026-08-28_AR.md`.

---

## 9. M06 — Responsive / Accessibility QA

تمت إضافة:

- global focus/motion safeguards.
- accessible contrast token corrections.
- accessibility integration suite.
- Responsive Visual Gate على 360×800، 390×844، 768×1024، 1024×768، 1440×900.

Implementation HEAD المرجعي:

`98fdc638737bdb8ab9be4937cff6155865998d1f`

### الأدلة الحالية

Responsive Visual Gate Run `33202256450`: **SUCCESS**.

Main Quality Gate #298 / `33202256449`:

- Backend SUCCESS.
- Frontend SUCCESS.
- Integration FAILURE.

نجحت اختبارات:

- RTL/keyboard/focus/overflow.
- reduced motion.
- 200% zoom equivalent.
- contrast.
- hiding technical vocabulary from child surfaces.
- full Vertical Slice.

فشل فقط mobile supervisor navigation test لأن dialog visible لكن selector `a.sidebar-nav-item` لا يطابق عنصرًا داخل الـdialog، لذلك لم يصل الاختبار حتى قياس touch target >=44px.

**نقطة العمل الحالية:** semantic selector/markup fix بدون تخفيض accessibility requirement، ثم full green gate.

مرجع: `M06_PROGRESS_2026-08-28_AR.md`.

---

## 10. ما لم يبدأ/يُغلق بعد

### M07 — Reports

Pre/Post, improvement, skills, levels, reinforcement history, Excel/PDF/audit consistency.

### M08 — Real Speech

Reference-Guided architecture موجودة كأساس؛ real provider/calibration/privacy/retention ما تزال خارجية/مفتوحة.

### M09 — Release

UAT, failures, backup/restore, security/privacy, deployment/HTTPS/monitoring/manuals.

---

## 11. ملفات الاستئناف الأحدث

- `docs/handoff/READ_FIRST_2026-08-28_AR.md`
- `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-08-28_AR.md`
- `docs/ops/CURRENT_STATE_2026-08-28_AR.md`
- `docs/ops/M05_HANDOFF_2026-08-28_AR.md`
- `docs/ops/M06_PROGRESS_2026-08-28_AR.md`
- `docs/ops/FULL_MAINTENANCE_PLAN_2026-08-28_AR.md`
- `docs/ops/OPEN_ITEMS_2026-08-28_AR.md`
- `docs/ops/progress_2026-08-28.json`

**أول إجراء في أي استئناف جديد: اقرأ READ_FIRST ثم افحص HEAD وGitHub Actions الفعلي قبل أي تعديل.**
