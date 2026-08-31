# HIMMA MASTER CONTINUITY HANDOFF — 2026-08-31

> هذا الملف هو مرجع الاستمرارية التنفيذي الأحدث لمنصة **هِمّة**. الهدف منه أن تبدأ أي محادثة/وكيل جديد من الحالة الفعلية للمستودع دون فقد القرارات، الأدلة، المشاكل التي أُغلقت، أو الأعمال التي ما زالت مفتوحة.
>
> **قاعدة البداية:** لا تفترض أن SHA المكتوب هنا ما زال HEAD بعد هذا التحديث التوثيقي. أول خطوة دائمًا: اقرأ الفرع الحالي، آخر commit، وحالة GitHub Actions، ثم قارنها بما هو موثق هنا. لا تعتبر أي commit لاحق معتمدًا تلقائيًا حتى ترى بواباته الخضراء.

---

## 1) تعريف المشروع والهدف النهائي

هِمّة منصة تعليمية عربية RTL موجهة لطلاب الصف الثالث ممن لديهم صعوبات في القراءة. المسار المقصود للطالب:

`دخول بكود → اختبار قبلي → حساب/تحديد مستوى البداية → أنشطة المستوى → تقوية موجهة عند ضعف حقيقي → تحقق بالعودة للمهارة الأساسية → انتقال تكيفي بين المستويات → الوصول للمستوى الثالث → اختبار بعدي → تقارير المشرف`.

الهدف ليس مجرد تشغيل واجهات، بل منصة تعليمية قابلة للتدقيق تحفظ الدليل الأكاديمي، التاريخ، المحاولات، الزمن، التقوية، والتحقق دون أن تستبدل التقوية دليل إتقان المهارة الأصلية.

---

## 2) المستودع والفروع والحوكمة

- Repository: `7eaur/himma-`
- فرع العمل الحالي: `recovery/ui-media-admin-overhaul`
- لا تعدّل الفروع المقبولة التالية مباشرة:
  - `stage/04-production-slice`
  - `stage/02-content`
- لا تستخدم `reset --hard` أو `clean -fd` أو force push أو حذف تاريخ مقبول.
- لا تُسرّب أسرار أو بيانات أطفال أو تسجيلات خاصة.
- تشغيل Docker محليًا ليس شرطًا للمستخدم؛ GitHub Actions يستخدم service containers في CI وهذا مقبول. لا تغيّر هذا القيد إلى مطلب محلي.
- لا تعلن PASS/إغلاق مرحلة من دون SHA دقيق + Workflow run + نتائج jobs.

### آخر HEAD تنفيذي أخضر قبل كتابة هذا الملف

`fbf3e4c835e87c142422db9fe35f7dec60fee090`

Commit message:

`fix(R3): align retake authorization indexes with ORM`

أدلة CI لنفس SHA:

- Himma CI — Quality Gate #490
- Run ID: `33342958058`
- Backend: SUCCESS
- Frontend: SUCCESS
- Integration/Playwright: SUCCESS
- Himma M04 — Responsive Visual Gate #94
- Run ID: `33342958086`
- Result: SUCCESS

أي commit توثيقي بعد هذا الملف سيجعل HEAD أحدث؛ افحص بواباته أولًا قبل اعتماد SHA جديد كخط أساس.

---

## 3) مصادر الحقيقة وترتيب السلطة

عند التعارض استخدم هذا الترتيب:

1. أحدث توجيه صريح من المستخدم.
2. المحتوى المعتمد من العميل `المحتوى المعتمد من العميل.txt` والمواد الأصلية المرجعية.
3. الحالة التنفيذية المثبتة بالكود والاختبارات والـCI على الفرع الحالي.
4. وثائق Source of Truth / القرارات الحديثة.
5. HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md.
6. الوثائق التاريخية الأقدم.
7. screenshots/prototype مرجع UX فقط، لا يُسمح له أن ينسخ منطقًا قديمًا فوق runtime الحالي.

مهم: الملفات القديمة التي تقول 123 عنصرًا / +18 فقط أصبحت تاريخية. runtime الحالي = 125 عنصرًا.

---

## 4) المحتوى الأكاديمي الحالي

### الأصل المعتمد

- Pretest: 30
- Posttest: 30
- Core: 30 = 10 لكل مستوى
- Reinforcement أصلي: 15 = 5 لكل مستوى
- الإجمالي الأصلي: 105

### إضافات الصيانة

- Reinforcement additions v1: +18
- Gap closure v2: +2 في L3
- Full runtime catalog: **125**
- Total reinforcement: **35**
- Skills: **44**

تم إغلاق فجوات تقوية سابقة:

- L2 `sukoon_word_reading` → دعم معتمد موجود.
- L3 `literal_comprehension` → `L3-REIN-11`.
- L3 `sentence_building` → `L3-REIN-12`.

لا تستخدم تقوية عشوائية ولا cross-level fallback.

---

## 5) قواعد الاختبار القبلي وتحديد البداية

الاختبار القبلي = 100 نقطة موزعة:

- readiness: 20
- word building/reading: 40
- fluency/comprehension: 40

القاعدة المعروفة:

- readiness أقل من 12/20 يفرض L1.
- total أقل من 50 → L1.
- 50 إلى أقل من 80 → L2 ما لم توجد بوابة قراءة تمنع.
- L3 يحتاج total مرتفعًا + passing reading gates + text accuracy gate عند توفر threshold معتمد.

**ممنوع اختراع threshold غير موجود في المصدر.** Placement يحدد نقطة البداية ولا يعد دليلًا دائمًا لإكمال الرحلة.

الاختبار القبلي والبعدي neutral: لا صحة/خطأ بعد كل سؤال، لا hints تكشف الإجابة، لا stars/rewards لكل سؤال قبل النهاية.

---

## 6) قواعد التعلم والتكيف الحالية

### على مستوى النشاط

- >=80: PASS
- 70..<80: GUIDED_RETRY
- <70: WEAKNESS_EVENT → targeted reinforcement

### mastery evidence

أحدث 3 محاولات valid فقط بأوزان:

- الأحدث 50%
- السابقة 30%
- الأقدم 20%

الـneutral evidence مثل تخطي فجوة وسائط معلنة أو صوت غير محلل لا يُحسب خطأ ولا يدخل denominator/mastery.

### R1 — سياسة الانتقال المبكر المحدثة

الفرع الحالي يحتوي الآن على قواعد انتقال مبكر بعد **6 أنشطة Core على الأقل** بدل القاعدة التاريخية التي كانت تنتظر 10/10 في L1/L2. الاختبارات الحالية تقفل أن:

- mastery promotion threshold = **85**.
- critical-skill floor = **70**.
- يجب تحقق minimum core count = **6**.
- يجب أن تكون critical-skill coverage كاملة حسب policy.
- أي reinforcement unresolved أو supervisor review pending يمنع promotion.
- automatic demotion غير مفعل؛ الضعف المتكرر يبقى support على نفس المستوى.
- الانتقال من L1/L2 يكون مستوى واحد فقط.
- L3 لا يعلو فوق 3 ويظل اكتمال الرحلة مرتبطًا بدليل المستوى الثالث الكامل قبل posttest.

**ملاحظة مهمة جدًا للمحادثة الجديدة:** هذه القاعدة أحدث من وثائق قديمة تقول “لا promotion قبل 10/10”. لا تعيد القاعدة القديمة من الذاكرة. افحص `test_learning_state_machine.py`, `test_adaptation.py`, policy loader/runtime قبل أي تغيير أكاديمي جديد.

---

## 7) Reinforcement lifecycle

المسار المعتمد في runtime:

`ضعف حقيقي → قرار support → نشاط تقوية mapped لنفس skill family/level → إكمال التقوية → إعادة فتح source core attempt → verification للخطوات الفاشلة فقط → verified أو escalated → متابعة المسار`.

ملفات أساسية:

- `services/api/reinforcement_cycles.py`
- `services/api/db/reinforcement_models.py`
- `services/api/adaptation_runtime.py`
- `services/api/reinforcement_review.py`

خصائص مهمة:

- cycle durable ومربوط decision/source attempt.
- failed step IDs تُستخرج من evidence حقيقي فقط.
- media-gap skip لا يتحول إلى failed evidence.
- verification bounded، والحد الحالي في model = 2 rounds افتراضيًا.
- failure بعد الحد → `escalated` للمشرف.
- التقوية لا تستبدل الأصل: source core يُعاد للتحقق.

---

## 8) R2 — إصلاح session handoff بعد early promotion

تم اكتشاف regression حقيقي بعد إدخال early promotion: endpoint `/activities/session/{id}/next` كان قد يغلق جلسة المستوى القديم أثناء التكيف ثم يعيد item مرتبطًا بجلسة مغلقة؛ submit التالي يرجع 404 “جلسة التعلم غير موجودة أو انتهت”.

تم إنشاء bridge في:

- `services/api/activities_v4.py`

وتم تسجيله قبل legacy activities router من `main.py`.

السلوك الحالي:

- بعد `prepare_next_for_student()` إذا حصل promotion وتم إنشاء session جديدة، يتم الانتقال إلى `prepared.session_id` بدل مواصلة session المغلقة.
- payload الناتج يحمل session_id الفعلي النشط.
- normal core selection يفضّل critical skill ناقصة/ضعيفة evidence عند توفر policy، ثم order_index كـ deterministic fallback.

الـclient/tests يجب أن يتعاملوا مع session_id في payload كمرجع authoritative عند تغير المستوى.

---

## 9) R3 — supervisor-authorized assessment retake history

أحدث سلسلة commits قبل هذا handoff تعالج عقد إعادة الاختبارات بتفويض المشرف مع الحفاظ على التاريخ وعدم كسر جلسات Core. رسائل commits الموثقة تشمل:

- `fix(R3): scope assessment attempt uniqueness to pre/post only`
- `fix(R3): keep Core sessions outside retake uniqueness`
- `test(R3): lock supervisor-authorized retake history contract`
- `fix(R3): align retake authorization indexes with ORM`

آخر SHA من السلسلة أخضر: `fbf3e4c...`.

المحادثة الجديدة يجب أن تعتبر هذا الجزء مدمجًا حاليًا، لكن قبل أي تمديد له راجع migration/model/tests الفعلية ولا تبنِ semantics جديدة من أسماء commits فقط.

---

## 10) تجربة الطالب — QX / Student Experience v2

تمت إعادة بناء تجربة السؤال لتكون مناسبة لطفل صف ثالث بدل واجهة generic.

ملفات محورية:

- `apps/web/src/app/student/activity/[id]/page.tsx`
- `apps/web/src/app/student/layout.tsx`
- `apps/web/src/app/student/student-experience.css`
- `apps/web/src/components/StudentExperienceEffects.tsx`
- `apps/web/tests/e2e/question-experience.spec.ts`
- `services/api/content_runtime.py`
- `services/api/test_student_question_experience.py`

قواعد UX:

- عنوان السؤال يشرح المهمة الفعلية، لا “اختر الإجابة الصحيحة”.
- الإجابات أسفل السؤال وبـtouch targets مناسبة.
- لا يظهر “مهمة واحدة في كل مرة” كنص UI؛ هذه قاعدة تصميم فقط.
- hint/success/error contextual في learning فقط.
- formal assessment يبقى neutral.
- أصوات خفيفة للانتقال/اختيار/نجاح/محاولة/وسام مع mute وreduced-motion.
- لا تعتمد sidebar mascot دائم يزاحم السؤال.
- لا blur/opacity overlay على الصفحة أثناء السؤال.

أمثلة copy المعتمدة:

- `استمع إلى صوت الحرف، ثم اختر الكلمة التي تبدأ بهذا الصوت.`
- `استمع إلى الكلمة، ثم اختر الحرف الذي تسمعه في بدايتها.`
- `استمع إلى الكلمة، ثم اختر الحرف الذي تسمعه في نهايتها.`
- original L1 Core onset pair: `استمع إلى الكلمتين. هل تبدأان بالصوت نفسه أم بصوتين مختلفين؟`

لا تغيّر semantic الأصل المعتمد لمجرد توحيد واجهة.

---

## 11) إصلاحات الخيارات والمحتوى البصري

تمت إصلاحات source-grounded لخيارات كانت ناقصة/غير متماسكة، منها:

- L1-CORE-03 forms options.
- L1-REIN-03 three-image choices.
- L2-REIN-04 three-image word matching.
- POST-Q08 / POST-Q09 choices.
- L3 comprehension choices.

full question audit يتحقق من 125 item و35 reinforcement وأن كل choice task لديه options حقيقية وتعليمات غير generic.

### الصور التعليمية

تم توليد 10 مشاهد sequence مطابقة للمفاهيم المطلوبة وإدخالها كـWebP تحت generated educational namespace:

1. غسل اليدين
2. الأكل
3. فتح الكتاب
4. سقي الزهرة
5. لبس الحذاء
6. الخروج من المنزل
7. دخول المكتبة
8. الذهاب إلى الشاطئ
9. اللعب بالرمل
10. تنظيف المكان

IDs: `HIMMA-GEN-SEQ-001..010`.

الـvisual plan أصبح `generate: []`.

لا تستخدم fuzzy mapping يجعل مشهدًا غير مطابق للمفهوم. beach labels تم تصحيحها سابقًا.

---

## 12) الصوت والتحليل الصوتي

### static audio

- موجود: 50
- فجوتان مؤكدتان: `موز` و`سَا`
- target: 52
- `موزة` ليست بديلًا عن `موز`.

### temporary skip

`HIMMA_TEMP_AUDIO_SKIP=true` للاختبار فقط في read_aloud/timed_read_aloud:

- لا mic/upload/review.
- neutral.
- excluded denominator/mastery/adaptation/reward.

عند false يجب استعادة التسجيل الحقيقي.

### M08 architecture

القرار: **Reference-Guided Arabic Reading Analysis**:

ASR → alignment against known reference → Correct/Deletion/Insertion/Substitution → phonemic helper evidence.

الموجود حاليًا يشمل pipeline/alignment scaffolding واختبارات لغياب provider والتعامل المحافظ مع calibration، لكن **M08 الحقيقي غير مكتمل** لأن ما يلي خارجي/مفتوح:

- provider فعلي مناسب للعربية/أطفال.
- calibration dataset/thresholds.
- privacy/consent/retention policy.
- production cost/latency/retry limits.
- ربط موثوق للنتيجة بالقرار الأكاديمي بعد الاعتماد.

لا تدّعِ أن ASR production جاهز.

---

## 13) التقارير والمشرف — M07

تم تنفيذ تقارير persisted وليست إعادة حساب صامت:

- pre/post summary.
- absolute improvement.
- relative improvement فقط عندما تكون معرفة رياضيًا.
- start/current/final level.
- assessment/learning time.
- attempts/completed attempts.
- reinforcement cycles summary.
- cohort summary.
- XLSX multi-sheet.
- individual PDF.
- cohort PDF.
- audit logging للتصدير.
- per-skill report من persisted graded evidence فقط.

قاعدة: per-skill report **وصفي** ولا يصبح mastery/adaptation rule تلقائيًا.

واجهة الإدارة تستخدم لفظ **المشرف** للمستخدم النهائي حتى لو بقي internal role/researcher في backend لأسباب compatibility.

---

## 14) Responsive / Accessibility / visual gates

مصفوفة responsive المرجعية:

- 360x800
- 390x844
- 768x1024
- 1024x768
- 1440x900

قواعد أساسية:

- no horizontal overflow.
- primary touch controls >=44px.
- RTL/mobile-first.
- prefers-reduced-motion respected.
- student primary CTA يجب ألا يخرج عن viewport.

الفرع الحالي لديه Responsive Visual Gate مستقل بالإضافة للـMain Quality Gate.

---

## 15) الهوية البصرية

ألوان هِمّة الحالية:

- Blue `#347FD9`
- Green `#51B985`
- Yellow `#FFC857`
- Navy `#20364D`
- Background `#F7FBFF`
- Border `#DCE8F2`

الخطوط:

- Tajawal — واجهة الطفل.
- IBM Plex Sans Arabic — المشرف/التقارير.
- Noto fallback.

لا تعيد تصميم المنصة باتجاه AI/glassmorphism أو clutter. الأولوية للوضوح، الطفل، لمس سهل، task focus، hierarchy، وإشارات بصرية قليلة وذات معنى.

---

## 16) سجل المحطات المهمة السابقة

محطات تاريخية مفيدة عند التحقيق، وليست كلها HEAD الحالي:

- B00 remote baseline: `e5fafe7...`.
- M06 accepted implementation: `cdb02c75ad33d1b002ee1fdb84ecf1fee3dc57d4`.
- Generated media/browser fidelity: `654c9946b4b5b6e254817b2611fdf6494aa2a65e`.
- QX final closure: `d6bab135e46ed93de3ac98236c5aa78e804c27ab` with Quality Gate #443 run `33274298950` and Responsive #49 `33274298939` both green.
- R1/R2/R3 work بعد QX غيّر منطق promotion/session/retake؛ لا ترجع إلى d6bab كـHEAD وظيفي إذا كان الفرع الحالي أخضر بعده.
- آخر green executable before this documentation: `fbf3e4c835e87c142422db9fe35f7dec60fee090`.

---

## 17) ما أُغلق فعليًا وما لا يزال مفتوحًا

### مغلق/منفذ حاليًا

- استعادة baseline والبوابات.
- approved catalog + runtime additions = 125.
- placement scoring structure/gates دون اختراع threshold مجهول.
- activity learning bands.
- targeted reinforcement mapping + durable cycles + verification/escalation.
- no automatic demotion.
- student question UX overhaul.
- media fidelity و10 sequence scenes.
- supervisor UX baseline.
- responsive/accessibility baseline.
- M07 persisted reports + exports + per-skill descriptive evidence.
- R1 early promotion policy (6 Core min, 85 mastery, 70 critical floor + gates).
- R2 active-session handoff across promotion.
- R3 supervisor-authorized pre/post retake history/index alignment.

### مفتوح ويحتاج عملًا/مراجعة

1. **M08 real speech analysis** — أكبر gap production حقيقي.
2. إضافة الصوتين الثابتين `موز` و`سَا` من مصدر موثوق/معتمد ثم manifest/runtime/tests.
3. **M09 Release/UAT**: full journey UAT، deployment readiness، production env/runbook، backup/restore، monitoring، privacy, data retention, support/rollback, release checklist.
4. مراجعة end-to-end للسياسة الأكاديمية الجديدة R1 مع العميل/مصدر القرار إن لم تكن موثقة خارج الكود؛ لا تغيّرها صامتًا، لكن لا ترجع عنها تلقائيًا لأنها الآن مقفلة بالاختبارات.
5. مراجعة retake UX في الواجهة إن كان backend contract أُغلق قبل إكمال أفضل UI للمشرف.
6. visual review نهائي للطالب والمشرف على artifact/screenshots بعد كل تغيير UI كبير.
7. إزالة/تحديث الوثائق التاريخية المتناقضة تدريجيًا بحيث تشير لهذا handoff بدل خلق مصادر حقيقة موازية.

---

## 18) أول خطوات المحادثة الجديدة — إلزامية

نفّذ بالترتيب دون سؤال المستخدم عن أمور يمكن حسمها من المستودع:

1. اقرأ هذا الملف كاملًا.
2. اقرأ `docs/ops/STATUS.md` و`docs/ops/progress.json`.
3. افحص branch `recovery/ui-media-admin-overhaul` وHEAD الحالي.
4. افحص آخر Main Quality Gate وResponsive Visual Gate لنفس HEAD.
5. إذا HEAD أحدث من آخر green المذكور هنا:
   - اقرأ commits الجديدة.
   - لا تعتبرها مقبولة حتى CI green.
   - أصلح أي failure حقيقي مع regression test.
6. راجع `HIMMA_CORRECTIVE_EXECUTION_ROADMAP_V2_AR.md` لكن لا تسمح لوثيقة أقدم أن تتغلب على runtime/قرارات أحدث.
7. ابدأ من **أول بند مفتوح مثبت**، والأولوية الافتراضية الآن هي M09 readiness/UAT بالتوازي مع بقاء M08 external-gated، ما لم يكن CI الحالي أحمر أو يظهر regression أعلى أولوية.
8. لا تنتقل إلى إطلاق production أو merge فروع أساسية من نفسك.

---

## 19) قائمة فحص عند أي تغيير جديد

قبل commit:

- هل التغيير يحافظ على 105 original source items؟
- هل runtime ما زال 125 / reinforcement 35؟
- هل formal pre/post بقي neutral؟
- هل neutral audio/media evidence مستبعد من scoring؟
- هل reinforcement targeted ولا random/cross-level؟
- هل verification يعود للأصل؟
- هل early promotion gates الحالية لم تتغير دون قرار صريح؟
- هل no automatic demotion بقي صحيحًا؟
- هل session handoff بعد promotion صحيح؟
- هل retake history لا يمس Core uniqueness بطريقة خاطئة؟
- هل UI Arabic RTL + touch + responsive + reduced motion؟
- هل backend/frontend/integration/Playwright green؟
- هل Responsive Visual Gate green إذا التغيير يمس UI/runtime المحتوى؟

---

## 20) ممنوعات الاستمرار

- لا تعيد بناء المشروع من الصفر.
- لا تستبدل runtime الحالي بprototype.
- لا تعدل original approved content semantics بلا مصدر.
- لا تستخدم أسماء الملفات وحدها لفهم المحتوى؛ اقرأ الكود والاختبارات.
- لا تحوّل report evidence إلى mastery rule.
- لا تعتبر temporary audio skip حلًا production.
- لا تستخدم `Whisper` وحده كحكم قراءة نهائي دون alignment/reference/calibration.
- لا تسمح بposttest قبل اكتمال journey المعتمد للمستوى الثالث وتفعيل المشرف.
- لا تقل “كل شيء مكتمل” طالما M08/M09 والأصوات المفقودة ما زالت مفتوحة.

---

## 21) صيغة التقرير المطلوبة عند الاستمرار

عند نهاية أي دفعة عمل، اكتب للمستخدم باختصار عملي:

- ما الذي فُحص.
- ما المشكلة التي ثبتت.
- ما الذي تغير فعليًا.
- الملفات/commits.
- HEAD الحالي.
- CI run IDs ونتائج backend/frontend/integration + responsive.
- ما الذي تبقى بالضبط.
- لا تقل PASS إذا run ما زال queued/in_progress.

---

## 22) الخلاصة التنفيذية للمحادثة القادمة

المشروع لم يعد عند QX فقط؛ بعده تم إدخال **R1 early-promotion gates**, ثم إصلاح **R2 session handoff**، ثم **R3 authorized retake/index history**. آخر تنفيذ موثّق قبل هذا الملف هو `fbf3e4c...` وبواباته الرئيسية والبصرية خضراء. المحتوى runtime 125، التقوية 35، الصور المولدة المطلوبة مغلقة، QX مغلق، M07 التقارير منفذ، بينما **M08 الحقيقي للصوت** و**M09 release/UAT** وباقي صوتي `موز` و`سَا` هي الأعمال الكبيرة المفتوحة.

ابدأ دائمًا من HEAD/CI الفعليين، ثم أكمل أول gap حقيقي بدل إعادة تدقيق ما أُغلق أو استرجاع قواعد قديمة من الذاكرة.
