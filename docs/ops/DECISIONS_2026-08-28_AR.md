# قرارات المراجعة والصيانة — هِمّة — 2026-08-28

هذا الملف يسجل أحدث القرارات. لا يحذف ADR التاريخي؛ عند التعارض الزمني يكون القرار الأحدث هو المرجع ما لم يكن موسومًا **PROPOSED**.

## D-2026-08-28-01 — المسار بعد القبلي

**معتمد.** القبلي يحدد نقطة البداية فقط، ثم المسار يصعد حتى L3:

- L1→L2→L3.
- L2→L3.
- L3.

Posttest بعد اكتمال L3 المطلوبة، لا بعد L1/L2 مباشرة.

## D-2026-08-28-02 — نتيجة النشاط

**معتمد.**

- >=80 pass.
- 70–<80 guided retry للجزء الضعيف/الخاطئ.
- <70 weakness + targeted reinforcement.

## D-2026-08-28-03 — الترقية

**معتمد.** 50/30/20 هو recent skill mastery profile ولا يسمح بتخطي Core. لا ترقية قبل 10/10 Core وعدم وجود gap علاجي غير محسوم.

## D-2026-08-28-04 — Level Session history

**معتمد.** كل مستوى يحتفظ بسياقه/تاريخه؛ الانتقال لا يعيد وسم التاريخ القديم.

## D-2026-08-28-05 — التقوية

**معتمد.**

`weakness → reinforcement → return to core → verification → continue`

لا random fallback ولا cross-level random fallback. verification bounded؛ عند التعثر ينتقل للمشرف.

## D-2026-08-28-06 — Reinforcement Mapping

**معتمد ومنفذ.**

`Skill → Skill Family → Approved candidates`

بدل exact skill-only كخيار وحيد.

## D-2026-08-28-07 — محتوى التقوية

**معتمد ومنفذ كإضافات Versioned.**

18 Micro-Reinforcement فوق 15 الأصلية؛ الإجمالي 33، وFull runtime catalog = 123 عنصرًا مع بقاء baseline الـ105 محفوظة.

## D-2026-08-28-08 — الصور الجديدة

**معتمد.** الصور الناقصة للتقويات ستُولد داخليًا لاحقًا وفق هوية هِمّة؛ لا يطلب من العميل البحث عنها حاليًا.

## D-2026-08-28-09 — الصوت الثابت

**معتمد.** 50 موجود + «موز» + «سَا» = 52 هدفًا. لا فجوات ثابتة جديدة معروفة بسبب التقويات الـ18.

## D-2026-08-28-10 — TEMP audio skip

**معتمد كمؤقت فقط.**

`HIMMA_TEMP_AUDIO_SKIP=true` يسمح بتجاوز recording tasks محايدًا دون fake file/AudioSubmission/score/mastery/reward/weakness/reinforcement evidence. عند false يعود recording requirement.

## D-2026-08-28-11 — نموذج الصوت

**معتمد تصميميًا.**

Reference-Guided Arabic Reading Analysis:

ASR → alignment to known text → Correct/Deletion/Insertion/Substitution → confidence → optional calibrated phoneme/haraka evidence → human review.

Whisper وحده ليس النظام الكامل. Real provider/calibration غير مكتملين.

## D-2026-08-28-12 — Student Product UI

**معتمد ومنفذ إلى baseline M04 الحالي.**

- Full-screen Learning Stage (`100dvh`).
- task-first hierarchy.
- companion character بارزة وذات تعليمات contextual.
- assessment/activity/reinforcement أقرب لنظام بصري موحد.
- responsive/reduced-motion/focus support.

لا يُرجع التصميم إلى Card صغيرة وسط فراغات كبيرة دون سبب منتجي واضح.

## D-2026-08-28-13 — Supervisor Product UX

**معتمد ومنفذ إلى baseline M05 الحالي.**

- Admin IA منظمة.
- Dashboard Action Center قبل الأرقام الثانوية.
- Student Profile Workspace Tabs بدل صفحة طويلة مزدحمة.
- reinforcement review مختصر expandable.
- Settings = Account / Security / Supervisors.

## D-2026-08-28-14 — المصطلح

**معتمد.** الظاهر للمستخدم «المشرف». `researcher` داخلي فقط حيث يلزم للتوافق البرمجي.

## D-2026-08-28-15 — Local infrastructure

**معتمد.** لا Docker محليًا لهِمّة. استخدام containers في CI لا يغير هذا القرار.

## D-2026-08-28-16 — Automatic Demotion

**PROPOSED — غير مثبت نهائيًا.**

التوصية الحالية: لا automatic demotion في normal journey بعد placement؛ يعالج الضعف داخل المستوى بالتقوية/الدعم، والتغيير الاستثنائي للمستوى يكون supervisor override بسبب موثق.

**ممنوع حذف demotion من الكود قبل Final/ADR.**

## D-2026-08-28-17 — Residual Reinforcement Gaps

**معتمد كسلوك أمان حتى اعتماد محتوى جديد.**

للثلاث فجوات:

- L2 sukoon word reading.
- L3 literal comprehension.
- L3 sentence building.

لا يختار النظام نشاطًا «قريبًا» بالحدس. السلوك الصحيح: explicit Safe Hold / supervisor path حتى اعتماد mapping أو Micro-Reinforcement.

## D-2026-08-28-18 — Accessibility Acceptance

**معتمد.**

لا تُعتبر الواجهة جاهزة لأن Desktop screenshot جميل أو لأن build أخضر فقط. M06 يجب أن يثبت:

- touch targets >=44px.
- visible focus / keyboard admin.
- no horizontal overflow.
- RTL صحيح.
- 200% zoom usable.
- accessible contrast للنص العادي.
- reduced motion.
- no implementation vocabulary child-facing.
- visual review عبر 360×800، 390×844، 768×1024، 1024×768، 1440×900.

لا يجوز خفض test expectation لمجرد إخضرار CI.

## D-2026-08-28-19 — Source Preservation

**معتمد.**

- baseline المحتوى الأصلي 105 يبقى محفوظًا.
- إضافات الصيانة منفصلة/versioned قدر الإمكان.
- لا وسائط مختلقة بدل gap معلن.
- لا قواعد أكاديمية تُغير بصمت أثناء أعمال UI/CI.
