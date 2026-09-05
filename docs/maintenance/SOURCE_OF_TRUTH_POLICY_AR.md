# سياسة مصدر الحقيقة للمستودعات — هِمّة

**التاريخ:** 2026-09-04  
**الحالة:** ACTIVE

## 1. المستودع الرسمي الوحيد

المصدر التنفيذي المعتمد للمشروع هو:

`7eaur/himma-`

والفرع الجاري توحيده حاليًا:

`recovery/ui-media-admin-overhaul`

أي إصلاح أو تحسين جديد يجب أن يدخل هنا ويثبت بالاختبارات والأدلة.

## 2. وضع Sandbox

`7eaur/himma-deployment-sandbox` ليس Source of Truth.

وضعه من الآن:

**Reference / historical development sandbox**

يستخدم فقط عند الحاجة إلى:

- مقارنة قرار تصميم سابق.
- استرجاع سياق تجربة أو تنفيذ.
- مراجعة وثائق migration/deployment تاريخية.
- استخراج فكرة مفيدة ثم إعادة تنفيذها بصورة مناسبة للبنية الرسمية.

لا ينسخ ملف منه إلى الرسمي لمجرد أن تاريخه أحدث أو شكله أفضل.

## 3. قاعدة المصالحة

عند وجود فرق بين الرسمي والـSandbox:

1. نحدد السلوك الفعلي في النسختين.
2. نحدد أيهما يتوافق مع العقود الأكاديمية والمعمارية الحالية.
3. نأخذ **القرار الأفضل** لا الملف بالضرورة.
4. نعيد تنفيذه داخل الرسمي بدون إعادة Patch/legacy architecture.
5. نضيف اختبارًا يمنع الرجوع للسلوك القديم.
6. نوثق القرار إذا كان معماريًا أو أكاديميًا.

## 4. ممنوعات

- لا wholesale copy من Sandbox.
- لا merge عشوائي بين تاريخي المستودعين.
- لا cherry-pick لمجرد تشابه عنوان commit.
- لا استبدال Runtime hardening الرسمي بنسخة Sandbox أقدم.
- لا إعادة `sandbox_bootstrap.py` إلى Core runtime.
- لا إعادة DOM enhancers/visual polish layers الملغاة.
- لا اعتبار Documentation في Sandbox دليلًا أن الكود الرسمي ناقص دون مقارنة الكود.

## 5. ما يحافظ عليه الرسمي

من أهم العقود التي لا يجوز خسارتها أثناء المصالحة:

- DB-only student runtime.
- versioned content projection.
- readiness يتحقق من عقد المحتوى لا الخدمات فقط.
- local runtime sync idempotent يحافظ على الطلاب والمحاولات والتاريخ.
- structured student APIs.
- assessment neutrality.
- targeted reinforcement.
- R1 promotion gates الحالية.
- waiting-audio-review state.
- reports تعتمد evidence فعلي ولا تصنع mastery.
- durable supervisor notifications.
- canonical task design system.

## 6. نهاية عمر Sandbox

بعد تحقق جميع الآتي على SHA واحد من الرسمي:

- Quality Gate أخضر.
- Responsive visual gate أخضر.
- Release/full journey gate المطلوب أخضر.
- Media gaps موثقة بدقة.
- لا تحسين معروف مطلوب من Sandbox لم تتم مصالحته.

يمكن عندها جعل Sandbox أرشيفًا/قراءة فقط وعدم استخدامه للتطوير اليومي.

## 7. دليل الاعتماد

لا تستخدم عبارة PASS/CLOSED بناءً على هذه الوثيقة.

الاعتماد يتطلب دائمًا:

- SHA دقيق.
- Workflow run IDs.
- نتائج jobs.
- artifacts/screenshots عند التغيير البصري.
- ذكر أي External Gate متبقٍ بوضوح.
