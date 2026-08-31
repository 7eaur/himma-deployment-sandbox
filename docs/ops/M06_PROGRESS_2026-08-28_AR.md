# M06 — Responsive / Accessibility / Design QA — Progress

**التاريخ:** 2026-08-28  
**الحالة:** **CLOSED** — Main Quality Gate + Responsive Visual Gate + visual evidence verified.

## الهدف

إثبات أن Student + Supervisor UI بعد M04/M05 تعمل فعليًا على الهاتف والتابلت والكمبيوتر، مع RTL صحيح، keyboard/focus، touch targets مناسبة، zoom، contrast، reduced motion، وعدم كشف مصطلحات تقنية للطفل.

## Implementation HEAD المقبول

`cdb02c75ad33d1b002ee1fdb84ecf1fee3dc57d4`

Commit:

`test(M06): use semantic mobile nav evidence`

هذا الرأس يحافظ على جميع إصلاحات M00→M05 ولا يغير أي قرار أكاديمي.

## الإصلاح النهائي للـRegression

الفشل السابق كان في سيناريو:

`mobile supervisor navigation keeps touch targets and layout intact`

المشكلة لم تكن أن target أقل من 44px؛ الاختبار كان يعتمد selector تجميلي هش داخل dialog.

تم الإصلاح على ثلاث خطوات متحفظة:

1. إضافة عقد stable للـnav item دون تغيير السلوك.
2. رفع زر إغلاق mobile menu من 42×42 إلى **44×44** بدل خفض شرط الاختبار.
3. تحويل الاختبار النهائي إلى locator دلالي:
   `getByRole("link", { name: "نظرة عامة" })`
   مع إبقاء شرط `>=44px` وno-horizontal-overflow كما هما.

أضيفت أيضًا لقطة مباشرة لحالة قائمة المشرف على الهاتف داخل artifact الرسمي:

`playwright-report/screenshots/18-mobile-supervisor-menu.png`

## Main Quality Gate النهائي

Run **#314** / ID `33211325199` على `cdb02c75ad33d1b002ee1fdb84ecf1fee3dc57d4`:

- Frontend: **SUCCESS**.
- Backend: **SUCCESS**.
- Integration: **SUCCESS**.
- Playwright E2E: **SUCCESS**.
- Upload Playwright report: **SUCCESS**.

إذن regression الذي كان يمنع M06 أُغلق دون حذف test أو skip أو تخفيض expectation.

## Responsive Visual Gate النهائي

Run **#22** / ID `33211325207` على نفس HEAD: **SUCCESS**.

المقاسات المغطاة:

- 360×800.
- 390×844.
- 768×1024.
- 1024×768.
- 1440×900.

Build + Chromium + responsive smoke matrix + screenshots artifact كلها ناجحة.

## Acceptance المثبت

- no horizontal overflow في سيناريوهات M06 المختبرة.
- mobile menu يفتح داخل dialog دلالي واضح.
- زر فتح القائمة 44×44 على الأقل.
- رابط التنقل داخل mobile menu ارتفاعه 44px على الأقل.
- زر الإغلاق 44×44.
- RTL في workspace.
- keyboard focus + focus outline.
- 200% zoom equivalent usable.
- contrast tokens الحرجة تحقق شرط النص العادي في الاختبار.
- reduced-motion يوقف الحركة الزخرفية.
- child entry surfaces لا تعرض implementation vocabulary المحظور.
- Full Vertical Slice ما زال ناجحًا داخل Main Quality Gate.

## Visual review

تمت مراجعة evidence الفعلية، وليس الاكتفاء بحالة CI:

- Responsive artifact يغطي landing + student login + supervisor login عبر المقاسات الخمسة.
- Playwright artifact يغطي رحلة الطالب/المشرف الأساسية وشاشات M04/M05.
- لقطة `18-mobile-supervisor-menu.png` تؤكد بصريًا أن القائمة تظهر كلوحة هاتف واضحة، RTL، بعناصر تنقل مقروءة، active state واضح، user area وlogout، مع overlay على المحتوى الخلفي.

ملاحظة: full-page screenshot قد يُظهر المحتوى الخلفي أسفل ارتفاع viewport لأن overlay نفسه viewport-fixed؛ هذا لا يمثل overflow داخل viewport ولا فشلًا في القائمة.

## القرارات الأكاديمية

لم يتغير في M06 أي من:

- Placement 20/40/40 والبوابات المعتمدة.
- >=80 pass، 70–<80 guided retry، <70 reinforcement.
- 10/10 core gate.
- Skill-family reinforcement mapping.
- Safe Hold للفجوات الثلاث المتبقية.
- Automatic Demotion ما زال OPEN DECISION ولا يُحسم بصمت.

## النتيجة

**M06 CLOSED.**

نقطة الاستئناف التالية حسب خطة الصيانة هي:

**M07 — Research Reports**.

لا يُعاد فتح M00→M06 إلا عند Regression جديد أو دليل يناقض القبول الحالي.
