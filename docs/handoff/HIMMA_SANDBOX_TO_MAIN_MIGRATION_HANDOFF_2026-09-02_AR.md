# هِمّة — Handoff v2 لنقل الحالة النهائية من الـSandbox إلى المستودع الأصلي

**التاريخ:** 2026-09-02  
**المصدر التجريبي:** `7eaur/himma-deployment-sandbox` / `main`  
**المستودع الهدف لاحقًا:** `7eaur/himma-`  
**الفرع الرسمي المستهدف عند بدء النقل:** `recovery/ui-media-admin-overhaul`  
**حالة الوثيقة:** مرجع تنفيذ/تدقيق للنقل فقط، وليست إذن Merge أو Production Release.  
**هذه الوثيقة تحل محل** `HIMMA_SANDBOX_TO_MAIN_MIGRATION_HANDOFF_2026-09-01_AR.md` **في أي نقطة تعارض.**

---

## 1. قاعدة النقل التي لا يجوز كسرها

لا تعمل cherry-pick عشوائي لسلسلة تجارب الـSandbox. المطلوب هو مقارنة المستودع الأصلي بالحالة النهائية هنا ثم نقل **القرارات النهائية والملفات النهائية فقط**.

المعمارية المطلوبة بعد النقل:

`Import/Seed sources → PostgreSQL runtime snapshot → structured API → student renderer`

وليس:

`prompt_text → parse/regex/guess → UI`

`prompt_text` يمكن أن يبقى في قاعدة البيانات للتوافق والتاريخ، لكنه **ليس عقد عرض للطالب** ولا يُرسل إلى Student View API ولا يتم تفكيكه في React.

ملفات JSON/CSV/manifest تستخدم في **الاستيراد/seed فقط**؛ أثناء جلسة الطالب لا يفتح Runtime ملفات المحتوى من المستودع.

الوسائط نفسها (audio/image binaries) تبقى في Media/Object Storage، وقاعدة البيانات تخزن الـasset IDs والربط والدلالة.

---

## 2. ثوابت المشروع التي يجب الحفاظ عليها

- Runtime total = **125**.
- Base approved items = **105**.
- Reinforcement = **35**.
- Canonical skills = **44**.
- Pretest = **30**.
- Learning = **65** (30 Core + 35 Reinforcement).
- Posttest = **30**.
- لا تغيير في canonical IDs أو stable keys أو ترتيب الرحلة بسبب إصلاحات العرض.
- لا تغيير في R1: >=6 Core، mastery >=85، critical floor >=70، full critical coverage، لا blockers، ترقية مستوى واحد فقط، لا auto-demotion.
- L3 يحتاج full evidence قبل journey completion/posttest.
- Pre/Post محايدان ولا يعرضان correctness feedback أو hints تكشف الإجابة.
- M08 يبقى External-Gated إلى أن تصل الأصول الصوتية الحقيقية؛ ممنوع اختلاق ملفات صوتية.

---

## 3. مصدر المحتوى Runtime — DB Only

تم إصلاح السبب البنيوي الذي كان يؤدي إلى تكرار السؤال/الخيارات وظهور الإجابة داخل حاوية العرض.

### المطلوب نقله

- `services/api/seed_db_runtime_contract.py`
- `services/api/content_runtime.py`
- Student View contracts للـassessment والـlearning.
- اختبارات DB-only.

### القاعدة

بعد `seed_all` تكون بيانات العرض الأكاديمية داخل PostgreSQL، بما فيها:

- canonical id
- interaction type
- skill
- question text
- instruction text
- stimulus text
- encouragement
- hint
- options
- correct flags / ordering في طبقة التقييم
- required selection count
- asset IDs
- semantic text
- media gaps
- internal story metadata عند الحاجة

لا يوجد Runtime read لـ`catalog.json` أو `manifest.csv` لبناء ما يراه الطالب.

---

## 4. الاختبار القبلي

**Display version:** `HIMMA-PRETEST-2026-09-01`

يستخدم Student View structured contract، وليس `prompt_text`.

### PRE-Q03 حاسم

- السؤال: `انظر إلى الحرف، ثم اختر الشكل الآخر للحرف نفسه.`
- stimulus: `م` فقط.
- الخيارات منفصلة.
- ممنوع تكرار وصف المصدر أو الخيارات داخل stimulus.

### إنهاء القبلي بعد التسجيلات الصوتية — إصلاح مهم

المشكلة السابقة:

- الطالب يكمل 30/30.
- التسجيل الحقيقي يبقى `uploaded` بانتظار المراجعة.
- الجلسة تبقى `in_progress`.
- `/student/profile` يعرض `متابعة الاختبار` رغم عدم وجود سؤال ناقص.
- حتى بعد مراجعة آخر تسجيل لم تكن الجلسة تُغلق تلقائيًا، فلا يتحدث `current_level`.

السلوك النهائي المطلوب:

1. 30/30 + تسجيلات معلقة → حالة **بانتظار مراجعة التسجيلات** وليس Resume.
2. temporary audio skip يبقى neutral ولا يعلق الإغلاق.
3. آخر مراجعة صوتية صالحة → finalize assessment تلقائيًا.
4. يتم حفظ `session.assigned_level` و`student.current_level`.
5. الصفحة الرئيسية تنتقل لمسار التعلم بدل `متابعة الاختبار`.
6. إذا كان التسجيل يحتاج rerecord فعلًا، عندها فقط يعود الطالب للجلسة.
7. صفحة النتيجة الحقيقية تعرض النسبة + المستوى + CTA متناسق.

Regression المطلوب: سيناريو mix من real audio + temporary skip ثم مراجعة آخر تسجيل.

---

## 5. الاختبار البعدي

**Display version:** `HIMMA-POSTTEST-2026-09-01`

تم اكتشاف أن البعدي سابقًا كان يمتلك `posttest_experience` في DB لكن الواجهة تقرأ `pretest_experience` فقط ثم ترجع إلى raw `instruction_text/prompt_text`.

النهائي:

- القبلي والبعدي يمران عبر Student View structured API.
- لا fallback إلى `prompt_text` في واجهة الطالب.
- نفس لغة التصميم ونفس renderer contract.

### POST-Q14

الهدف النهائي:

`نَخْلَة`

والترتيب:

`ن → خ → ل → ة`

لا يرجع إلى `نَخْل`.

---

## 6. الأنشطة والتقوية

**Learning version:** `HIMMA-LEARNING-2026-09-01-R2`

### عقد الجولة

- round_number
- round_total
- skill
- encouragement
- hint
- question_text
- instruction_text
- stimulus_text
- interaction_type
- options
- required_selection_count
- assets
- media_gaps
- retry / attempts state

واجهة النشاط لا تحلل legacy prompt ولا تخمّن stimulus.

### Retry messaging

`retry ? hint : encouragement`

لا يظهر hint + encouragement معًا.

### التلميحات

تمت إضافة Quality Gate يمنع التلميح من طباعة خيار صحيح غير تافه مباشرة. تم إصلاح تلميحات L1 التي كانت تكشف أسماء الإجابات.

---

## 7. مشكلة تداخل stimulus والخيارات

مثال المشكلة القديمة:

`سُ؛ سَ/سِ/سُ`

أو صيغة حرف مع الخيارات داخل نفس النص الخام.

النهائي:

- stimulus يحتوي **العنصر المطلوب فقط** عندما يكون stimulus مطلوبًا.
- الخيارات تعرض في option controls فقط.
- لا `/` أو `الخيارات:` أو serialized option list داخل stimulus.

تم اختبار المستوى الأول خصوصًا:

- L1-CORE-01
- L1-CORE-03
- L1-CORE-06
- L1-CORE-07

ويجب الحفاظ على Regression العام لكل المحتوى.

---

## 8. عدد الاختيارات — Exact DB Cardinality

تم اكتشاف أن assessment/activity UI كانت تسمح بالإرسال عند `>= 2` في multi-select بغض النظر عن العدد الصحيح.

النهائي:

- الـBackend يحسب `required_selection_count` من DB.
- Single = 1.
- Multi = عدد correct options في DB.
- Sequence/Build = عدد عناصر الترتيب المطلوبة.
- UI لا يسمح بالنقص أو الزيادة.
- عند الوصول للحد لا يمكن إضافة خيار زائد.
- زر المتابعة لا يتفعل إلا عند العدد الصحيح.

هناك Gate يمر على **كل جولات التعلم** للتحقق من cardinality.

---

## 9. Popup «أحسنت» المتكرر

السبب القديم:

مكوّن عالمي كان يبحث في DOM عن كلمات مثل `أحسنت` و`رائع` ويعامل العبارة التشجيعية نفسها كحدث نجاح، لذلك ظهر Popup بشكل متكرر ومزعج.

النهائي:

- لا inference من نص الصفحة.
- العبارات التشجيعية النصية تبقى داخل النشاط.
- Popup/celebration العام مرتبط بحالة إنجاز فعلية مثل `data-phase="done"` فقط.
- الخطأ/retry لا يولد نافذة نجاح.

---

## 10. نشاط الذاكرة البصرية

النهائي:

1. الصور تبقى ظاهرة.
2. الطالب يركز.
3. لا اختفاء تلقائي بمؤقت.
4. الطالب يضغط `التالي`.
5. بعدها يدخل مرحلة الاسترجاع/الترتيب.

ممنوع إعادة النسخة التي تختفي فيها الصور فجأة.

---

## 11. استبدال نشاط المسار — القرار النهائي الأحدث

**هذا القسم يلغي قرار اتجاه القراءة الموجود في Handoff بتاريخ 2026-09-01.**

لا يعاد path/maze/tracing، ولا تعاد نسخة `من أين نبدأ القراءة؟ / يمين أم يسار؟`.

### L1-CORE-09 — استمع إلى القصة ثم أجب

interaction: `listen_choose_one`

skill: **الفهم السمعي المباشر**

**story_text_internal — لا يظهر للطالب:**

`ذهبت ليان مع أبيها إلى المزرعة في الصباح. رأت أرنبًا أبيض قرب الشجرة، فأعطته جزرة. ثم ساعدت أباها في سقي النباتات. وقبل أن تعود إلى البيت، قطفت زهرة صفراء لأمها.`

الجولات:

1. أين ذهبت ليان؟ → `إلى المزرعة` | `إلى المدرسة` | `إلى السوق`
2. مع من ذهبت ليان؟ → `مع أبيها` | `مع معلمتها` | `مع صديقتها`
3. ماذا رأت ليان قرب الشجرة؟ → `أرنبًا أبيض` | `قطة سوداء` | `عصفورًا صغيرًا`
4. ماذا أعطت ليان للأرنب؟ → `جزرة` | `تفاحة` | `قطعة خبز`
5. ماذا فعلت ليان قبل أن تعود إلى البيت؟ → `قطفت زهرة صفراء لأمها` | `لعبت بالكرة` | `ذهبت إلى المدرسة`

القصة لا توضع في `stimulus_text`.

الصوت حاليًا:

- `story_audio_asset_id = null`
- status = `pending_audio_asset`
- Media gap معلن.
- لا fake audio.

### L1-REIN-11 — استمع واختر الإجابة

interaction: `listen_choose_one`

**story_text_internal — لا يظهر للطالب:**

`ذهب نادر مع أخته إلى الشاطئ. بنيا قلعة من الرمل، ثم جمعا أصدافًا جميلة. وبعد اللعب جلسا تحت المظلة وشربا الماء، ثم عادا إلى البيت.`

الجولات:

1. أين ذهب نادر؟ → `إلى الشاطئ`
2. مع من ذهب نادر؟ → `مع أخته`
3. ماذا بنى نادر وأخته؟ → `قلعة من الرمل`
4. ماذا جمع نادر وأخته؟ → `أصدافًا`
5. ماذا شرب نادر وأخته؟ → `الماء`

لكل جولة 3 خيارات، correct واحد فقط، والتلميحات لا تكشف correct literal.

الصوت حاليًا Pending مثل النشاط الأساسي.

### الأصول الصوتية الخارجية الناقصة حاليًا

أصبح المطلوب تسليم **4 أصول صوتية**:

1. `موز`
2. `سَا`
3. قصة ليان — L1-CORE-09
4. قصة نادر — L1-REIN-11

لا يتم إغلاق M08 قبل وصول الأصول الصحيحة وربطها واختبارها.

---

## 12. القالب المرئي وتنظيف الطبقات

- الأنشطة تعيد استخدام `apps/web/src/app/student/session/[id]/session.module.css`.
- تم حذف/إزالة طبقات Learning DOM enhancer القديمة.
- لا MutationObserver لإصلاح المحتوى بعد الرندر.
- تم حذف طبقة `activity-polish.css` الميتة/القديمة حتى لا تتداخل مستقبلًا.
- top/global sound toggle أزيل من شاشات التعلم/الاختبار.
- **زر الاستماع الداخلي يبقى** للأسئلة التي تعتمد على الصوت.
- progress panel أكثر إحكامًا (~25% أقل ارتفاعًا من النسخة السابقة).
- typography مرنة باستخدام CSS fluid/clamp؛ لا تدّعِ وجود JS AutoFit كامل إلا إذا أضيف لاحقًا.

---

## 13. Media semantics

تم إصلاح semantic metadata للأصول عند DB snapshot، ومن أمثلة الحماية:

- PRE-Q24 / `STY-01` يحتفظ بـ`semantic_text = نص الاختبار القبلي`.
- حتى partial-development DB fallback يأخذ semantics من DB template metadata ولا يفتح repository files.

---

## 14. Quality Gates المضافة/المحدثة

يجب نقل الاختبارات التي تحمي التالي:

- 125 runtime items.
- 35 reinforcement.
- 44 skills.
- DB-only student runtime.
- no raw prompt/template_data in student payload.
- complete student content integrity.
- no serialized source fragments in student-visible copy.
- no empty choice tasks.
- no duplicate visible options.
- exactly one correct option in single-choice.
- required selection cardinality per learning round.
- no hint answer leakage.
- L1 stimulus never serializes options.
- PRE-Q03 contract.
- POST-Q14 نخلة contract.
- auditory story replacement for L1-CORE-09/L1-REIN-11.
- story text internal only.
- story audio pending as explicit gap, no fake asset.
- pretest audio-review auto-finalization and assigned level update.
- memory preview manual-next behavior.

---

## 15. ملفات/طبقات مهمة عند النقل

راجع الفرق النهائي حول هذه المناطق بدل cherry-pick الأعمى:

### Backend

- `services/api/assessment.py`
- `services/api/student.py` / profile/journey state حسب بنية الأصل
- `services/api/content_runtime.py`
- `services/api/learning_experience.py`
- `services/api/seed_all.py`
- `services/api/seed_db_runtime_contract.py`
- `services/api/seed_student_experience_v2.py`
- `services/api/seed_learning_posttest_projection_runtime.py`
- `services/api/seed_pretest_experience_2026_09_01.py`
- seed/correction modules التي تبني 125 item runtime

### Frontend

- `apps/web/src/app/student/session/[id]/page.tsx`
- `apps/web/src/app/student/session/[id]/session.module.css`
- `apps/web/src/app/student/activity/[id]/page.tsx`
- `apps/web/src/components/StudentExperienceEffects.tsx`
- صفحة الطالب الرئيسية/حالة الرحلة

### Tests

- DB-only runtime tests
- full content integrity
- student content quality
- learning selection contract
- assessment audio review completion
- student experience v2 / auditory story replacement
- E2E question/activity experience

---

## 16. ما لا يجب إعادته

- LearningExperienceEnhancer القديم.
- DOM MutationObserver لتعديل نص السؤال/stimulus/options.
- `learning-experience-polish.css` القديم.
- `activity-polish.css` القديم.
- parse/regex في React لـ`prompt_text`.
- fallback للبعدي إلى raw `prompt_text`.
- `>=2` كقاعدة عامة للـmulti-select.
- global popup يستنتج النجاح من كلمات `أحسنت/رائع`.
- path tracing القديم.
- reading-direction replacement الذي كان وسيطًا مؤقتًا قبل اعتماد القصة السمعية.
- fake audio للأصول الناقصة.

---

## 17. خطة النقل إلى المستودع الأصلي

### A — Compare

قارن `7eaur/himma-:recovery/ui-media-admin-overhaul` مع الحالة النهائية للـSandbox، ولا تغيّر الفرع الرسمي أثناء التحليل.

### B — Data contracts

انقل DB runtime snapshot + display contracts + Student View APIs أولًا.

### C — Content migrations

انقل Pretest/Learning/Posttest structured projections، ثم auditory story replacement، ثم media-gap state.

### D — Frontend

اربط القالب بالـstructured API فقط. لا parsing للـlegacy fields.

### E — Lifecycle

انقل إصلاح pretest waiting/review/finalize/level update وحالة dashboard.

### F — Tests

شغّل Catalog validation + seed idempotency + backend suite + frontend type/lint/unit/build + Playwright E2E.

### G — Review

راجع يدويًا على الأقل:

- PRE-Q03
- سؤال صوت + صورة
- read-aloud + pending review
- level result page
- L1-CORE-01/03/06/07
- memory preview
- L1-CORE-09 auditory story pending-audio state
- L1-REIN-11 auditory story pending-audio state
- multi-select exact cardinality
- POST-Q14
- mobile viewport

### H — No production merge without approval

بعد Green + evidence فقط يتم طلب موافقة المستخدم قبل أي merge/release.

---

## 18. Evidence من الـSandbox عند كتابة هذه الوثيقة

### Runtime functional SHA قبل توثيق v2

`ff62e373856661cd177f98b6d6b92fb5b847fd1e`

### GitHub Actions

Run: `33578211934`

عند بدء تحديث الوثيقة:

- Backend: **SUCCESS**
- Frontend: **SUCCESS**
- Integration / Playwright: كان **IN PROGRESS**؛ يجب تحديث الحكم النهائي بعد انتهائه، ولا يُقال Full Green قبل ذلك.

### Vercel

Deployment: `dpl_Gh5ZYeiugnHSrDJBXPQhDqUYWJzH`

- SHA: `ff62e373856661cd177f98b6d6b92fb5b847fd1e`
- state: **READY**
- target: production داخل مشروع الـSandbox فقط.

### Railway

Deployment: `36d4b947-4423-401d-be06-f0df259da73b`

- SHA: `ff62e373856661cd177f98b6d6b92fb5b847fd1e`
- state: **SUCCESS**

---

## 19. Definition of Done للنقل المستقبلي

لا تعتبر النقل للمستودع الأصلي مغلقًا إلا إذا:

- source-of-truth/runtime flow DB-driven.
- لا student UI يعتمد على raw prompt parsing.
- 125/35/44 invariants سليمة.
- Pre/Post structured and neutral.
- learning structured and retry-safe.
- no duplicated options/stimulus overlap.
- no answer-leaking hints.
- exact selection cardinality.
- pretest audio pending state لا يظهر Resume كاختبار ناقص.
- last audio review finalizes placement and updates level.
- auditory story content موجود في DB والstory text غير ظاهر للطالب.
- الأصوات الأربعة الحقيقية تربط عند وصولها أو تبقى gaps معلنة.
- POST-Q14 = نخلة.
- Frontend + Backend + Integration Green على SHA واحد.
- فحص يدوي responsive للمسار الحرج.
- لم يتم تغيير R1 أو scoring أو IDs بلا قرار مستقل.
- لم يتم Merge/Release قبل الموافقة الصريحة.

---

**الخلاصة:** المرجع النهائي للنقل هو الحالة الوظيفية المثبتة في الـSandbox بعد 2026-09-02، وليس تاريخ التجارب الوسيطة. أي اختلاف بين هذه الوثيقة ووثيقة 2026-09-01 يُحسم لصالح هذه الوثيقة.