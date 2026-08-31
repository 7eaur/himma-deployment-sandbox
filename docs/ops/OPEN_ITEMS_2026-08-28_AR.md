# البنود المفتوحة — هِمّة — تحديث 2026-08-29

هذا الملف أحدث من `OPEN_ITEMS.md` القديم عند التعارض الزمني.

| ID | البند | الحالة/الأثر | نقطة الحسم |
|---|---|---|---|
| OI-02 | مزود ASR/العقد/الكلفة/نقل التسجيلات | يوقف Real Speech adapter النهائي | M08 قبل real provider |
| OI-03 | Confidence threshold/version | يوقف decision الآلي الموثوق للصوت | بعد تسجيلات ممثلة ومعايرة |
| OI-04 | مدة التدخل وعدد/مدة الجلسات البحثية | إعداد بحثي خارجي | قبل بدء الدراسة الفعلية |
| OI-05 | سياسة الاحتفاظ بتسجيلات الأطفال | يوقف production child audio | قبل real child audio |
| OI-06 | domain/hosting/HTTPS النهائي | يوقف النشر | M09 |
| OI-07 | بيانات/شعارات الجهة المشرفة للتقارير النهائية إن طلبت | يؤثر على branding النهائي للتقارير فقط | M07/M09 عند توفرها |
| OI-08 | تدوير أي أسرار استخدمت تاريخيًا والتحقق من production secrets | أمان إنتاجي | M09 |
| OI-10 | صوت «موز» | gap ثابت معلن؛ لا يُستبدل بـ«موزة» | قبل اكتمال الصوت الثابت |
| OI-11 | صوت «سَا» | gap ثابت معلن | قبل اكتمال الصوت الثابت |
| OI-12 | Automatic Demotion: هل يلغى من normal journey؟ | policy أكاديمية/منتجية غير محسومة؛ لا حذف صامت | قبل final adaptation sign-off/UAT |
| OI-13 | بوابة دقة القراءة/النص اللازمة للـL3 إذا كانت ستعتمد على الصوت الحقيقي | لا يجوز اختراع threshold | M08 calibration / academic approval |
| OI-M07-01 | supported per-skill research summary | المطلوب تلخيص evidence المصححة/الخاطئة المخزنة حسب المهارة دون إنشاء scoring rule جديد | قبل إغلاق M07 |
| OI-18 | Backup/restore + UAT + deployment/monitoring | يوقف release | M09 |

## بنود أُغلقت

- OI-M00: Run #206 الأحمر — **مغلق**؛ M00 أُنجز.
- Placement equal-weight scoring — **مغلق** عبر M01؛ 20/40/40 + readiness gate.
- M02 state machine الأساسي — **مغلق**.
- OI-M03-01 — L2 قراءة كلمات السكون — **مغلق**: الربط المعتمد يعيد استخدام `L2-REIN-02`.
- OI-M03-02 — L3 الفهم المباشر — **مغلق**: `L3-REIN-11` بخمس جولات معتمدة.
- OI-M03-03 — L3 بناء الجملة — **مغلق**: `L3-REIN-12` بخمس جولات معتمدة.
- Skill-family mapping — **مغلق للفجوات المعروفة**؛ 44 مهارة لها مرشح/مرشحات معتمدة من نفس المستوى، بلا random fallback.
- Student Profile الطويل — **أعيد بناؤه Tabs** في M05.
- Settings الطويلة — **قُسمت Account/Security/Supervisors** في M05.
- OI-M06-01 — mobile supervisor selector/touch-target regression — **مغلق**.
- OI-M06-02 — M06 screenshot review — **مغلق**.
- Responsive acceptance الأساسية على mobile/tablet/desktop — **مغلقة ضمن M06**.
- **OI-15 — صور تقويات التسلسل/الإضافات — مغلق.** تم إدخال 10 مشاهد WebP معتمدة، manifest مستقل، mapping صريح إلى `L1-REIN-12` و`L3-REIN-10`، اختبارات SHA/dimensions/media، وPlaywright browser fidelity ضمن Main Quality Gate. Accepted visual implementation HEAD `654c9946b4b5b6e254817b2611fdf6494aa2a65e`; Quality Gate #363 / `33222592452` أخضر بالكامل، وResponsive Visual Gate #28 / `33222592468` أخضر. Screenshot evidence: `playwright-report/screenshots/generated-sequence-assets.png` وتمت مراجعته بصريًا.
- OI-17 — بنية Research Reports Excel/PDF — **الجزء الخاص بالتصدير مغلق وظيفيًا**: Excel متعدد الأوراق + PDF فردي + PDF إجمالي + audit logging + UI endpoints موجودة ومثبتة على lineage أخضر. يبقى OI-M07-01 فقط قبل الإغلاق الكامل لـM07.

## الحقيقة الحالية للمحتوى

- 105 عنصرًا أصليًا محفوظًا كما هو.
- 18 إضافة تقوية v1.
- 2 إضافة تقوية v2 المعتمدة في 2026-08-29.
- إجمالي runtime = **125 عنصرًا**.
- إجمالي التقويات = **35**.
- لا توجد الآن فجوة تقوية معروفة تتطلب Safe Hold بسبب انعدام مرشح علاجي؛ Safe Hold يبقى آلية أمان عامة للحالات غير المتوقعة/غير المعتمدة وليس fallback عشوائيًا.

## قرارات محسومة ولا تعاد مناقشتها بلا سبب جديد

- الواجهة تستخدم «المشرف».
- الطالب يدخل بكود رقمي 6 أرقام.
- لا Docker محليًا لهِمّة.
- no random reinforcement / no cross-level random fallback.
- الصور الجديدة تستخدم فقط عندما لا يوجد أصل معتمد مطابق دلاليًا، مع reuse-first.
- TEMP_AUDIO_SKIP مؤقت ومحايد أكاديميًا.
- Reference-Guided Arabic Reading Analysis هو المعمار المستهدف للصوت.
- الصوت الثابت الحالي 50؛ المستهدف 52 بعد «موز» و«سَا».
- Placement يحدد نقطة البداية، ثم المسار يصعد إلى L3 قبل Posttest.
- >=80 pass، 70–<80 guided retry، <70 reinforcement path.
- لا ترقية مستوى قبل 10/10 core وعدم وجود دورة تقوية غير محسومة.

## أول إجراء

أكمل **OI-M07-01** كتقرير وصفي للمهارات من evidence المخزنة فقط، اربطه بالتصدير/الواجهة دون تغيير أي قرار أكاديمي، ثم أغلق M07 على Quality Gate أخضر. بعد ذلك يبدأ M09 release/UAT preparation، بينما M08 يبقى مسار الصوت الحقيقي المنفصل والمقيّد بمدخلات خارجية.
