# إصدار مستودع هِمّة

- حالة السلسلة الحالية: `1.2.0-recovery`
- التاريخ: 2026-09-04
- المستودع: `7eaur/himma-`
- الفرع التنفيذي: `recovery/ui-media-admin-overhaul`

## التغييرات المعتمدة في سلسلة Recovery الحالية

- Runtime أكاديمي DB-only مبني من مصادر versioned وإسقاط deterministic.
- واجهة الطالب تعتمد Structured APIs وقالب تصميم موحد، مع إزالة طبقات `polish` وDOM patching.
- فصل Assessment completion الدائم عن آليات التطوير وإزالة duplicate route ownership.
- توحيد Activities route ownership.
- استبدال نشاط المسار السمعي بالمحتوى المعتمد للفهم السمعي وربطه بمهارة `الفهم السمعي المباشر` مع الحفاظ على التاريخ.
- إزالة `patch_db_runtime()`؛ القصص السمعية تأتي من المصدر versioned قبل الإسقاط.
- حذف Temporary Audio Skip بالكامل من UI/API/styles/runtime flags/backend.
- اعتماد المراجعة البشرية للمشرف لتسجيلات الطالب حتى ربط النموذج الصوتي الآلي المعتمد.
- إغلاق فجوات الصوت الثابتة: حزمة الصوت الحالية 54 أصلًا = 54 WAV + 54 MP3.
- `LET-01` أصبح التسجيل المعتمد **مَ** مع الحفاظ على الـID، وجرى اعتماد `SYL-13` = سَا، `WRD-29` = موز، `INS-01` و`INS-02` للقصتين.

## ملاحظة الإصدار

`FINAL` لا يعني Production Release. الإطلاق يظل خاضعًا لبوابات CI/UAT وM09 وموافقة المستخدم الصريحة. M08 كتحليل صوت آلي إنتاجي يبقى مستقلًا عن اكتمال الأصول الصوتية الثابتة.

مرجع الصوت: `docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.
