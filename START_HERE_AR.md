# ابدأ من هنا — مستودع هِمّة

هذه نقطة الدخول التنفيذية لأي محادثة أو وكيل جديد يعمل على منصة هِمّة.

## 1) اقرأ هذه المراجع أولًا

بالترتيب:

1. `docs/ops/STATUS.md`
2. `docs/ops/progress.json`
3. `docs/maintenance/REPOSITORY_HARDENING_PLAN_2026-09-04_AR.md`
4. `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`
5. `docs/architecture/STUDENT_TASK_DESIGN_SYSTEM_AR.md`
6. `docs/ops/M09_RELEASE_UAT_RUNBOOK.md`
7. `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md`
8. `docs/specs/SOURCE_OF_TRUTH.md`

وثائق أغسطس الأقدم تبقى كسجل تاريخي ولا تتقدم على الكود والاختبارات والوثائق النشطة أعلاه عند التعارض.

## 2) المستودع التنفيذي

- Repository: `7eaur/himma-`
- Working branch: `recovery/ui-media-admin-overhaul`
- افحص HEAD وGitHub Actions في بداية كل جلسة؛ لا تعتمد على SHA محفوظ داخل وثيقة إذا تحرك الفرع بعدها.
- لا تعدّل `stage/04-production-slice` أو `stage/02-content` مباشرة.
- لا force push / reset hard / clean destructive.
- لا إطلاق أو دمج production دون موافقة المستخدم الصريحة.

## 3) الحقيقة التشغيلية الحالية

- Approved original content: 105 عنصرًا.
- Runtime total: 125.
- Reinforcement total: 35.
- Skills: 44.
- المسار المعماري: `Approved versioned source -> deterministic seed/projection -> PostgreSQL runtime -> structured API -> deterministic renderer`.
- Design System واحد لمهام الطالب؛ لا `*-polish.css` ولا DOM enhancers كحل للحالة.
- Assessment completion وActivities route ownership موحدان بلا duplicate route-by-order.
- القصتان السمعيتان تأتيان من مصدر versioned واحد، ولا يوجد `patch_db_runtime()` بعد الإسقاط.

## 4) الصوت

الأصول الثابتة المعتمدة مكتملة: 54 WAV + 54 MP3، ولا توجد فجوة صوت ثابت مطلوبة للعناصر الحالية.

آخر الإضافات/الاستبدالات:

- `LET-01` = **مَ**، ببايتات التسجيل المعتمد المصدر `SYL-15` مع الحفاظ على المعرّف المستقر.
- `WRD-29` = **موز**.
- `SYL-13` = **سَا**.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.

الأزواج العشرة WAV/MP3 موجودة فعليًا في GitHub ومتحقق منها بالحجم وGit blob SHA وSHA-256. الدليل الكامل:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`

لا يوجد Student Audio Skip في UI أو API أو feature flags. تسجيل الطالب يبقى في `waiting_audio_review` ويُراجع من المشرف حتى اعتماد وربط نموذج التحليل الصوتي الآلي.

إغلاق الأصول الثابتة لا يعني اكتمال M08 كتحليل صوت آلي؛ المزود والمعايرة والخصوصية وسياسة القرار الآلي بوابات مستقلة.

## 5) الاختبارات والبوابات

لا تعلن PASS أو CLOSED بناء على وثيقة فقط. لكل مرشح تنفيذ:

1. تحقق من SHA الحالي.
2. تحقق من `Himma CI — Quality Gate` لنفس SHA.
3. عند تغييرات UI تحقق من M04 Responsive Visual Gate وأدلته.
4. تحقق من M09 Release Readiness عندما ينطبق.
5. أصلح failure من الجذر، ولا تغير المنتج فقط لإرضاء اختبار قديم إذا كان عقد المنتج الحالي صحيحًا.

## 6) التسجيلات والبيانات

- لا تحذف DB/history/attempts/mastery لإصلاح seed أو runtime.
- التقارير وصفية ولا تنشئ mastery evidence.
- لا تخزن أسرارًا أو بيانات أطفال أو تسجيلات دراسة حقيقية داخل Git.
- النص الداخلي للقصة لا يظهر بدل التسجيل الصوتي للطالب.

## 7) التشغيل المحلي

اقرأ scripts/README/package metadata الحالية قبل التشغيل. استخدم طريقة التشغيل الموجودة في المستودع ولا تجعل Docker المحلي شرطًا على المستخدم. CI قد يستخدم service containers مستقلًا.

عند أي تعارض: **الكود الحالي + الاختبارات + CI لنفس SHA + المراجع النشطة أعلاه** هي المرجع التنفيذي.
