# عقد الصوت التشغيلي ومراجعة المشرف — منصة هِمّة

**التاريخ:** 2026-09-04  
**الحالة:** ACTIVE / AUTHORITATIVE  
**المستودع:** `7eaur/himma-`  
**الفرع:** `recovery/ui-media-admin-overhaul`

## 1. الغرض

هذه الوثيقة هي المرجع التشغيلي الأحدث لأصول الصوت الثابتة ومسار تسجيل الطالب ومراجعة المشرف. عند التعارض مع وثيقة أقدم تخص فجوات الصوت أو التخطي المؤقت، تتقدم هذه الوثيقة مع الكود والـmanifest والاختبارات الحالية.

## 2. مصادر الحقيقة

- `assets/audio/HIMMA_AUDIO_V1/manifest.csv`
- `assets/audio/HIMMA_AUDIO_V1/wav_master/`
- `assets/audio/HIMMA_AUDIO_V1/web_mp3/`
- `assets/audio/HIMMA_AUDIO_V1/QA_REPORT.md`
- `packages/content/src/audio_asset_requirements_v1.json`
- `packages/content/src/l1_auditory_comprehension_v1.json`

لا يعد وجود صف في الـmanifest وحده إثباتًا كافيًا؛ الأصل المعتمد يجب أن يملك WAV وMP3 حقيقيين في الشجرة وأن يمر عبر validator.

## 3. الأصول المعتمدة التي أغلقت الفجوات

| Runtime ID | المعنى المعتمد | الاستخدام | الحالة |
|---|---|---|---|
| `LET-01` | `مَ` | المعرّف التاريخي نفسه، مع استبدال الباينري القديم بالمصدر المعتمد `SYL-15` | APPROVED REPLACEMENT |
| `WRD-29` | `موز` | `L1-CORE-06` الجولة 1 | APPROVED |
| `SYL-13` | `سَا` | `L2-CORE-06` الجولة 4 و`L2-REIN-08` الجولة 4 | APPROVED |
| `INS-01` | قصة ليان في المزرعة | `L1-CORE-09` الجولات 1–5 | APPROVED |
| `INS-02` | قصة نادر في الشاطئ | `L1-REIN-11` الجولات 1–5 | APPROVED |

لا ينشر `SYL-15` كمعرّف Runtime إضافي؛ بايتاته المعتمدة منشورة تحت `LET-01` للحفاظ على الاستدعاءات المستقرة.

## 4. إثبات الملفات الثنائية

تمت مقارنة الملفات المعتمدة المصدرية مع GitHub باستخدام حجم الملف وGit blob SHA المشتق من المحتوى. النتيجة: الأزواج العشرة مطابقة ومرفوعة فعليًا.

| الملف | bytes | Git blob SHA-1 | SHA-256 |
|---|---:|---|---|
| `wav_master/LET-01.wav` | 109446 | `a45e02d3c3aeaeefec98c785b8aa06e4be7ab2fd` | `a36a1694904dac06af41466ec03d39b384d266cefa78583126dfade8bc30ef57` |
| `web_mp3/LET-01.mp3` | 20942 | `6174edbcc403900d1456aef8e55b87a4386c6118` | `0041fb344c269fc7e1cf06c8c1bbcbc46a7f5c392007bc53aeca4556622d8fe8` |
| `wav_master/SYL-13.wav` | 134142 | `af01e4013504d042c37fb39984b666dbcdb3d9db` | `527897bc50c6803ef573071917ae8c4a73bbc3a1c8a7399bbab46028c3da6559` |
| `web_mp3/SYL-13.mp3` | 25539 | `417d3a3aecd32f4e134462840d00b7189f15c9fa` | `92cff71b964e725a613c312f641677fab8f6f3e1b75407f504130e29d425bbaf` |
| `wav_master/WRD-29.wav` | 123558 | `d3d7df3a528198da49e3262b92db72af99ef4ff8` | `6b13934e4ebadfc3f4b15e30f482e6ba42214dc0cde2b1d770ec5508a22bbded` |
| `web_mp3/WRD-29.mp3` | 23449 | `983990edfc5c5ed87e97862b97b323deb520b869` | `38f4beec9b4a0d28e9300732fefcbc87e45b7d299451b7f0a007475fde5d6cbd` |
| `wav_master/INS-01.wav` | 1915782 | `4733b98840a5783808806b4750fc3e2bff067d83` | `738a37b37f2dc36088dc037d3c601fa46561a42a307a9f52e84393ce26548929` |
| `web_mp3/INS-01.mp3` | 348622 | `11429e59fceea488a31f148ef9f69168f3936857` | `93a537f5650ea3b6942b54c7608716307979ae954c4c61c2516d7b9c1932e6a8` |
| `wav_master/INS-02.wav` | 1838166 | `6d65ec52eed83f4c781baee3b78376bb79508c93` | `702c681c07ed61711972096b236ee2a7c41e5df59f49bfeb1277f18e3b92a685` |
| `web_mp3/INS-02.mp3` | 334411 | `4357ad716f0f3e9be137c7a82103d8877d0a3c8f` | `5f2abeb3d069a6d6bf761797c006b72652ec89135fc20a82f70fbd220aab3ba2` |

حزمة `HIMMA_AUDIO_V1` الحالية تحتوي 54 أصلًا ثابتًا = 54 WAV + 54 MP3، ولا توجد فجوة صوت ثابت معلنة متبقية لهذه العناصر.

## 5. سياسة العرض للطالب

- لا substitution لأصل غير مطابق.
- لا Placeholder يعد أصلًا معتمدًا.
- لا يظهر نص القصة بدل التسجيل في النشاط السمعي؛ نص القصة داخلي لأغراض المرجع والتحقق فقط.
- إذا أصبح أصل مطلوب غير متاح في Runtime مستقبلًا، يفشل المسار مغلقًا بدل اختلاق إكمال أكاديمي.
- لا يوجد زر أو API أو Feature Flag لتخطي تسجيل الطالب.

## 6. تسجيل الطالب ومراجعة المشرف

الحالة المعتمدة حتى ربط نموذج التحليل الصوتي الآلي:

`student recording -> persisted recording -> supervisor audio review -> accepted / rerecord required -> academic continuation`

المشرف هو سلطة القرار الحالية للتسجيلات التي تحتاج مراجعة. حالة `waiting_audio_review` حالة عرض/تشغيل حقيقية وليست نجاحًا تلقائيًا، ولا تنشئ وحدها mastery أو score جديدًا.

## 7. النموذج الصوتي المستقبلي

الهدف المعماري:

`Reference-Guided Arabic Reading Analysis = ASR + reference alignment + C/D/I/S + phonemic helper evidence`

ربط النموذج الآلي عمل مستقبلي مستقل عن إغلاق فجوات الصوت الثابت. يجب قبل جعله سلطة إنتاجية اعتماد المزود، المعايرة، حدود الثقة، الخصوصية والاحتفاظ، وسياسة human override/audit.

لا يسمح للنموذج مستقبلًا بإعادة كتابة التاريخ الأكاديمي المقبول بصمت. أي migration لسلطة القرار يحتاج قرارًا صريحًا واختبارات وتدقيقًا.

## 8. حالة الإغلاق

- Fixed prompt/story audio assets: **CLOSED**.
- Required missing static audio: **0**.
- Temporary Audio Skip: **REMOVED COMPLETELY**.
- Supervisor human review: **ACTIVE / AUTHORITATIVE**.
- Automated ASR/scoring production integration: **FUTURE / NOT YET AUTHORITATIVE**.
- إغلاق M08 كتحليل صوت آلي إنتاجي لا يستنتج من إغلاق الأصول الثابتة؛ له بواباته الخاصة.

## 9. التحقق عند أي تعديل صوت لاحق

1. تحديث الأصل المعتمد والـmanifest معًا.
2. وجود WAV وMP3 حقيقيين.
3. مطابقة semantic text مع التسجيل المقصود.
4. تشغيل `packages/content/scripts/validate_catalog.py`.
5. تشغيل seed/projection وعدم استخدام patch لاحق للـRuntime.
6. تشغيل اختبارات Backend/Frontend/Integration ذات الصلة.
7. عدم إعلان PASS دون SHA ونتائج CI لذلك SHA.
