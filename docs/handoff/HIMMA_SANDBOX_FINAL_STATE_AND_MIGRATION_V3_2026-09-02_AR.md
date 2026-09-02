# هِمّة — الحالة النهائية الحالية وخطة النقل V3

**التاريخ:** 2026-09-02  
**المصدر:** `7eaur/himma-deployment-sandbox` / `main`  
**الهدف لاحقًا:** `7eaur/himma-`  
**الفرع الرسمي المستهدف عند النقل:** `recovery/ui-media-admin-overhaul`  
**الحالة:** مرجع نقل وتدقيق فقط. لا Merge ولا Production Release دون اعتماد صريح.  

هذه الوثيقة **تحل محل** وثائق Handoff الأقدم في أي نقطة تعارض، خصوصًا قرارات نشاط المسار/اتجاه القراءة وحالة CTA وcompleted assessment reopen.

---

# 1. مبدأ النقل

لا تنقل تاريخ تجارب الـSandbox حرفيًا. لا تعمل cherry-pick عشوائي لكل commits.

الطريقة الصحيحة:

1. قارن ملفات المستودع الأصلي بالحالة النهائية في الـSandbox.
2. استخرج التغييرات النهائية فقط.
3. حافظ على invariants الأكاديمية والـIDs والتاريخ.
4. انقل المعمارية النهائية، لا طبقات التجربة التي حُذفت لاحقًا.
5. شغّل Quality Gate في المستودع الأصلي بعد كل حزمة منطقية.

المعمارية المستهدفة:

`Approved source/import → versioned seed → PostgreSQL runtime snapshot → structured student API → deterministic renderer`

لا تستخدم:

`raw prompt → parsing/regex/DOM patch → student UI`

---

# 2. ثوابت قبول النقل

يجب أن تبقى الأرقام التالية بعد النقل:

- Base = **105**.
- Runtime total = **125**.
- Reinforcement = **35**.
- Skills = **44**.
- Pretest = **30**.
- Learning = **65**.
- Posttest = **30**.

أي نقل يرفع skill count إلى 45 أو يغيّر runtime total أو يحذف stable keys يعتبر regression.

---

# 3. الإصدارات المعتمدة للعرض

- Student Experience: `HIMMA-STUDENT-EXPERIENCE-2.0`
- Pretest: `HIMMA-PRETEST-2026-09-01`
- Learning: `HIMMA-LEARNING-2026-09-01-R2`
- Posttest: `HIMMA-POSTTEST-2026-09-01`

Overlay/seed ordering المطلوب:

`base → reinforcement additions → corrections → Student V2 → pretest overlay → learning/posttest projection`

---

# 4. مصدر الحقيقة أثناء Runtime

ملفات source/catalog/manifest ليست Student Runtime API.

أثناء الجلسة:

- DB هي snapshot التنفيذية.
- structured API ترجع حقول العرض.
- UI لا يفتح JSON/CSV من المستودع.
- UI لا يقرأ `prompt_text` لتحديد stimulus/options.
- media binaries خارج DB، بينما DB تحفظ asset IDs/semantics/linkage.

---

# 5. Pretest contract

لكل سؤال:

- question_number
- section
- skill
- encouragement
- question_text
- instruction_text
- stimulus
- interaction_type
- options
- assets/media semantics

## PRE-Q03 lock

- question: `انظر إلى الحرف، ثم اختر الشكل الآخر للحرف نفسه.`
- stimulus: `م` فقط.
- choices منفصلة.

أي ظهور للنص المصدر الكامل أو options داخل stimulus يعتبر blocker.

---

# 6. Learning/Posttest renderer

الأنشطة تستخدم نفس لغة وقالب الاختبار عبر shared assessment CSS.

الـlearning student payload هو المصدر الوحيد لعرض الجولة.

الحقول المطلوبة منطقيًا:

- round_number
- round_total
- skill
- question_text
- instruction_text
- stimulus_text
- encouragement
- hint
- interaction_type
- options
- required_selection_count
- assets/media_gaps
- retry/attempt state

لا تعاد طبقات:

- `LearningExperienceEnhancer`
- activity DOM polish overlay
- raw prompt parser
- MutationObserver content correction

---

# 7. Feedback messaging

Learning:

`retry ? hint : encouragement`

- لا يظهر الاثنان معًا.
- hint لا يكشف الإجابة مباشرة.

Pre/Post:

- neutral measurement.
- لا correctness reveal أثناء الاختبار.

---

# 8. Memory activity

- images visible أولًا.
- no automatic timer hide.
- الطالب يضغط `التالي`.
- recall/reorder بعد ذلك.

هذا السلوك override لأي نص مصدر أقدم يقول إن الصور تختفي تلقائيًا.

---

# 9. L1 path replacement — القرار النهائي

لا path tracing.

لا `من أين نبدأ القراءة؟`.

لا `يمين أم يسار؟`.

البديل النهائي:

## Core

`L1-CORE-09 — استمع إلى القصة ثم أجب`

- skill: الفهم السمعي المباشر.
- interaction: listen_choose_one.
- story internal only.
- five literal comprehension rounds.

## Reinforcement

`استمع واختر الإجابة`

- قصة نادر والشاطئ.
- five direct literal questions.

## Media rule

internal listen control مطلوب؛ global sound toggle غير مطلوب.

لا يعتبر voice مؤقت غير معتمد production asset.

---

# 10. L1-CORE-06 / POST-Q14 locks

`L1-CORE-06`: `هل الصوت يطابق بداية الكلمة؟` مع choices `متشابهان / مختلفان`.

`POST-Q14`:

- target `نَخْلَة`
- order `ن → خ → ل → ة`

---

# 11. Visual/UI decisions

تعديلات التصميم الأخيرة كانت تحسينات صغيرة فوق القالب الموحد:

- إزالة global/floating sound toggle.
- الحفاظ على internal listen button.
- progress panel compact تقريبًا 25%.
- responsive question/stimulus/options typography.
- shared CSS بدل activity-specific clone.

`clamp()` responsive فقط؛ لا يُوصف بأنه guaranteed auto-fit.

---

# 12. CTA visibility contract

## ممنوع

Selectors تعتمد على بنية DOM مثل:

`button:last-child > span:last-child { display:none !important; }`

لإخفاء سهم أو decoration.

## السبب

بعد تغير markup أصبح `last span` هو CTA label، فاختفى `تأكيد والمتابعة`.

## الإصلاح المرجعي

Commit:

`edaff8e01eb122e0d3252190e9c8a02db7874f8c`

المطلوب في الأصل هو نقل **المبدأ النهائي**: style classes/semantic elements بدل nth/last-child hacks.

---

# 13. Assessment completion / reopen contract

## الحالة المطلوبة نهائيًا

لجلسة `in_progress`:

- next يعيد السؤال التالي أو null عند اكتمال الأسئلة.
- finish يحسب/يحفظ النتيجة حسب authoritative scoring policy.

لجلسة `completed`:

- next = `null`.
- finish المتكرر = replay للنتيجة المخزنة نفسها.
- لا إعادة scoring.
- لا إعادة تغيير current level.
- لا إعادة تعطيل/تفعيل posttest side effects.
- completed بلا stored result = explicit error؛ لا fabrication.

## ملاحظة معمارية حرجة

في الـSandbox يوجد finish route shadowing:

`assessment_retake_router` مسجل قبل `temporary_audio_skip_router` و`assessment_router`.

`assessment_retake.py` يملك:

`POST /assessment/session/{session_id}/finish`

ويستدعي `temporary_audio_skip.finish_assessment_with_optional_temporary_skips()`.

لذلك أي إصلاح يوضع فقط داخل `assessment.finish_session()` غير كافٍ للـHTTP contract.

الإصلاح النهائي يجب أن يكون في authoritative bridge/policy، مع الحفاظ على:

- retake attempt history.
- `official_for_reporting` selection.
- temporary skip neutrality.
- pre/post scoring semantics.

**هذه النقطة ما زالت غير مغلقة في لحظة كتابة V3.**

---

# 14. Retakes

يجب الحفاظ على:

- supervisor authorization قبل إعادة pre/post.
- سبب مكتوب.
- previous session history لا يحذف.
- assessment_attempt_no يزداد.
- supersedes_session_id محفوظ.
- محاولة واحدة official_for_reporting.

لا تجعل completed replay يخلق retake أو يغير official history.

---

# 15. Audio completion

- real `uploaded` audio = انتظار مراجعة.
- `rerecord_required` = الطالب يحتاج العودة للتسجيل.
- graded audio يدخل scoring حسب policy.
- temporary skip = neutral evidence، ليس wrong.
- آخر مراجعة صالحة قادرة على finalize pretest.

Regression الأساسي audio review completion يمر في آخر Backend run.

---

# 16. Selection cardinality

لا hardcode مثل `>=2`.

استعمل `required_selection_count` من DB/structured API.

- single 1.
- multi exact correct-count.
- ordered/build exact sequence length.

---

# 17. Success popup

لا تقرأ كلمات `أحسنت/رائع` من DOM لتحديد النجاح.

success event يأتي من state/phase حقيقي فقط.

---

# 18. Media/M08

M08 لا يغلق بهذه التعديلات.

لا تولد fake production assets للأصول غير المتاحة.

أي neutral gap يبقى explicit.

---

# 19. ملفات مهمة عند المقارنة مع الأصل

Backend/content/runtime:

- `services/api/seed_all.py`
- `services/api/db/sandbox_bootstrap.py`
- `services/api/content_runtime.py`
- `services/api/assessment.py`
- `services/api/assessment_view.py`
- `services/api/temporary_audio_skip.py`
- `services/api/assessment_retake.py`
- `services/api/learning_experience.py`
- Student Experience/content overlay seed files.

Frontend:

- `apps/web/src/app/student/session/[id]/page.tsx`
- `apps/web/src/app/student/session/[id]/session.module.css`
- `apps/web/src/app/student/activity/[id]/page.tsx`
- `apps/web/src/components/StudentExperienceEffects.tsx`
- assessment legacy polish/components يجب مقارنتها بعناية، ولا تفترض أنها كلها obsolete إلا بعد فحص الاستعمال.

Tests:

- pretest experience tests.
- learning renderer regression.
- DB-only runtime tests.
- full content integrity.
- selection contract.
- student content quality/question experience.
- auditory story replacement tests.
- assessment audio review completion.
- completed assessment reopen regression.
- Playwright vertical slice/question experience/media/accessibility.

---

# 20. Reference commits

المراجع الأساسية للحالة الحالية تشمل:

`44a7214...`
`2023e084...`
`d128e4fb...`
`d4919a7e...`
`4867f01e...`
`7462f9ba...`
`436380bc...`
`7e441b9f...`
`085c451...`
`9668d54...`
`40fc073...`
`52dfda34...`
`fcb30314...`
`a011e2df...`
`b72fd90a...`
`ff62e373...`
`edaff8e0...`
`8ed267de...`
`cf679d86...`

راجع `HIMMA_SANDBOX_EXECUTION_CHANGELOG_V3_2026-09-02_AR.md` لتفسير كل واحد ومشكلة CTA/finish بالتفصيل.

---

# 21. حالة Quality Gate الحالية

آخر run موثق قبل إضافة ملفات V3:

`33582241449`

على SHA:

`cf679d86dad9750945fc5e55f12d207fbf4f86e6`

النتائج:

- Frontend = SUCCESS.
- Backend = FAILURE.
- Backend tests = 194 passed / 2 failed.
- Integration = SKIPPED.

الفشلان:

- completed assessment reopen should replay stored result.
- completed assessment with missing stored result should return 409.

السبب الجذري: authoritative finish bridge shadowing كما في القسم 13.

**لا تعتبر V3 جاهزة للنقل التنفيذي حتى تصبح هذه البوابة خضراء ويعمل Integration/Playwright.**

---

# 22. Definition of Done قبل نقل الـSandbox إلى الأصل

يجب أن تتحقق كلها:

1. completed finish replay fixed في authoritative bridge.
2. Backend full tests PASS.
3. Frontend TS/ESLint/unit/build PASS.
4. Integration PASS.
5. Playwright vertical slice PASS.
6. question-experience PASS، ويثبت CTA label visible.
7. media-fidelity PASS ضمن الأصول المتاحة/الفجوات المعلنة.
8. accessibility integration PASS.
9. runtime counts 105/125/35/44/30/65/30 محفوظة.
10. no raw prompt leakage.
11. auditory replacement present، old path/direction absent.
12. POST-Q14 correct.
13. no new fake audio.
14. migration diff reviewed ضد `recovery/ui-media-admin-overhaul`.
15. لا تعديل للفروع الأساسية مباشرة، ولا Production Release بدون موافقة المستخدم.

---

# 23. ترتيب النقل المقترح

مرحلة A — Content/DB contract  
مرحلة B — Structured APIs  
مرحلة C — Student renderer/shared UI  
مرحلة D — Assessment completion/audio/retake bridge  
مرحلة E — Regression tests  
مرحلة F — Full Quality Gate + evidence  
مرحلة G — مراجعة المستخدم  
مرحلة H — merge/release فقط بعد الموافقة

لا تدمج كل شيء دفعة واحدة دون gates.

---

# 24. ما يجب حذفه/عدم نقله

- experimental DOM patches.
- obsolete enhancer layers.
- old path tracing.
- superseded reading-direction replacement.
- CSS selector الذي يخفي CTA span حسب last-child.
- duplicated stimulus/options composition.
- fake media fallbacks.
- generic hints التي تكشف الإجابة.
- auto memory timer hide.
- success inference from copy text.

---

# 25. المرجع التنفيذي

للتاريخ الكامل للمشاكل والمحاولات والحلول والـSHA:

`docs/handoff/HIMMA_SANDBOX_EXECUTION_CHANGELOG_V3_2026-09-02_AR.md`

وللقرارات السابقة المفيدة التي لا تتعارض مع V3 يمكن الرجوع لوثائق 2026-09-01 و2026-09-02 القديمة، لكن **V3 تنتصر عند التعارض**.

---

**نهاية Final State & Migration V3.**
