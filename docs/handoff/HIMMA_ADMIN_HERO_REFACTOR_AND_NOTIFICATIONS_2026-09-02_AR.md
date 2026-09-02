# هِمّة — توثيق إعادة تنظيم Hero ولوحة المشرف والإشعارات

**التاريخ:** 2026-09-02  
**المستودع:** `7eaur/himma-deployment-sandbox` / `main`  
**الغرض:** توثيق تفصيلي للحالة التي يجب نقلها لاحقًا إلى `7eaur/himma-` بعد اكتمال التحقق.  
**حالة المستند:** ACTIVE — يكمل وثائق V3 ولا يمنح إذن Merge/Production.

---

## 1. سبب هذه الدفعة

الملاحظات التي بدأ منها العمل:

1. Hero الصفحة الرئيسية منخفض أكثر من اللازم عن الـHeader ويحتاج توازن أفضل، خصوصًا على الهاتف.
2. لوحة المشرف غير موحدة بصريًا؛ صفحات تستخدم headers/buttons محلية وأخرى تستخدم classes عامة.
3. أمثلة واضحة: زر تصدير صفحة المهارات كان يبدو كعنصر منفصل وغير متسق مع بقية اللوحة.
4. لا يوجد Admin UI layout/primitives كافية للعناصر المتكررة: Page Header، Actions، Panels، Stats، Toolbars، Empty states، Responsive data rendering.
5. بعض الصفحات صعبة على الهاتف، خصوصًا تفاصيل الطالب مع الـMobile topbar والـTabs والإجراءات الأفقية.
6. المشرف لا يملك Inbox واضحًا لمعرفة الجديد الذي يحتاج تدخلًا: تسجيلات بانتظار المراجعة أو حالات تقوية متصاعدة.
7. المطلوب ليس CSS patch؛ المطلوب حل معماري يقلل التكرار ويثبت Responsive behavior.

---

## 2. نتائج الـAudit الجذرية

### 2.1 Admin Shell موجود لكنه ليس Design System كاملًا

كان يوجد `apps/web/src/app/admin/(dashboard)/layout.tsx` مسؤول عن Sidebar وموبايل Topbar، لكن الصفحات الداخلية تستخدم خليطًا من:

- Tailwind utility classes.
- `globals.css` buttons/cards.
- CSS modules خاصة بكل صفحة.
- headers/actions مبنية داخل الصفحات.

النتيجة: نفس الوظيفة لها أكثر من شكل، وأي تعديل يستلزم تكراره في عدة صفحات.

### 2.2 Breakpoints غير متوافقة

الـAdmin shell كان ينتقل للموبايل عند breakpoint مختلف عن صفحة Student Details. هذا يخلق منطقة وسطية تظهر فيها عناصر Desktop dense مع Mobile shell أو العكس.

القرار: توحيد breakpoint الهيكلي الأساسي عند `820px` للـShell والصفحات الثقيلة.

### 2.3 الجداول ليست نمطًا مناسبًا للهاتف

`overflow-x-auto` وحده ليس UX كافيًا لكل الجداول. في البيانات التي يجب قراءتها واتخاذ إجراء عليها، الهاتف يحتاج Card representation.

القرار: `AdminResponsiveTable` يعرض Desktop table، ويعرض Mobile cards عند العرض الصغير.

### 2.4 الإشعارات لا يجب أن تكون Badge مزيفة

إظهار رقم محسوب مؤقتًا فقط في الواجهة لا يحفظ read/unread ولا يمنع التكرار ولا يعطي تاريخًا للمشرف.

القرار: Durable supervisor notification read-model مستقل عن القرارات الأكاديمية، مع `dedupe_key`, `read_at`, `href`, entity reference.

---

## 3. Hero الصفحة الرئيسية

**الملف:** `apps/web/src/app/landing.module.css`  
**Commit:** `712dcb9a8db1b6d2abcbf11075284e0fac0516f4`

التغييرات:

- تقليل المسافة العليا للـHero ليصبح أقرب بصريًا من الـHeader دون overlap.
- تقليل desktop `min-height` من الشكل الطويل السابق إلى توزيع أكثر توازنًا.
- تحسين tablet gap والـvisual max width.
- الهاتف:
  - Header أكثر compact.
  - Hero يبدأ أعلى.
  - العنوان والـlead أقل فراغًا.
  - Primary CTA بعرض واضح على الهاتف.
  - visual card أصغر radius/shadow ومقاس الشخصية متناسب.
  - الـdecorative circles تتدرج مع المقاس.
  - floating cards تختفي على الهاتف بدل تزاحم المشهد.
  - معالجة إضافية للشاشات <=380px.

الهدف: رفع الـHero بطريقة ناتجة عن إعادة توزيع spacing/min-height، وليس `margin-top:-x` ترقيعي.

---

## 4. Admin UI primitives المشتركة

تم إنشاء:

- `apps/web/src/components/admin/AdminUI.tsx`
- `apps/web/src/components/admin/AdminUI.module.css`

Commits الأصلية:

- `25d56080730bdf7c3e5c4ebe550931873b076019`
- `95b5784daa2acc72f7f70365050bc9037463f6d1`

المكونات المعتمدة:

- `AdminPage`
- `AdminPageHeader`
- `AdminAction`
- `AdminPanel`
- `AdminToolbar`
- `AdminStatGrid`
- `AdminStat`
- `AdminEmptyState`
- `AdminResponsiveTable`
- `AdminMobileCard`
- `AdminNotice`

### إصلاح تصدير الملفات من الجذر

`AdminAction` كان يمكن أن يمرر كل href إلى `next/link`. روابط `/api/...` الخاصة بـExcel/PDF ليست Navigation pages.

**الإصلاح:** `/api/...` يستخدم native `<a>`, صفحات التطبيق تستخدم `Link`.

**Commit:** `49dc810889ed8928905d78ef50f2d78ff88789be`

هذا يجعل إصلاح أزرار التصدير مركزيًا بدل كتابة استثناء في كل صفحة.

---

## 5. Admin Shell والتنقل

### الملفات

- `apps/web/src/app/admin/(dashboard)/layout.tsx`
- `apps/web/src/app/admin/(dashboard)/dashboard-layout.module.css`

### Commits

- `c4de292c2e5de649c4966b7c336ce73619c5737e`
- `3d093859c14eef0d0b59a1902f0e7534de19e571`

### IA الجديدة

التنقل مقسم حسب مهمة المشرف:

1. المتابعة
   - نظرة عامة
   - مراجعة التسجيلات
2. الطلاب
   - جميع الطلاب
   - إضافة طالب
3. النتائج والتقارير
   - التقارير
   - ملخص المهارات
4. إدارة المنصة
   - الإعدادات والمشرفون

بدل قائمة متساوية الأهمية بصريًا.

### Mobile shell

- Sidebar يختفي عند <=820px.
- topbar mobile أصبح Grid محسوب: menu / logo / label / notification.
- <=460px يقل النص.
- <=360px يختفي label غير الضروري بدل التزاحم.
- Mobile drawer له width مضبوط وscroll مستقل.

---

## 6. Student Details على الهاتف

**الملف:** `apps/web/src/app/admin/(dashboard)/students/[id]/student-detail.module.css`  
**Commit:** `0588c804fc1a396042630a446179523162b06998`

المشكلة:

- header الداخلي + mobile shell + tabs أفقية + action groups كانت كثيفة في عروض الهاتف/التابلت الصغيرة.

الحل:

- breakpoint الصفحة = 820px ليتطابق مع Shell.
- Header stacks على الهاتف.
- status action بعرض كامل.
- Tabs تتحول إلى Grid 2 columns بدل horizontal strip.
- Panels/grids/journey تصبح عمودًا واحدًا عند الحاجة.
- action groups 2 columns ثم 1 column على الهاتف الضيق.
- code/history/link cards stacks.
- summary cards لا تسبب min-width overflow.
- النصوص الطويلة تستخدم wrapping.
- <=360px tabs عمود واحد وتبسيط identity.

---

## 7. الصفحات التي انتقلت إلى Shared Admin UI

### Skill Reports

**Commit:** `4a259953312ff5fbb26f01e1b6443e35ca7b845d`

- Header موحد.
- زر Excel مصمم بـAdminAction.
- Refresh موحد.
- Stats/Panel مشتركة.
- Desktop table + Mobile cards.

### Students list

**Commit:** `633dca55dd1336a7d576b5538f98a69e1eaa7b48`

- Header/action/toolbar مشتركة.
- Search + status filtering.
- Desktop table / mobile student cards.
- زر فتح ملف واضح على الهاتف.

### Reports

**Commit:** `af501f42232b3be0d66e0c5221e8c98cedc91c4a`

- Excel/PDF/Refresh ضمن PageHeader actions.
- shared stats and panels.
- نتائج الطلاب Mobile cards بدل فرض الجدول العريض.

### Audio Review

**Commit:** `8b27ddbe730ebc88204a7ed0b91f6d341f26c35a`

- Shared Page/PageHeader/Panel/Actions.
- Review editor responsive.
- الحفاظ على قاعدة عدم استبدال queue أثناء تحرير المشرف، حتى لا تضيع الملاحظات بسبب refresh.

### New Student

**Commit:** `e36ef96a02adc6a6663d1b22ddb9a1f5a2bb6257`

- Shared page header/panel/actions.
- الحفاظ على test IDs وعقد إنشاء الطالب.
- طرق الرمز auto/manual responsive.
- success state موحد.

### Settings

تعذر استبدال ملف TSX عبر أداة المستودع بسبب حساسية محتواه المتعلقة بحقوق الدخول، لذلك لم يتم الالتفاف على ذلك.

تم تحديث CSS نفسه بأمان:

**Commit:** `830290ecf671dff57def88666c07a1cdc9b56e3d`

- Header visual language متوافق.
- breakpoint 820.
- Tabs Grid على الهاتف.
- forms/supervisor list column layout.
- overflow/wrapping guards.

يجب عند النقل للمستودع الأصلي تقييم استبدال Header markup بـ`AdminPageHeader` يدويًا بعد مراجعة آمنة، دون تغيير منطق كلمات المرور أو المشرفين.

---

## 8. نظام إشعارات المشرف

### قاعدة البيانات

Model:

`services/api/db/notification_models.py`

Commit:

`c5c4e6aa0d7adabb74f34658a569a58e4fc19d0f`

الحقول:

- notification_type
- title
- message
- href
- entity_type/entity_id
- dedupe_key UNIQUE
- is_read
- created_at/read_at

Migration:

`services/api/alembic/versions/0010_researcher_notifications.py`

Commit أولي:

`93261fb28d7e5fe9385be871ed8d4e65987e6e52`

`alembic/env.py` يسجل الموديل الجديد:

`a8664f12546192bcaabe9dd97541a18e73d116e4`

### Notification API

`services/api/admin_notifications.py`

Commit:

`290796cf7b2f52b7ca1ee256af8c451526b3c1cc`

الـAPI:

- GET `/researcher/notifications`
- POST `/researcher/notifications/{id}/read`
- POST `/researcher/notifications/read-all`

الحالات المادية الحالية:

1. `AudioSubmission.status = uploaded` → `audio_review_required` → `/admin/audio-review`
2. `ReinforcementCycle.status = escalated` → `reinforcement_attention` → `/admin/students/{id}`

التسجيل الذي لم يعد pending يتم إغلاق إشعاره غير المقروء تلقائيًا عند sync.

**قاعدة مهمة:** Notification table لا تقرر scoring/mastery/adaptation؛ هي read model للانتباه فقط.

### Frontend Notification Center

- `AdminNotifications.tsx`
- `AdminNotifications.module.css`

Commits:

- `749961a2812b925211b1aace26bfa6a998c4417b`
- `02e69dd01fb6c6a64004ef96edaa60d162858bea`

الخصائص:

- unread badge.
- popover.
- mark one/read all.
- direct navigation.
- mobile fixed dialog/scrim.
- refresh كل 30 ثانية.

لا يوجد WebSocket/Push في هذه الدفعة. هذا Poll خفيف فوق Durable DB state، وليس استخراجًا من DOM.

### Regression tests

`services/api/test_admin_notifications.py`

Commit:

`fbed823fcf269ddf9cf421a110fd971abb7b0068`

يغطي read/unread persistence وidempotent read-all.

---

## 9. مشاكل اكتشفها CI أثناء التنفيذ

### 9.1 Alembic index naming drift

الـmigration أنشأت:

`ix_researcher_notifications_type`

بينما SQLAlchemy `index=True` توقع:

`ix_researcher_notifications_notification_type`

هذا ليس schema logic failure بل mismatch في naming سيجعل `alembic check` غير نظيف.

**الحل:** migration تستخدم الاسم الذي يتوقعه metadata.

**Commit:** `701a895c2f2c58f973565f6ce6cf108fc3ba63b9`

### 9.2 React lint — synchronous refresh call in effect

`AdminNotifications` كان ينادي `refresh()` مباشرة داخل effect body، وقاعدة React الحديثة تمنع نمطًا قد ينتج cascading state updates.

**الحل:** initial refresh يتم عبر `setTimeout(...,0)`، والـinterval يبقى subscription timer، مع cleanup كامل.

**Commit:** `1f72913118c63765cb3c25902c72ecd34e27b18f`

---

## 10. Completed assessment reopen — إغلاق السبب الفعلي قبل Admin refactor

قبل بدء دفعة Admin تم تثبيت سبب فشل `/finish` السابق.

المحاولة `8ed267de...` عدلت `assessment.py` لكن الطلب الفعلي كان يمر بمسار أعلى أولوية:

`assessment_retake.py → temporary_audio_skip.finish_assessment_with_optional_temporary_skips`

أي Route shadowing.

تم إصلاح الـauthoritative route نفسه في:

**Commit:** `7798458524459baa82714aa6204207d87f5d8600`

السلوك:

- completed + persisted result → replay، بدون recompute/mutation.
- completed + missing result → 409.
- in-progress → scoring path الطبيعي.

يجب أن يبقى regression `test_assessment_completed_reopen.py` عند النقل.

---

## 11. Quality Gate

آخر SHA وظيفي عند إنشاء هذه الوثيقة:

`49dc810889ed8928905d78ef50f2d78ff88789be`

Quality Gate:

`33685228647`

**الحالة عند كتابة المستند:** IN PROGRESS.

ممنوع اعتبار هذه الدفعة CLOSED حتى:

- Backend SUCCESS
- Frontend SUCCESS
- Integration SUCCESS
- Vercel READY على SHA النهائي
- Railway SUCCESS على SHA backend النهائي

بعد اكتمالها يجب تحديث هذا القسم بالأرقام النهائية بدل `IN PROGRESS`.

---

## 12. قواعد النقل للمستودع الأصلي

1. لا cherry-pick عشوائي لكل commits؛ قارن final files وانقل الحالة النهائية.
2. Migration `0010` يجب تطبيقها بعد `0009` وفحص upgrade/downgrade/check.
3. لا تنقل Notification UI دون Backend model/API/migration معًا.
4. لا تعيد page-local export buttons بعد وجود AdminAction.
5. حافظ على breakpoint الهيكلي 820px بين shell وStudent Details.
6. لا تجعل mobile tables تعتمد دائمًا على horizontal scrolling عندما تكون البيانات إجراءية؛ استخدم cards.
7. لا تغير منطق assessment/adaptation أثناء Admin refactor.
8. لا تعتبر notification state مصدرًا أكاديميًا.
9. وثّق أي event notification جديد مع dedupe key وdestination واضحين.
10. المستودع الأصلي يبقى غير معدل حتى موافقة النقل.
