# هِمّة — ملحق التحقق النهائي للـSandbox قبل النقل للمستودع الأصلي

**التاريخ:** 2026-09-02  
**يُقرأ مع:** `docs/handoff/HIMMA_SANDBOX_TO_MAIN_MIGRATION_HANDOFF_2026-09-02_AR.md`  
**الغرض:** تسجيل آخر المشاكل التي ظهرت بعد إصدار Handoff v2، وإثبات حالة النشر والـCI بدون ادعاء PASS غير مثبت.

---

## 1. آخر حالة محتوى/Backend معتمدة في الـSandbox

آخر SHA وظيفي يتضمن تحويل نشاط المسار إلى القصص السمعية مع DB Runtime والاختبارات:

`ff62e373856661cd177f98b6d6b92fb5b847fd1e`

يتضمن:

- L1-CORE-09 = قصة ليان + 5 أسئلة فهم مباشر.
- L1-REIN-11 = قصة نادر + 5 أسئلة تقوية.
- story text داخلي فقط ولا يظهر في stimulus.
- interaction = `listen_choose_one`.
- 3 خيارات لكل جولة وإجابة صحيحة واحدة.
- story audio asset = null مؤقتًا.
- media gap صريح بدل fake audio.
- إجمالي الأصول الصوتية الخارجية الناقصة = 4: `موز`، `سَا`، قصة ليان، قصة نادر.

Railway deployment المرتبط بهذا الـBackend:

- Deployment: `36d4b947-4423-401d-be06-f0df259da73b`
- SHA: `ff62e373856661cd177f98b6d6b92fb5b847fd1e`
- Status: `SUCCESS`

الـcommits اللاحقة الخاصة بالوثائق/CSS ظهرت على Railway كـ`SKIPPED` لأن خدمة الـAPI لم تتغير؛ هذا سلوك صحيح ولا يعني أن النشر الخلفي ناقص.

---

## 2. مشكلة E2E/واجهة اكتُشفت بعد Handoff v2

في GitHub Actions run:

`33578211934`

نجح Backend وFrontend، لكن Integration/Playwright فشل في اختبارين.

الاختباران كانا ينتظران زرًا باسم:

`تأكيد والمتابعة`

الفحص لم يكتف بتغيير الاختبار. تم تنزيل Playwright artifact وفحص لقطة:

`pretest-q1-desktop.png`

وأظهرت اللقطة أن زر الـCTA نفسه موجود بصريًا في أسفل البطاقة لكنه يظهر ككتلة زرقاء **بدون نص مرئي**. لذلك اعتُبرت المشكلة UI/Accessibility regression حقيقية وليست مجرد توقع اختبار قديم.

### السبب/الحماية المضافة

تمت إضافة قاعدة Safety مشتركة في:

`apps/web/src/app/student/student-experience.css`

تضمن أن النص داخل `primaryWide`:

- `display:inline !important`
- `visibility:visible !important`
- `opacity:1 !important`
- يرث لون وخط الزر.
- يبقى موجودًا حتى عندما يكون الزر disabled قبل اختيار الإجابة.

Commit الإصلاح:

`81c067d71a9c0867196cce20885074312bf912eb`

Message:

`fix(student): keep primary CTA labels visible and accessible`

هذا الإصلاح يجب نقله للمستودع الأصلي مع اختبارات الـE2E؛ لا يجوز حل المشكلة بحذف assertion فقط.

---

## 3. نشر Frontend بعد إصلاح CTA

Vercel deployment:

- Deployment ID: `dpl_Fz8mqVJ8aC28Ji8a7B28cVGxPnQA`
- SHA: `81c067d71a9c0867196cce20885074312bf912eb`
- State: `READY`
- Target: production داخل مشروع الـSandbox فقط.

الرابط العام للـSandbox يبقى:

`https://himma-deployment-sandbox.vercel.app`

---

## 4. Quality Gate بعد إصلاح CTA

GitHub Actions run:

`33579499049`

SHA:

`81c067d71a9c0867196cce20885074312bf912eb`

الحالة عند كتابة هذا الملحق:

- Frontend: `SUCCESS`
  - TypeScript ✅
  - ESLint ✅
  - Unit tests ✅
  - Next.js build ✅
- Backend: `SUCCESS`
  - catalog validation ✅
  - migrations upgrade/downgrade/upgrade ✅
  - model drift ✅
  - seed idempotency ✅
  - backend test suite ✅
- Integration: `IN PROGRESS`
  - containers ✅
  - MinIO ✅
  - migrations/full seed ✅
  - FastAPI start ✅
  - frontend deps/build/start ✅
  - Playwright browsers ✅
  - Playwright E2E: running عند كتابة الملحق.

**قاعدة evidence:** لا تعتبر هذه الحالة Full Green إلا إذا أصبح Integration = SUCCESS على نفس run/SHA.

---

## 5. ما يجب نقله للمستودع الأصلي بخصوص هذا الاكتشاف

1. لا تعدل اختبارات E2E فقط لتقبل CTA مختفيًا.
2. انقل قاعدة حماية نص CTA أو نفذ حماية مكافئة في القالب النهائي.
3. احتفظ باختبار mobile/desktop الذي يتحقق أن زر `تأكيد والمتابعة` مرئي باسمه وليس مجرد مستطيل قابل للنقر.
4. راجع disabled state بصريًا: يجب أن يقل وضوح الزر لكن يبقى نصه مقروءًا.
5. اختبر accessibility name للزر بواسطة role/name.
6. لا تعيد طبقات CSS القديمة التي قد تخفي child span أو تتداخل مع primary CTA.

---

## 6. سلسلة المراجع النهائية حتى الآن

- Handoff v2: `docs/handoff/HIMMA_SANDBOX_TO_MAIN_MIGRATION_HANDOFF_2026-09-02_AR.md`
- هذا الملحق: يوثق آخر Verification Regression وإصلاحه.
- Story content functional SHA: `ff62e373856661cd177f98b6d6b92fb5b847fd1e`
- CTA/frontend verification SHA: `81c067d71a9c0867196cce20885074312bf912eb`
- Railway API deployment: `36d4b947-4423-401d-be06-f0df259da73b` / SUCCESS
- Vercel frontend deployment: `dpl_Fz8mqVJ8aC28Ji8a7B28cVGxPnQA` / READY
- CI verification run: `33579499049`

عند انتهاء Integration يجب إما تحديث هذا الملحق بنتيجة SUCCESS النهائية أو تسجيل الفشل الجديد وسببه وإصلاحه قبل النقل الرسمي.