# هِمّة — سجل التنفيذ والتعديلات التفصيلي V3

**التاريخ:** 2026-09-02  
**المستودع:** `7eaur/himma-deployment-sandbox`  
**الفرع:** `main`  
**الغرض:** توثيق كل التعديلات الجوهرية التي نُفذت في الـSandbox، مع المشكلة والسبب الجذري والحل والاختبار والدليل.  
**هذه الوثيقة لا تمنح إذن Merge أو Production Release.**

---

# 1. قواعد القراءة

هذه الوثيقة تسجل التنفيذ الفعلي، لا النوايا. كل بند يميز بين:

- **المشكلة/الاحتياج**: ما الذي كان خطأ أو ناقصًا.
- **السبب الجذري**: لماذا حدث الخطأ.
- **الحل النهائي أو الحالي**: ما الذي تغير فعليًا.
- **الاختبار/الدليل**: كيف تم التحقق.
- **Commit/SHA**: مرجع التغيير عندما يكون متاحًا.
- **الحالة**: مغلق / معتمد / يحتاج تحقق / External-Gated.

إذا تعارض هذا الملف مع وثيقة أقدم، فالقرار الأحدث في هذه الوثيقة وفي `HIMMA_SANDBOX_FINAL_STATE_AND_MIGRATION_V3_2026-09-02_AR.md` هو المرجع.

---

# 2. ثوابت لم تتغير أثناء العمل

- Base approved content = **105** عنصرًا.
- Runtime total = **125** عنصرًا.
- Reinforcement total = **35**.
- Canonical skills = **44**.
- Pretest = **30**.
- Learning runtime = **65** (30 Core + 35 Reinforcement).
- Posttest = **30**.
- R1 المبكر لا يعود إلى شرط 10/10؛ القاعدة: >=6 Core + mastery >=85 + critical floor >=70 + full critical coverage + no reinforcement/review blockers + ترقية مستوى واحد فقط + no auto-demotion.
- L3 يحتاج full evidence قبل journey completion/posttest.
- M08 يبقى External-Gated.
- لا يتم اختلاق ملفات الصوت الناقصة. الفجوات الثابتة المعروفة تشمل `موز` و`سَا` حسب الحالة المعتمدة.
- Pre/Post محايدان ولا يكشفان correctness feedback أو hint يفضح الإجابة.

---

# 3. إعادة بناء عقد عرض الاختبار القبلي

## المشكلة

كانت واجهة الطالب معرضة لعرض نص المصدر الخام، وخصوصًا `prompt_text` الذي قد يحتوي stimulus + وصف + خيارات في نص واحد، ثم تعيد الواجهة عرض الخيارات مرة ثانية كأزرار.

## القرار

اعتماد عقد عرض منظم مستقل عن raw execution payload.

**Version:** `HIMMA-PRETEST-2026-09-01`

حقول العرض الأساسية:

- question_number
- section
- skill
- encouragement
- question_text
- instruction_text
- interaction_type
- stimulus
- options
- assets/media semantics

## PRE-Q03 — Regression حاسم

العرض الصحيح:

- السؤال: `انظر إلى الحرف، ثم اختر الشكل الآخر للحرف نفسه.`
- stimulus: `م` فقط.
- الخيارات منفصلة: `مـ / بـ / لـ / سـ` مع السماح بترتيب ثابت/مسموح دون تغيير الإجابة.
- ممنوع وضع وصف المصدر أو قائمة الخيارات داخل stimulus.

## تنفيذ Backend

- `services/api/seed_pretest_experience_2026_09_01.py`
- overlay لكل PRE-Q01..PRE-Q30.
- `step.prompt_text` لا يصبح عقد العرض للطالب.
- Q3 يثبت stimulus = `م` فقط.
- ordered sequence/build criteria محفوظة.
- source/history محفوظة.

## Seed/Bootstrap

`services/api/seed_all.py` أصبح يطبق الترتيب:

`base → reinforcement additions → corrections → Student V2 → pretest → learning/posttest projection`

`services/api/db/sandbox_bootstrap.py` يتحقق من baseline runtime ويعيد seed الآمن عند stale DB.

## اختبارات

- `test_pretest_experience_2026_09_01.py`
- `test_seed_all.py`
- تغطية Q1/Q3/Q4/Q19/Q24/Q30 + idempotency/versioning.

## مرجع commit مهم

`44a7214...` — approved pretest content + responsive assessment template.

**الحالة:** معتمد في الـSandbox.

---

# 4. توحيد الأنشطة والتقوية والبعدي مع قالب الاختبار

## المشكلة

كان لكل جزء من تجربة الطالب طبقات عرض مختلفة، ما أدى إلى اختلاف شكل الأنشطة عن الاختبار، وتداخل CSS/DOM enhancers، وظهور تكرار أو نصوص خام.

## الحل

- نفس لغة التصميم.
- الأنشطة تعيد استخدام:
  `apps/web/src/app/student/session/[id]/session.module.css`
- فصل العرض عن التنفيذ.
- Activity renderer يعتمد structured Learning Experience API فقط.

**Learning display version:** `HIMMA-LEARNING-2026-09-01-R2`  
**Posttest version:** `HIMMA-POSTTEST-2026-09-01`

## Commits بنيوية

- `436380bc94d845cd056bcc6f1a569721a561513f` — authoritative learning view payload.
- `a5f1b9d8b02f66f0e00af15c766f0d42e47e21e3` — إزالة activity layout enhancer/polish layers، والإبقاء على adaptive hold overlay فقط.
- `7e441b9f...` — activity single assessment-style renderer.
- `8d64ff4...` — lint follow-up.
- `085c451...` — حذف old `LearningExperienceEnhancer`.
- `9668d54...` — حذف old activity CSS overlay.
- `40fc073ae2e0514ed14037f2847597a5f1ba8905` — Regression يمنع raw duplicate prompt من الظهور.

**الحالة:** Activity architecture نظفت. Assessment نفسه ما زال يحتوي بعض legacy polish components ويجب عدم الادعاء بأنها حُذفت كلها.

---

# 5. حل تكرار stimulus والخيارات

## العرض المعيب

أمثلة ظهرت بصيغ مثل:

`سُ؛ سَ/سِ/سُ`

ثم نفس `سَ / سِ / سُ` تظهر مرة ثانية كخيارات.

## السبب الجذري

الواجهة كانت تستعمل أو تتأثر بنص raw prompt يحتوي بيانات مصدرية مركبة بدل structured fields.

## الحل

- stimulus لا يحتوي options serialization.
- listen questions التي ليس لها target text لا تعرض stimulus نصيًا مصطنعًا.
- الخيارات تأتي فقط من `options` في DB/API.
- Activity page تتجاهل legacy display fields في `/next`.

## Regression

اختبار يحقن عمدًا نصًا مثل `سُ؛ سَ/سِ/سُ` في endpoint التنفيذ الخام ويتحقق أنه لا يصل إلى UI.

**Commit:** `40fc073ae2e0514ed14037f2847597a5f1ba8905`.

**الحالة:** مغلق معماريًا في activity renderer.

---

# 6. العبارات التشجيعية والتلميح عند الخطأ

## القرار النهائي

قبل أول خطأ:

`message = encouragement`

بعد الخطأ/retry:

`message = hint`

ولا يظهر الاثنان معًا.

## القيود

- hint لا يكشف correct option مباشرة.
- UI لا يولد hint عام فوق hint المخزن.
- Pre/Post لا يتحولان لتجربة تعليمية تكشف الصحة أثناء القياس.

## Quality Gate

أضيفت اختبارات جودة تمنع تلميحات التعلم من طباعة خيار صحيح غير تافه مباشرة.

**الحالة:** مغلق في العقود الحالية.

---

# 7. نشاط الذاكرة البصرية

## القرار الذي صححه المستخدم

لا تختفي الصور تلقائيًا بعد مؤقت.

## السلوك النهائي

1. تظهر الصور.
2. يطلب من الطالب التركيز.
3. الصور تبقى ظاهرة.
4. الطالب يضغط `التالي` بنفسه.
5. بعدها يدخل recall/reorder phase.
6. التقييم بعد إعادة الترتيب.

**الحالة:** معتمد ويجب الحفاظ عليه عند النقل.

---

# 8. استبدال نشاط path/reading-direction بالفهم السمعي

## تسلسل القرار

- الأصل القديم كان path tracing.
- تم استبداله مؤقتًا باتجاه القراءة (`من أين نبدأ القراءة؟` / `يمين أم يسار؟`).
- المستخدم رفض هذا البديل لاحقًا وطلب نشاط قصة مسموعة + أسئلة فهم مباشر.

**القرار الأحدث يلغي البديل السابق.**

## النشاط الأساسي

**L1-CORE-09**  
الاسم: `استمع إلى القصة ثم أجب`  
المهارة: `الفهم السمعي المباشر`  
interaction: `listen_choose_one`

القصة internal only ولا تعرض نصيًا للطالب.

الجولات المباشرة:

1. أين ذهبت ليان؟ → إلى المزرعة.
2. مع من ذهبت ليان؟ → مع أبيها.
3. ماذا رأت قرب الشجرة؟ → أرنبًا أبيض.
4. ماذا أعطت للأرنب؟ → جزرة.
5. ماذا فعلت قبل العودة؟ → قطفت زهرة صفراء لأمها.

## التقوية

الاسم: `استمع واختر الإجابة`

قصة نادر والشاطئ، 5 أسئلة literal listening comprehension.

## قواعد التنفيذ

- story text internal only.
- زر استماع داخلي داخل المهمة مسموح ومطلوب.
- هذا مختلف عن global sound toggle الذي أزيل.
- replay مسموح.
- hint يستبدل encouragement عند الخطأ.
- لا inferential questions.

## Commits

- `a011e2df41be6cfb6661e46f691eaab8c7a42145` — content/spec definition.
- `b72fd90a16f40207a0896a84571255554124d0a3` — learning DB projection/reference implementation.
- `ff62e373856661cd177f98b6d6b92fb5b847fd1e` — verification/regression for approved auditory story replacement.

## ملاحظة taxonomy

يجب الحفاظ على **44 skills**. لا يسمح أن يضيف النقل مهارة 45 عرضيًا. عند النقل للمستودع الأصلي يجب مقارنة mapping النهائي ومعالجة skill replacement ضمن العدد المعتمد.

**الحالة:** المحتوى/العقد معتمدان في الـSandbox؛ media production الحقيقي يبقى مرتبطًا بتوفر الأصل الصوتي المعتمد.

---

# 9. POST-Q14

التصحيح النهائي:

- الهدف: `نَخْلَة`
- build order: `ن → خ → ل → ة`

ممنوع الرجوع إلى `نَخْل`.

**الحالة:** معتمد.

---

# 10. DB-only Student Runtime

## المشكلة

كان من الممكن أن تعتمد طبقة الطالب على repository content files أثناء runtime أو على parsing للنصوص.

## القرار البنيوي

`Import/Seed sources → PostgreSQL runtime snapshot → structured API → student renderer`

وليس:

`catalog/json/prompt → parse at request/render time`

## القواعد

- JSON/CSV/manifest للاستيراد والseed.
- جلسة الطالب لا تفتح ملفات المحتوى من المستودع.
- DB تحمل display contract + evaluation linkage + asset IDs.
- media binaries في object/media storage.

## اختبارات

- `test_db_only_student_runtime.py`
- `test_full_student_content_integrity.py`
- `test_student_content_quality.py`
- `test_student_question_experience.py`

**الحالة:** قاعدة معمارية معتمدة.

---

# 11. Exact Selection Cardinality

## المشكلة

كانت multi-select/sequence flows معرضة للسماح بالإرسال وفق قاعدة عامة بدل العدد الصحيح من DB.

## الحل

Backend يعيد `required_selection_count`:

- Single = 1.
- Multi = عدد correct options.
- Sequence/Build = عدد عناصر الترتيب المطلوبة.

UI لا يسمح بالنقص أو الزيادة ويُفعّل CTA عند العدد الصحيح فقط.

## Gate

`test_learning_selection_contract.py` يمر على جولات التعلم ويتحقق من cardinality من DB.

**الحالة:** مغلق.

---

# 12. Popup النجاح المتكرر

## المشكلة

مكوّن عالمي كان يستنتج success من كلمات داخل DOM مثل `أحسنت` و`رائع`، وبالتالي يعتبر encouragement نجاحًا حقيقيًا.

## الحل

- لا inference من النص.
- celebration مربوط بحالة إنجاز فعلية (`data-phase="done"` أو state equivalent).
- retry/error لا يولد success popup.

**الحالة:** معتمد.

---

# 13. إزالة أزرار الصوت العامة مع الحفاظ على listen controls التعليمية

## المطلوب

إزالة زر الصوت العام/العائم من تجربة الأنشطة والاختبارات، مع عدم كسر أسئلة الاستماع.

## الحل

- global floating sound toggle أزيل من learning/activity.
- assessment header sound control أُخفي ضمن shared styling.
- internal `.listenButton` يبقى عندما interaction يتطلب الاستماع.

## Commit

`52dfda34bda6297edc6cf81ddc3ed6a7a4faa2b6` — remove floating sound toggle from learning screens.

**الحالة:** معتمد.

---

# 14. تصغير حاوية التقدم والخطوط المرنة

## المطلوب

تعديل بسيط واحترافي، لا إعادة تصميم:

- تقليل مساحة progress تقريبًا 25%.
- question typography أصغر وأكثر مرونة.
- stimulus text مرن.
- options text مرن.
- CTA متناسق.

## التنفيذ

في shared assessment CSS:

`apps/web/src/app/student/session/[id]/session.module.css`

باستخدام responsive `clamp()`.

## Commit

`fcb303142147fc78163151de0290c743854dbe4f`

## قيد مهم

`clamp()` ليس AutoFit حقيقيًا ولا يضمن أن أي نص طويل سيبقى سطرًا واحدًا. إذا طُلب ضمان one-line fit لكل طول، الحل الصحيح هو shared `AutoFitText` بقياس فعلي (ResizeObserver/binary search)، وليس المزيد من CSS hacks.

**الحالة:** معتمد كتعديل responsive، لا يُدّعى أنه auto-fit مطلق.

---

# 15. اختفاء نص زر CTA «تأكيد والمتابعة»

## العرض

زر CTA كان موجودًا بصريًا لكن label اختفى، وفشل vertical/question experience test.

## محاولة أولى غير كافية

`81c067d71a9c0867196cce20885074312bf912eb`

حاول حماية CTA labels، لكنه لم ينجح لأن قاعدة أقدم تستخدم `!important` كانت أكثر تحديدًا/تغلبت عليه.

## السبب الجذري الحقيقي

داخل `assessment-polish.css` كانت توجد قاعدة legacy من شكل:

`button:last-child > span:last-child { display: none !important; }`

تم إنشاؤها قديمًا لإخفاء span يحتوي سهم CTA. بعد إزالة السهم من markup صار آخر `span` هو **نص الزر نفسه**؛ فبدأت القاعدة تخفي label.

## الحل

- حذف selector القديم الذي يفترض بنية CTA لم تعد موجودة.
- إيقاف DOM-structure styling الذي يقرر وظيفة العنصر من كونه `last-child`.
- جعل label مرئيًا ضمن القالب الفعلي بدل الاعتماد على override فوق legacy rule.

## Commit النهائي للمشكلة

`edaff8e01eb122e0d3252190e9c8a02db7874f8c`

## دليل الاختبار

بعد هذا الإصلاح صار `question-experience` الذي كان يفشل على CTA **PASS**. في run لاحق وصل Playwright إلى مشكلة أعمق بعد CTA، ما يثبت أن النص لم يعد هو blocker الأول.

**الحالة:** مشكلة اختفاء CTA label مغلقة.

---

# 16. مشكلة إعادة فتح جلسة Assessment مكتملة

## العرض

بعد إنهاء الاختبار ومراجعة التسجيلات، إذا أعيد فتح رابط الجلسة:

- الصفحة كانت تدخل `data-phase="error"` بدل عرض النتيجة المكتملة.

## التشخيص الأول

- `/assessment-view/session/{id}/next` كان يعتمد engine يطلب جلسة `in_progress` فقط.
- `/assessment/session/{id}/finish` كان يرفض `completed`.

## محاولة الإصلاح الأولى

Commit:

`8ed267de27e28a206d45a6df9e3b12ba22ced204`

التغيير داخل `assessment.py`:

- `get_next_item(... require_active=False)` ثم completed → `None`.
- `finish_session` completed + stored result → replay stored `final_score/assigned_level`.
- completed بلا stored result → `409` بدل fabrication.

ثم أضيف Regression:

`cf679d86dad9750945fc5e55f12d207fbf4f86e6`

ملف:

`services/api/test_assessment_completed_reopen.py`

## نتيجة CI

GitHub Actions run:

`33582241449`

- Frontend: **SUCCESS**.
- Backend: **FAILURE**.
- Integration: **SKIPPED** بسبب Backend failure.
- Backend summary: **194 passed / 2 failed**.
- الفاشلان هما اختبارا completed assessment reopen الجديدان.

## السبب الجذري الأعمق الذي كشفه الفشل

المشكلة ليست أن منطق `assessment.py` خاطئ فقط، بل أن الطلب لا يصل إليه أولًا.

`main.py` يسجل routers بهذا الترتيب الحاسم:

- `assessment_retake_router`
- `temporary_audio_skip_router`
- `assessment_router`

وفي `assessment_retake.py` يوجد route بنفس المسار:

`POST /assessment/session/{session_id}/finish`

وهو bridge:

`finish_assessment_and_select_official_attempt()`

هذا bridge يُستدعى قبل legacy `assessment.finish_session` ويستدعي:

`temporary_audio_skip.finish_assessment_with_optional_temporary_skips()`

والدالة الأخيرة ما زالت تشترط:

`session.status == "in_progress"`

لذلك completed replay في `assessment.py` لا يُستدعى أصلًا عند HTTP request.

## الحالة الحالية الدقيقة

- `/next` completed behavior أصبح يعمل حسب Regression.
- `/finish` completed replay **غير مغلق بعد** بسبب authoritative finish bridge route shadowing.
- لا يجوز اعتبار Quality Gate أخضر على HEAD `cf679d86...`.
- الحل النهائي يجب أن يوضع في authoritative finish bridge/policy، لا في legacy route فقط، مع الحفاظ على retake `official_for_reporting` semantics.

**الحالة:** مفتوحة — السبب الجذري موثق بدقة، وتحتاج إصلاح bridge ثم إعادة CI/Playwright.

---

# 17. التسجيلات الصوتية وإغلاق القبلي بعد المراجعة

## المشكلة الأصلية

30/30 قد تكتمل بينما تسجيل حقيقي ما زال `uploaded`، فتظل الجلسة in_progress، وبعد مراجعة آخر تسجيل كان يمكن أن تبقى الرحلة معلقة أو يظهر Resume بلا سؤال.

## السلوك المطلوب المعتمد

- pending real audio → awaiting review، وليس سؤالًا ناقصًا.
- temporary skip neutral.
- آخر مراجعة صالحة → finalize assessment.
- حفظ assigned level/current level في القبلي.
- posttest لا يعيد الطالب للخلف.
- rerecord_required وحده يعيد الطالب للجلسة.

## Regression موجود

`test_assessment_audio_review_completion.py::test_completed_pretest_waits_for_real_audio_then_finalizes_placement`

وقد ظهر **PASS** في run `33582241449`.

**الحالة:** مسار audio-review completion الأساسي يمر؛ completed reopen route ما زال بندًا مستقلًا مفتوحًا كما في القسم السابق.

---

# 18. Temporary Audio Skip

## الغرض

اختبار مؤقت فقط، academically neutral، لا يصنع ملف صوتي وهمي ولا score وهمي ولا reward/mastery evidence.

## القيود

- feature flag required.
- production/trial readiness يجب ألا تسمح باعتباره بديلًا للصوت الحقيقي.
- عند تعطيله يرفض الطلب.

## اختبارات run 33582241449

- temporary skip enabled creates no audio: PASS.
- disabled rejects skip: PASS.
- neutral for adaptation/rewards: PASS.
- pretest scoring excludes temporary skips from denominator: PASS.

**الحالة:** معتمد كتسهيل اختبار فقط، وليس production audio solution.

---

# 19. Bootstrap / seed invariants

`seed_all.py` وsandbox bootstrap يحافظان على:

- baseline 105.
- reinforcement 35.
- total 125.
- skills 44.
- V2 125.
- pretest 30.
- learning 65.
- posttest 30.

## دليل CI الأخير

في run `33582241449` قبل فشل Regression الجديد:

- catalog validation: PASS (`105 items, 44 canonical skills`).
- migrations upgrade/downgrade/upgrade: PASS.
- model drift check: PASS.
- base seed idempotency: PASS.
- `test_seed_all.py`: PASS.

**الحالة:** مغلق بالنسبة لهذه invariants.

---

# 20. جودة المحتوى الكامل

في آخر Backend run تم جمع **196 test**.

قبل فشل completed-reopen الجديد مرّت اختبارات جوهرية منها:

- DB-only runtime.
- full student content integrity.
- generated sequence assets.
- journey locks/transitions.
- selection cardinality.
- learning state machine.
- reinforcement end-to-end.
- full single candidate journey.
- placement scoring.
- posttest journey gate.
- pretest overlay 30 questions.
- recovery contracts.
- all 44 reinforcement skill map.
- reports/exports.
- speech alignment/pipeline.
- student-visible copy quality.
- Student Experience V2 all runtime items.
- path tasks replaced by approved auditory comprehension.
- POST-Q14 coherence.
- child-clear instructions.
- choice tasks have real options.
- L1 visible stimulus never serializes its choices.

هذا مهم: آخر failure مركز في **completed session finish replay contract**، وليس انهيارًا عامًا للمحتوى أو seed أو frontend.

---

# 21. النشر التجريبي

## Vercel

الـSandbox public alias:

`https://himma-deployment-sandbox.vercel.app`

الإصلاح الخاص باختفاء CTA (`edaff8e...`) وصل إلى Vercel READY حسب التحقق أثناء التنفيذ.

## Railway

المشروع:

`37b9445f-8545-49e0-a23f-590deff9111e`

Environment:

`3c926a7c-48b3-4e1e-99ab-8e3c39669890`

API service:

`3531bf9f-828c-425a-92f2-39cdf3aee51c`

إصلاح `8ed267de...` تم نشره بنجاح على Railway، ثم HEAD test commit `cf679d86...` دخل deploy أيضًا. لكن نجاح deploy لا يساوي نجاح Quality Gate؛ الـCI ما زال أحمر بسبب المسار المذكور أعلاه.

---

# 22. Commits مرجعية مهمة بترتيب موضوعي

- `44a7214...` — pretest + assessment template.
- `2023e084...` — structured learning/posttest seed.
- `d128e4fb...` — structured learning rounds + manual memory preview.
- `d4919a7e...` — structured posttest display.
- `4867f01e...` — non-blocking rollout seed lock.
- `7462f9ba...` — structured learning stimulus data.
- `436380bc...` — authoritative learning view.
- `7e441b9f...` — assessment-style learning renderer.
- `085c451...` — delete old enhancer.
- `9668d54...` — delete old CSS overlay.
- `40fc073...` — raw duplicate prompt regression.
- `52dfda34...` — remove global floating sound.
- `fcb30314...` — compact progress/responsive typography.
- `7268692b...` — old migration handoff docs (superseded where conflicting).
- `a011e2df...` — auditory comprehension replacement spec.
- `b72fd90a...` — auditory story DB projection.
- `ff62e373...` — auditory story verification.
- `81c067d7...` — first CTA visibility attempt; not sufficient.
- `edaff8e0...` — root CTA label fix.
- `8ed267de...` — first completed-session replay engine fix.
- `cf679d86...` — completed-session reopen Regression tests; current CI reveals route-shadowing gap.

---

# 23. ما لا يجوز إعادته أثناء النقل

- raw `prompt_text` parsing للعرض.
- options serialized داخل stimulus.
- DOM MutationObserver/Enhancer لإصلاح المحتوى بعد render.
- path/maze/tracing القديم.
- بديل اتجاه القراءة الذي تم إلغاؤه بعد اعتماد الفهم السمعي.
- auto-hide memory images timer.
- DOM word matching لاستنتاج success popup.
- global sound toggle فوق listening controls.
- selector من نوع `last-child span` لإخفاء عناصر CTA حسب ترتيب DOM.
- generic cardinality مثل `>=2` بدل DB count.
- fake audio/media assets لسد M08.
- اعتبار deploy READY دليلًا كافيًا بدل CI/functional evidence.

---

# 24. الحالة عند كتابة هذه الوثيقة

آخر HEAD وظيفي/اختباري قبل إضافة هذه الوثيقة:

`cf679d86dad9750945fc5e55f12d207fbf4f86e6`

آخر Quality Gate مفحوص:

`33582241449`

النتيجة:

- Frontend: SUCCESS.
- Backend: FAILURE — 194 passed / 2 failed.
- Integration: SKIPPED.
- blocker الحالي: completed assessment `/finish` replay يمر عبر retake/temporary-audio authoritative bridge قبل legacy assessment route.

لذلك: **لا يوجد Full Green claim في هذه النقطة.**

---

# 25. الخطوة التالية الصحيحة

1. إصلاح completed replay في authoritative finish bridge/policy (`assessment_retake` → `temporary_audio_skip`) مع عدم كسر official attempt selection.
2. تشغيل Backend tests والتأكد أن اختبارَي `test_assessment_completed_reopen.py` يمران.
3. تشغيل Integration/Playwright كامل.
4. إثبات CTA + vertical slice + completed reopen.
5. تحديث Final Verification بأرقام run/job/artifacts النهائية.
6. بعدها فقط اعتبار Sandbox migration candidate جاهزًا للمقارنة مع المستودع الأصلي.

---

**نهاية سجل التنفيذ V3.**
