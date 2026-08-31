# اقرأ هذا أولًا — هِمّة — تحديث الاستئناف 2026-08-28

هذا هو **مدخل الاستئناف الإلزامي الأحدث**. إذا تعارض مع `RESUME_HERE.md` أو handoff أقدم، فهذا الملف وما يشير إليه أحدث زمنيًا.

## 1) قبل أي تعديل

1. اعمل على نفس المستودع `7eaur/himma-`.
2. الفرع التنفيذي الحالي: `recovery/ui-media-admin-overhaul`.
3. **لا تعمل Reset/Hard rollback، لا تنشئ مشروعًا بديلًا، ولا تعدّل الفروع الأساسية.**
4. افحص HEAD الحالي فعليًا لأن commits التوثيق اللاحقة قد تكون أحدث من SHA المذكور أدناه.
5. لا تستخدم Docker محليًا في مشروع هِمّة؛ Docker الموجود في GitHub Actions لا يغيّر هذا القيد المحلي.

## 2) ترتيب القراءة

اقرأ بالترتيب:

1. `docs/ops/HIMMA_MASTER_CONTINUITY_HANDOFF_2026-08-28_AR.md`
2. `docs/ops/CURRENT_STATE_2026-08-28_AR.md`
3. `docs/ops/M06_PROGRESS_2026-08-28_AR.md`
4. `docs/ops/FULL_MAINTENANCE_PLAN_2026-08-28_AR.md`
5. `docs/specs/ADAPTATION_REINFORCEMENT_REDESIGN_2026-08-28_AR.md`
6. `docs/specs/REINFORCEMENT_CONTENT_ADDITIONS_2026-08-28_AR.md`
7. `docs/design/PRODUCT_UX_REBUILD_PLAN_2026-08-28_AR.md`
8. `docs/specs/AUDIO_INVENTORY_AND_GAPS_2026-08-28_AR.md`
9. `docs/ops/DECISIONS_2026-08-28_AR.md`
10. `docs/ops/OPEN_ITEMS_2026-08-28_AR.md`
11. `docs/ops/progress_2026-08-28.json`

ثم افحص GitHub Actions والـGit الفعلي؛ **الكود ونتائج CI أحدث من أي نص إذا ظهر تعارض.**

## 3) نقطة التنفيذ الحالية

آخر Implementation HEAD قبل دفعة التوثيق الجديدة:

`98fdc638737bdb8ab9be4937cff6155865998d1f`

عليه:

- Responsive Visual Gate #18 / Run `33202256450`: **SUCCESS**.
- Quality Gate #298 / Run `33202256449`:
  - Backend: **SUCCESS**.
  - Frontend: **SUCCESS**.
  - Integration/Playwright: **FAILURE**.

الفشل الحالي محدد في اختبار M06 فقط:

`tests/e2e/accessibility-integration.spec.ts`

سيناريو:

`mobile supervisor navigation keeps touch targets and layout intact`

الـdialog باسم **«قائمة لوحة المشرف»** يظهر، لكن الاختبار يبحث داخله عن `a.sidebar-nav-item` ولا يجد عنصرًا بهذا المحدد. بقية اختبارات M06 في نفس التشغيل نجحت، وكذلك الـVertical Slice الكامل نجح.

### المهمة الأولى في المحادثة التالية

صحح التوافق بين Markup واختبار تنقل المشرف على الجوال **دون تخفيض شرط 44px أو حذف الاختبار**، ثم أعد Quality Gate حتى يصبح Backend + Frontend + Integration/Playwright كلها خضراء. بعدها أكمل قبول M06.

## 4) حالة برنامج الصيانة

- M00: CLOSED.
- M01: CLOSED.
- M02: CLOSED.
- M03: IMPLEMENTED مع 3 فجوات محتوى علاجية موثقة وغير مخترعة.
- M04: Student Product UI rebuilt/accepted إلى baseline الحالي.
- M05: Supervisor Product UX rebuilt إلى baseline الحالي.
- **M06: ACTIVE — Responsive/Accessibility/Design QA.**
- M07: PENDING — Research Reports.
- M08: PENDING/EXTERNAL-GATED — Real Speech Analysis.
- M09: PENDING — Release/UAT.

## 5) ممنوع نسيانه

- المحتوى الأصلي = 105 عنصرًا ولا يُعدّل بصمت.
- 18 تقوية إضافية معتمدة فوق 15 الأصلية؛ runtime full catalog = 123 عنصرًا، منها 33 تقوية.
- `HIMMA_TEMP_AUDIO_SKIP` مؤقت ومحايد أكاديميًا.
- الصوت الثابت: 50 موجود + ناقص «موز» و«سَا» = 52 مستهدف.
- ASR الحقيقي لم يكتمل؛ الهدف Reference-Guided Arabic Reading Analysis.
- Automatic Demotion ما يزال قرارًا مفتوحًا؛ لا يُحذف أو يُعتمد صامتًا.
