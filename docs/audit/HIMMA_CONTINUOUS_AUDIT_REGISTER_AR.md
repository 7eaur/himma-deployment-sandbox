# هِمّة — سجل التدقيق المستمر والمشاكل

**الملف المرجعي الدائم للتدقيق:** `docs/audit/HIMMA_CONTINUOUS_AUDIT_REGISTER_AR.md`  
**المستودع:** `7eaur/himma-deployment-sandbox`  
**تاريخ إنشاء السجل:** 2026-09-01  
**مرجع HEAD عند إنشاء الإصدار الأول:** `7268692b6e85df90bb800129ff8f99727bb5c168`  
**الحالة:** ACTIVE — سجل حي يُحدَّث مع كل فحص جديد أو اكتشاف أو إصلاح أو إعادة تحقق.  

> هذا الملف هو المكان الرسمي الذي تُجمع فيه نتائج التدقيق الفني والوظيفي والأكاديمي والتشغيلي لمنصة هِمّة. لا تُحذف المشكلة من السجل بعد إصلاحها؛ تُغيّر حالتها ويُضاف دليل الإصلاح وإعادة التحقق حتى يبقى التاريخ محفوظًا.

---

# 1) الغرض من هذا السجل

هذا السجل لا يهدف إلى سرد ملاحظات عامة أو انطباعات تصميمية فقط. الهدف هو إنشاء **Issue & Audit Register** دائم للمشروع يجيب عن الأسئلة التالية لكل مشكلة:

- ما المشكلة بالضبط؟
- أين ظهرت؟
- هل هي مؤكدة أم ما زالت تحتاج تحققًا؟
- ما درجة خطورتها؟
- ما أثرها على الطالب أو المشرف أو البيانات أو النشر؟
- هل تمس المحتوى الأكاديمي أو منطق التكيّف؟
- ما السبب الجذري المتوقع أو المثبت؟
- ما الإصلاح الصحيح المقترح دون إعادة بناء المنصة بلا داعٍ؟
- هل أُصلحت؟
- هل أُعيد اختبارها بعد الإصلاح؟
- في أي commit/نسخة تم ذلك؟

هذا السجل مستقل عن ملفات التسليم والهجرة مثل:

`docs/handoff/HIMMA_SANDBOX_TO_MAIN_MIGRATION_HANDOFF_2026-09-01_AR.md`

ملف الـHandoff يشرح **ما يجب نقله وكيف**، بينما هذا الملف يحفظ **ما اكتشف أثناء التدقيق وما حالته**.

---

# 2) قواعد تحديث السجل

من الآن فصاعدًا، عند اكتشاف مشكلة أو خطر أو فجوة تحقق:

1. تُضاف المشكلة إلى هذا الملف برقم ثابت `HIMMA-AUD-XXX`.
2. لا يُعاد استخدام الرقم لمشكلة أخرى.
3. تُسجل الحالة الحالية بوضوح.
4. إذا أُصلحت المشكلة، لا تُحذف؛ تتحول إلى `RESOLVED` ثم `VERIFIED` بعد اختبار فعلي.
5. أي مشكلة تغيرت بسبب تعديل حديث ولكن لم تُختبر من جديد تصبح `NEEDS-REVALIDATION`.
6. أي استنتاج لم يثبت بعد لا يُكتب كمشكلة مؤكدة، بل `INVESTIGATING`.
7. لا يُغيّر المحتوى الأكاديمي أو scoring أو adaptive logic فقط لإغلاق Issue تقني إلا بمبرر واعتماد واضح.
8. كل نتيجة مرتبطة بالنشر يجب أن تميز بين GitHub HEAD وبين النسخة المنشورة فعليًا على Vercel/Railway.
9. لا يُعلن المشروع جاهزًا للإطلاق بسبب `/health=200` أو Build أخضر وحدهما.
10. أي إصلاح جديد يجب أن يضيف Regression Test عندما يكون ذلك ممكنًا.

---

# 3) حالات المشاكل

| الحالة | المعنى |
|---|---|
| `CONFIRMED-OPEN` | مشكلة مثبتة وما زالت مفتوحة في النسخة التي تم التحقق منها. |
| `RESOLVED-UNVERIFIED` | تم تطبيق إصلاح لكن لم يكتمل اختبار ما بعد الإصلاح. |
| `VERIFIED-RESOLVED` | أُصلحت وأعيد اختبارها فعليًا. |
| `NEEDS-REVALIDATION` | كانت مشكلة مؤكدة لكن حدثت تعديلات لاحقة قد تكون أصلحتها؛ يجب إعادة التحقق على HEAD الحالي. |
| `INVESTIGATING` | يوجد دليل أو خطر معتبر لكن لم يثبت السبب/الأثر النهائي بعد. |
| `ACCEPTED-RISK` | خطر معروف تم قبوله صراحة لبيئة معينة مثل Sandbox. |
| `NOT-APPLICABLE` | لم يعد ينطبق بسبب قرار منتج/محتوى معتمد غيّر المسار. |

---

# 4) درجات الأولوية

| الأولوية | التعريف |
|---|---|
| `P0` | يمنع المسار الأساسي أو يهدد صحة البيانات/الأمان بشكل حرج أو يجعل الإطلاق غير مقبول. |
| `P1` | خلل وظيفي كبير أو خطر إطلاق مرتفع يحتاج إصلاحًا قبل اعتبار المنصة جاهزة. |
| `P2` | مشكلة مهمة في الاعتمادية/الأمان/UX/الأداء، لكنها لا توقف المسار بالكامل في كل الحالات. |
| `P3` | تحسين أو Hardening أو جودة طويلة المدى. |

---

# 5) ملخص تنفيذي للحالة الحالية

الحكم الحالي من التدقيق هو أن المشروع **ليس بحاجة إلى إعادة كتابة من الصفر**. توجد بنية جيدة وأجزاء صحيحة يجب الحفاظ عليها، لكن لا يجوز اعتبار المنصة جاهزة للإطلاق النهائي قبل إغلاق أو إعادة التحقق من نقاط المسار التعليمي والصوت والجاهزية التشغيلية والأمان.

أهم المحاور التي ظهرت أثناء التدقيق:

- تعارضات سابقة/محتملة بين أنواع المحتوى التعليمي وبين Renderer/Submit contract.
- فجوة بين Infrastructure Readiness وبين Product Readiness.
- مشاكل Seed/Bootstrap ظهرت فعليًا أثناء نشر قاعدة Sandbox فارغة.
- اعتماد بعض التصحيح/التفسير على ترتيب البيانات أو نصوص غير منظمة.
- Hardening أمني مطلوب للمصادقة وCookies.
- فجوات Responsive/Performance تحتاج تحققًا بصريًا وحيويًا.
- دورة التحليل الصوتي تحتاج إغلاق تحقق End-to-End.
- حوكمة النشر من `main` تحتاج تشديدًا قبل Production فعلي.

---

# 6) سجل المشاكل التفصيلي

## HIMMA-AUD-001 — تعارض `path_sequence` مع Renderer الأنشطة

**الأولوية:** P1  
**الحالة الحالية:** `NEEDS-REVALIDATION`  
**المجال:** Student Learning / Frontend / Content Contract  

### ما تم اكتشافه

أثناء التدقيق على نسخة سابقة من الـSandbox، وُجد أن المحتوى يحتوي نشاطًا من النوع:

`path_sequence`

بينما Renderer الأنشطة كان يتعامل كأنواع ترتيب مع أنواع مثل:

`sequence`
`memory_sequence`

دون إدخال `path_sequence` في نفس مسار التفاعل، ما يعني أن الطالب يستطيع الوصول إلى النشاط ورؤية العناصر لكن لا يستطيع تكوين إجابة صالحة بالطريقة المطلوبة، وقد يبقى زر الإرسال غير قابل للاستخدام.

### الأثر

- إمكانية توقف رحلة الطالب في نشاط أساسي.
- عدم تطابق بين Content Contract والواجهة.
- المسار قد يبدو سليمًا في الاختبارات العامة لأن المشكلة مرتبطة بنوع Interaction محدد.

### التغير اللاحق المهم

ملف التسليم الحالي يوثق قرارًا أحدث بإلغاء صيغة path/maze/tracing القديمة واستبدالها وظيفيًا بـ:

- `L1-CORE-09` — `من أين نبدأ القراءة؟`
- `L1-REIN-11` — `يمين أم يسار؟`

لذلك لا ينبغي اعتبار المشكلة مفتوحة تلقائيًا على HEAD الحالي. يجب إعادة فحص Runtime catalog الفعلي للتأكد من عدم بقاء أي `path_sequence` قابل للوصول.

### معيار الإغلاق

- لا يوجد `path_sequence` نشط غير مدعوم في Runtime، **أو** Renderer يدعمه بعقد كامل.
- E2E يصل إلى النشاط المعني ويكمله فعلًا.
- لا يوجد مسار يجعل CTA عالقًا بسبب Interaction Type غير مدعوم.

---

## HIMMA-AUD-002 — تعارض أنشطة `read_aloud / timed_read_aloud` بين التسجيل وSubmit

**الأولوية:** P0/P1  
**الحالة الحالية:** `NEEDS-REVALIDATION`  
**المجال:** Student Learning / Audio / Frontend-Backend Contract  

### ما تم اكتشافه

في جولة تدقيق سابقة، ثبت أن Runtime يحتوي أنشطة قراءة جهرية/موقوتة، وأن واجهة النشاط تسجل وترفع الصوت، لكنها بعد ذلك كانت تمرر نتيجة إلى مسار Submit العادي للأنشطة بينما Backend يرفض أنواع:

`read_aloud`
`timed_read_aloud`

على ذلك المسار ويطلب استخدام مسار التسجيل الصوتي المخصص.

### الأثر

- الطالب قد يسجل صوته بنجاح ثم يفشل حفظ/تقييم النشاط.
- احتمالية بقاء النشاط دون تقدم رغم نجاح التسجيل.
- انفصال بين Upload lifecycle وLearning activity lifecycle.

### ملاحظة على النسخة الحالية

الـHandoff الأحدث ينص على أن التسجيل/الميكروفون **يبقى** في أنشطة القراءة التي تتطلب تسجيلًا، لكن هذا وحده لا يثبت أن عقد Submit الحالي أصبح صحيحًا End-to-End.

### المطلوب للتحقق

فحص مباشر للنسخة الحالية من:

- واجهة Activity Renderer.
- Recording upload endpoint.
- Activity submit endpoint.
- Speech job creation.
- حالة التسجيل بعد الرفع.
- انتقال الطالب بعد اكتمال النتيجة.

### معيار الإغلاق

اختبار E2E حقيقي:

`فتح نشاط قراءة → إذن ميكروفون → تسجيل → رفع → إنشاء job/analysis → حفظ attempt → تحديث progress → ظهور النتيجة/الانتقال الصحيح`

دون أي bypass أو نتيجة مصطنعة.

---

## HIMMA-AUD-003 — `/ready` يثبت البنية التحتية لكنه لا يثبت جاهزية المنتج

**الأولوية:** P1  
**الحالة الحالية:** `CONFIRMED-OPEN`  
**المجال:** Backend / Deployment / Operational Readiness  

### الدليل الذي ظهر فعليًا أثناء النشر

كانت خدمات البنية التحتية تعيد نجاحًا:

- PostgreSQL: OK
- Storage: OK
- Redis: OK
- `/ready`: 200

وفي نفس الوقت ظهرت قاعدة تشغيل فارغة فعليًا تقريبًا من بيانات المنتج، بما فيها counters مثل:

- users = 0
- skills = 0
- content items = 0
- students = 0

### المشكلة

الـReadiness الحالي يجيب عن سؤال:

> هل يستطيع API الوصول إلى dependencies؟

لكنه لا يجيب بشكل كافٍ عن:

> هل منصة هِمّة نفسها جاهزة لاستقبال طالب ومشرف وتشغيل المسار الأكاديمي؟

### المخاطر

- منصة تبدو خضراء للمراقبة لكنها غير قابلة للاستخدام.
- CI/CD أو مزود النشر يعتبر rollout ناجحًا قبل اكتمال bootstrap.
- صعوبة اكتشاف seed failure بسرعة.

### الإصلاح المقترح

إضافة Product Readiness/Startup validation منفصل أو توسيع readiness بعناية ليتحقق من أمور مثل:

- schema/migration head.
- catalog version المتوقع.
- count/signature للمحتوى المعتمد.
- وجود skill catalog.
- وجود admin bootstrap المطلوب للبيئة.
- عدم وجود bootstrap/seed failure marker.

### معيار الإغلاق

لا يمكن للبيئة أن تعلن Product Ready إذا كانت قاعدة البيانات infrastructure-connected ولكن Runtime catalog غير جاهز.

---

## HIMMA-AUD-004 — سباق Seed/Bootstrap وظهور `duplicate stable_key`

**الأولوية:** P1  
**الحالة الحالية:** `RESOLVED-UNVERIFIED`  
**المجال:** Backend / Database / Deployment  

### ما حدث فعليًا

أثناء rollout/تهيئة قاعدة Sandbox، ظهر فشل يتضمن duplicate key على `stable_key` عندما تداخل تشغيل bootstrap/seed مع أكثر من instance/process.

### السبب المعماري

وجود مسؤولية Seed/Bootstrap داخل startup path لخدمة يمكن أن تتوسع أفقيًا يخلق احتمال سباق إذا لم توجد آلية قفل/Idempotency قوية.

### الإصلاحات التي ظهرت لاحقًا

النسخة الأحدث تضمنت guards/advisory locking وفحوصًا أكثر صرامة للكتالوج.

### لماذا الحالة ليست VERIFIED بعد

يجب اختبار السيناريو المتزامن بعد التعديلات الجديدة، وليس الاكتفاء بقراءة الكود.

### التصميم الأفضل على المدى الطويل

`Deploy → migrations → deterministic bootstrap/seed job → validation → API rollout`

مع إبقاء الـAPI غير مسؤول عن إصلاح قاعدة البيانات بنفسه في كل Startup قدر الإمكان.

### معيار الإغلاق

- تشغيل bootstrap متزامن أكثر من مرة لا يخلق duplicate records.
- إعادة التشغيل لا تغير IDs/stable keys بلا داعٍ.
- failure يوقف الجاهزية بوضوح.

---

## HIMMA-AUD-005 — تصحيح `choose_many` يعتمد على أول خيارين في بعض مسارات الأنشطة

**الأولوية:** P1/P2  
**الحالة الحالية:** `NEEDS-REVALIDATION`  
**المجال:** Academic Scoring / Backend  

### ما تم اكتشافه

في أحد مسارات تقييم الأنشطة، ظهر منطق يعتمد على بناء الإجابة المتوقعة من ترتيب الخيارات، مثل أخذ أول خيارين، بدل جعل الحقيقة الأكاديمية تأتي حصريًا من حقل واضح مثل:

`is_correct`

### الخطر

ترتيب الصفوف/الخيارات يصبح جزءًا ضمنيًا من scoring.

إعادة ترتيب الخيارات لأسباب UI أو Seed أو Authoring قد تغير الإجابة الصحيحة دون تعديل صريح للمعيار الأكاديمي.

### المطلوب

توحيد مصدر الحقيقة للتصحيح على metadata أكاديمية صريحة وعدم استنتاج الإجابة من order إلا عندما تكون المهمة نفسها مهمة ترتيب.

### معيار الإغلاق

اختبار يغيّر ترتيب Options مع بقاء `is_correct` كما هو ويثبت أن النتيجة لا تتغير.

---

## HIMMA-AUD-006 — اعتماد بعض منطق التقييم/الترتيب على Parsing نص عربي غير منظم

**الأولوية:** P2  
**الحالة الحالية:** `NEEDS-REVALIDATION`  
**المجال:** Content Contract / Scoring / Maintainability  

### ما تم اكتشافه

ظهرت أجزاء تستنتج عددًا أو ترتيبًا أو معيارًا من نص criteria/prompt عربي بدل الاعتماد على حقول بنيوية صريحة.

### المشكلة

النص التحريري ليس API Contract ثابتًا.

أي تعديل لغوي بسيط يمكن أن يكسر parsing دون أن يكون التغيير مقصودًا وظيفيًا.

### الاتجاه الصحيح

النسخة الأحدث بدأت بالفعل بفصل:

- `question_text`
- `instruction_text`
- `stimulus_text`
- `interaction_type`
- `options`
- `assets`
- metadata التقييم

ويجب استكمال نفس المبدأ في كل ما يؤثر على scoring/runtime behavior.

---

## HIMMA-AUD-007 — عدم وجود Rate Limiting واضح على تسجيل الدخول

**الأولوية:** P1  
**الحالة الحالية:** `CONFIRMED-OPEN`  
**المجال:** Security / Authentication  

### الخطر

دخول الطالب يعتمد على رمز قصير نسبيًا، وتسجيل الدخول الإداري endpoint حساس. بدون rate limiting/lockout مناسب يمكن تنفيذ محاولات متكررة بسرعة.

### الملاحظة

Redis موجود بالفعل في البنية، لذلك يمكن استخدامه لتنفيذ throttling دون إدخال dependency جديدة كبيرة.

### الإصلاح المقترح

سياسة مجمعة تعتمد على:

- IP.
- معرف/كود الدخول بعد hashing عند الحاجة.
- نافذة زمنية.
- progressive delay أو temporary lock.
- logging دون تسجيل credentials الحساسة.

### معيار الإغلاق

اختبارات أمنية تثبت أن المحاولات الكثيفة تُبطأ/تُرفض دون التأثير المفرط على الطالب الشرعي.

---

## HIMMA-AUD-008 — Cookie `Secure` مرتبطة باسم البيئة بدل حقيقة HTTPS

**الأولوية:** P2  
**الحالة الحالية:** `CONFIRMED-OPEN`  
**المجال:** Security / Session Management  

### ما تم اكتشافه

المنطق يجعل `Secure` مرتبطة تقريبًا بكون `ENV=production`.

لكن Sandbox نفسها منشورة على HTTPS للعامة بينما `ENV=sandbox`، ما قد يترك Cookie دون `Secure` رغم أن الوصول الخارجي HTTPS.

### الإصلاح المقترح

استخدام إعداد صريح مثل:

`COOKIE_SECURE=true`

أو اشتقاقه من سياسة البيئة/HTTPS المعتمدة، لا من اسم environment فقط.

### معيار الإغلاق

كل بيئة HTTPS عامة تستخدم Cookie بـ`HttpOnly` و`Secure` و`SameSite` المناسبين.

---

## HIMMA-AUD-009 — إبطال الجلسات بعد تغيير بيانات الاعتماد يحتاج Hardening

**الأولوية:** P3  
**الحالة الحالية:** `INVESTIGATING`  
**المجال:** Security / Authentication  

### الملاحظة

تعطيل المستخدم يعمل بصورة جيدة لأن الطلبات المحمية تعيد التحقق من حالة المستخدم في قاعدة البيانات، لكن يجب التأكد من سياسة إبطال جميع JWTs القديمة عند تغيير كلمة مرور المشرف أو إجراء أمني مماثل.

### الاتجاه المقترح

`session_version` أو `token_version` أو revocation timestamp عند الحاجة.

---

## HIMMA-AUD-010 — الصور الموقعة/البعيدة تستخدم `unoptimized`

**الأولوية:** P2  
**الحالة الحالية:** `CONFIRMED-OPEN`  
**المجال:** Frontend / Performance / Mobile  

### المشكلة

استخدام `unoptimized` للصور البعيدة/Signed URLs يتجاوز جزءًا من Next Image Optimization.

### الأثر المحتمل

- LCP أعلى.
- استهلاك بيانات جوال أكبر.
- بطء التنقل في الأنشطة التي تحتوي صورًا.

### الإصلاح لا يعني إزالة Signed URLs

يمكن الاحتفاظ بنموذج التخزين الحالي مع:

- تجهيز أحجام/variants مناسبة.
- WebP/AVIF حيث ينطبق.
- Cache headers.
- عدم تحميل وسائط الجولة القادمة بلا حاجة.
- thumbnail policy.

### معيار الإغلاق

قياس فعلي على شبكة جوال/محاكاة slow 4G مع صور المحتوى الحقيقي.

---

## HIMMA-AUD-011 — Safe Area في شريط الإجراءات السفلي على iPhone تحتاج دعمًا صريحًا

**الأولوية:** P2  
**الحالة الحالية:** `INVESTIGATING`  
**المجال:** Responsive UX / Mobile  

### الملاحظة

ظهر شريط/منطقة إجراء سفلية مثبتة على الجوال دون دليل كافٍ على إضافة:

`env(safe-area-inset-bottom)`

### الخطر

CTA قد يقترب أكثر من اللازم من Home Indicator على بعض أجهزة iPhone.

### معيار الإغلاق

Visual/E2E على viewport مناسب مع safe-area simulation أو جهاز فعلي.

---

## HIMMA-AUD-012 — كثافة عمودين على الشاشات الصغيرة جدًا تحتاج تحققًا

**الأولوية:** P2/P3  
**الحالة الحالية:** `INVESTIGATING`  
**المجال:** Responsive UX / Arabic RTL  

### الملاحظة

بعض أنماط الاختيارات تبقى بعمودين قرب عرض 320–430px. قد تعمل مع كلمات قصيرة لكنها قد تصبح مزدحمة مع محتوى عربي أطول وصور.

### المطلوب

فحص بصري بالمحتوى الحقيقي على الأقل عند:

- 320
- 360
- 375
- 390
- 430
- 768

ولا يكفي Demo content القصير.

---

## HIMMA-AUD-013 — Production deployment من `main` دون حماية Branch كافية

**الأولوية:** P1  
**الحالة الحالية:** `CONFIRMED-OPEN`  
**المجال:** GitHub / CI-CD / Release Governance  

### ما تم اكتشافه

المستودع التجريبي يستخدم `main`، وVercel مرتبط بالنشر منها، بينما حماية الفرع/مراجعة التغييرات ليست بالمستوى الذي يجب الاعتماد عليه لاحقًا لإنتاج حقيقي.

### الخطر

أي Push مباشر قد يتحول إلى Production deployment قبل اكتمال Quality Gate أو المراجعة.

### ملاحظة

هذا مقبول جزئيًا كـSandbox سريع، لكنه **غير مقبول كحوكمة Production النهائية**.

### المطلوب قبل Production

- required checks.
- branch protection/ruleset.
- منع force push.
- review gate عند الحاجة.
- فصل Sandbox/Preview عن Production deployment policy.

---

## HIMMA-AUD-014 — اختلاف GitHub HEAD عن آخر Backend منشور بسبب Watch Patterns

**الأولوية:** P2  
**الحالة الحالية:** `ACCEPTED-RISK` للـSandbox مع ضرورة التوثيق  
**المجال:** Deployment Observability  

### ما ظهر أثناء التدقيق

في إحدى لحظات الفحص كان GitHub HEAD/Vercel أحدث من Railway backend لأن آخر commits لم تمس الملفات المشمولة في Railway watch patterns.

### لماذا هذا ليس Bug تلقائيًا

إذا كان التغيير Frontend/Docs فقط، عدم إعادة نشر Backend سلوك مطلوب.

### الخطر الحقيقي

أن يقال "اختبرنا HEAD الحالي" بينما Backend الحي فعليًا على commit أقدم.

### قاعدة التدقيق

كل تقرير تشغيل حي يجب أن يسجل:

- GitHub HEAD SHA.
- Vercel deployment SHA.
- Railway API deployment SHA.
- schema/catalog version عند الحاجة.

---

## HIMMA-AUD-015 — Vercel Root Directory كانت خاطئة وأنتجت Build فارغًا و404

**الأولوية التاريخية:** P1  
**الحالة الحالية:** `VERIFIED-RESOLVED` بالنسبة لمشكلة Root Build  
**المجال:** Deployment / Vercel  

### ما حدث

المشروع كان يبني من root المستودع بدل:

`apps/web`

فكانت Logs تنتهي في نحو ثانية دون Next.js build حقيقي ثم يظهر 404.

### الإصلاح

تم ضبط Root Directory ليكون:

`apps/web`

وبعدها ظهرت Logs فعلية لـNext.js تشمل install/build/typecheck/static pages.

### قاعدة منع التكرار

أي مشروع Vercel جديد لهذا المستودع يجب أن يُثبت Root Directory قبل أول حكم على صحة التطبيق.

---

## HIMMA-AUD-016 — Deployment Protection/SSO أعاقت التحقق الخارجي المباشر من Vercel

**الأولوية:** P2  
**الحالة الحالية:** `NEEDS-REVALIDATION`  
**المجال:** Vercel / QA Accessibility  

### ما ظهر

Deployment-specific/branch URLs كانت تعيد توجيهًا إلى Vercel SSO/Deployment Protection، ما منع smoke testing عادي بدون access/share mechanism.

### الأثر

ليست مشكلة تطبيق بحد ذاتها، لكنها تجعل التحقق الخارجي وأدوات E2E أصعب وقد تسبب التباسًا بين "App 404" و"Deployment protected".

### المطلوب

تحديد سياسة واضحة:

- Preview protected.
- Sandbox QA URL قابل للاختبار للجهات المخولة.
- Production policy مستقلة.

---

## HIMMA-AUD-017 — Redis Sandbox بدون Persistence ليس تصميم Production نهائيًا

**الأولوية:** P3 للـSandbox / P1 إذا نُقل كما هو للإنتاج  
**الحالة الحالية:** `ACCEPTED-RISK` في Sandbox  
**المجال:** Infrastructure / Redis  

### الملاحظة

خدمة Redis الحالية في Sandbox مبنية كخدمة `redis:7-alpine` بسيطة دون اعتبارها مخزنًا دائمًا.

### الحكم

هذا مقبول إذا كان Redis يستخدم cache/ephemeral coordination فقط في Sandbox، لكنه يحتاج مراجعة قبل Production إذا احتوى بيانات queues/rate-limit/session state يتسبب فقدانها في أثر وظيفي غير مقبول.

---

## HIMMA-AUD-018 — دورة Speech Worker لم تُغلق End-to-End بعد

**الأولوية:** P1  
**الحالة الحالية:** `INVESTIGATING`  
**المجال:** Audio Analysis / Worker / Queue / Student Flow  

### سبب فتح المشكلة

المشروع يحتوي مفاهيم Recording/SpeechAnalysisJob، لكن أثناء التدقيق لم يُحسم بعد بصورة تشغيلية أن كل تسجيل يحتاج تحليلًا يتم التقاطه فعليًا بواسطة Worker منشور ثم ينتهي إلى حالة نهائية تؤثر على attempt/progress بصورة صحيحة.

### لا يجوز الخلط

وجود خدمة باسم verification أو وجود Job model لا يثبت وحده وجود Speech Worker عامل.

### المطلوب للتحقق

- من ينشئ SpeechAnalysisJob؟
- ما حالة البداية؟
- من يستهلكه؟
- كيف يتعامل مع retry/failure/dead jobs؟
- هل توجد idempotency؟
- ماذا يرى الطالب أثناء pending؟
- هل يوجد timeout/fallback؟
- هل النتيجة تُربط بالنص المرجعي الصحيح؟
- هل C/D/I/S + phoneme data تدخل بالطريقة المقصودة فقط؟

### معيار الإغلاق

تشغيل تسجيل فعلي في Sandbox وتتبع السجل من upload إلى final analysis/result/progress.

---

## HIMMA-AUD-019 — CI يحتاج Regression coverage صريح للمشاكل التي ظهرت

**الأولوية:** P1/P2  
**الحالة الحالية:** `CONFIRMED-OPEN`  
**المجال:** Testing / CI  

### الاختبارات التي يجب أن تكون موجودة أو مثبتة كجزء من Quality Gate

- كل `interaction_type` موجود في Runtime له Renderer قابل للتفاعل.
- read-aloud activity contract.
- concurrent bootstrap/seed.
- empty DB لا تعلن Product Ready.
- choose_many لا يعتمد على option order.
- 320px mobile critical flow.
- safe-area behavior.
- RTL Arabic overflow.
- media missing/skip لا يعطي mastery.
- audio worker success/failure/retry.
- admin login + student creation + student code login.
- pretest → placement → learning → remediation → verification → progression → posttest.

### نقطة جيدة مثبتة

هناك Regression tests أضيفت بالفعل لبعض مشاكل عرض المحتوى المهيكل ومنع تكرار options/raw prompt، ويجب الحفاظ عليها.

---

## HIMMA-AUD-020 — Demo seed سابقًا ملأ حد الطلاب وأفشل Integration CI

**الأولوية التاريخية:** P1  
**الحالة الحالية:** `VERIFIED-RESOLVED` في إعداد Sandbox CI الذي تم تعديله  
**المجال:** CI / Seed Configuration  

### ما حدث

تشغيل demo student seed ملأ حد الطلاب المسموح وهو 15، ثم فشل Integration test عند محاولة إنشاء طالب جديد.

### الإصلاح الصحيح الذي اتُّخذ

تعطيل demo students في Integration environment بدل رفع الحد أو تغيير منطق المنتج.

### قاعدة منع التكرار

لا يتم تغيير `MAX_STUDENTS=15` لإرضاء اختبار CI. الاختبارات يجب أن تستخدم بيئة/seed مناسبين.

---

## HIMMA-AUD-021 — الاعتماد على Startup Seed يجعل فشل البيانات أقل وضوحًا من Job مستقل

**الأولوية:** P2  
**الحالة الحالية:** `CONFIRMED-OPEN` كقرار معماري يحتاج تحسينًا لاحقًا  
**المجال:** Deployment Architecture  

### الملاحظة

حتى بعد إضافة locking/guards، ربط bootstrap الأساسي بحياة API يزيد الاقتران بين Runtime startup وبين data lifecycle.

### التوصية

قبل Production النهائي، اجعل data initialization خطوة deployment واضحة وقابلة للتكرار/المراقبة، مع validation قبل فتح traffic.

---

## HIMMA-AUD-022 — يلزم توحيد تعريف "جاهز" بين CI وVercel وRailway والاختبار الوظيفي

**الأولوية:** P2  
**الحالة الحالية:** `CONFIRMED-OPEN`  
**المجال:** Release Governance / QA  

### المشكلة

كل طبقة قد تعتبر النجاح شيئًا مختلفًا:

- Vercel: Build/Deployment READY.
- Railway: container + healthcheck.
- GitHub: workflow green.
- المنتج: رحلة الطالب والمشرف تعمل.

### المطلوب

تعريف Release Gate واحد يربط:

`Build Green + Migrations + Catalog + Dependencies + Smoke + Critical E2E + No P0/P1 release blockers`

---

# 7) نقاط صحيحة يجب الحفاظ عليها

هذه ليست مشاكل، بل ضوابط جيدة ظهرت أثناء التدقيق ويجب عدم كسرها أثناء الإصلاح:

1. الـBackend هو صاحب القرار في أجزاء مهمة من scoring/progression، وليس الواجهة فقط.
2. Ownership checks موجودة في المسارات الحساسة التي تمت مراجعتها.
3. Idempotency موجودة في عدة عمليات مهمة.
4. Posttest مرتبط بقيود Backend وليس مجرد إظهار زر في الواجهة.
5. skips بسبب media gap/temporary audio لا تتحول تلقائيًا إلى mastery evidence.
6. `/ready` يفحص PostgreSQL وStorage وRedis فعليًا؛ المشكلة أنه لا يكفي وحده لProduct Readiness.
7. RTL أساسي في الواجهة وليس patch ثانويًا.
8. `prefers-reduced-motion` موجود في التصميم.
9. الواجهة تستخدم logical properties في أجزاء مهمة.
10. Content architecture الأحدث تتجه إلى payload منظم بدل parsing النص الخام.
11. الاختبار القبلي والبعدي يجب أن يبقيا محايدين دون feedback يكشف صحة الإجابة أثناء القياس.
12. حد الطلاب 15 قرار معتمد ولا يُعدّل بسبب deployment/test convenience.
13. Runtime المعتمد الحالي يجب أن يحافظ على 125 عنصرًا و35 تقوية و44 مهارة بحسب مرجع التسليم الحالي.

---

# 8) محاور التدقيق التي ما زالت مفتوحة

## 8.1 الصوت End-to-End

يجب إغلاق دورة:

`record → upload → job → worker → analysis → retry/failure → result → attempt → adaptive signal/progress`

## 8.2 لوحة المشرف

يجب فحص:

- Login.
- Dashboard.
- Student creation.
- 15-student cap.
- Reports.
- Recording review إن وجدت.
- Empty/Error/Loading states.
- Mobile navigation.
- table overflow.
- permissions.

## 8.3 قاعدة البيانات

يجب تدقيق:

- Unique constraints.
- Foreign keys.
- cascades.
- indexes.
- stable keys.
- attempt uniqueness/idempotency.
- speech jobs.
- access codes.
- audit logs.
- migration reversibility/consistency.

## 8.4 المحتوى الكامل

يجب تنفيذ فحص آلي على جميع عناصر Runtime للتحقق من:

- interaction types المستخدمة فعليًا.
- كل نوع له Renderer/validator.
- options correctness metadata.
- missing assets.
- audio requirements.
- image requirements.
- duplicate stable keys.
- orphan skills.
- pre/post neutrality.
- remediation mapping.

## 8.5 الجوال وAccessibility

- 320/360/375/390/430/768.
- landscape cases عند الحاجة.
- Arabic overflow.
- keyboard focus.
- contrast.
- screen reader labels.
- touch targets.
- safe areas.
- reduced motion.

## 8.6 الأداء

- LCP.
- INP.
- CLS.
- image payload.
- audio payload.
- route transitions.
- caching.
- signed asset URL behavior.

## 8.7 CI/CD

- latest main workflows.
- required checks.
- deployment SHA parity.
- branch protection.
- rollback behavior.
- migration failure behavior.

---

# 9) Release Blockers الحالية

لا يُعتمد الإطلاق النهائي حتى يتم على الأقل:

1. إغلاق/إعادة تحقق HIMMA-AUD-002 الخاصة بأنشطة القراءة الصوتية.
2. إغلاق HIMMA-AUD-018 وإثبات Speech Worker flow فعليًا.
3. ضمان عدم وجود Interaction Type مستخدم في Runtime دون Renderer/validator، بما يشمل إعادة تحقق HIMMA-AUD-001.
4. معالجة Product Readiness أو إنشاء Gate يمنع قاعدة فارغة من الظهور كمنصة جاهزة.
5. حسم أي scoring path يعتمد على ترتيب options أو parsing نص غير منظم.
6. إغلاق Rate Limiting المطلوب قبل Production العام.
7. تشغيل Critical E2E على المسار الكامل للطالب والمشرف.
8. عدم وجود P0 مفتوح أو P1 يوقف المسار الأساسي.

---

# 10) بروتوكول التحقق من كل إصلاح

لا يكفي تغيير الكود. لكل Issue يتم إغلاقها يجب تسجيل:

- Commit SHA.
- الملفات المتغيرة.
- نوع الاختبار.
- نتيجة Unit/Integration/E2E.
- نتيجة CI.
- نتيجة البيئة المنشورة إذا كانت المشكلة Runtime.
- هل ظهرت Regression أخرى؟
- تاريخ التحقق.

صيغة مثال:

```text
Issue: HIMMA-AUD-XXX
Fix SHA: ...
Verification SHA: ...
CI: PASS
Hosted smoke: PASS
E2E: PASS
Status: VERIFIED-RESOLVED
Verified at: YYYY-MM-DD
Notes: ...
```

---

# 11) سجل التحديثات

## 2026-09-01 — الإصدار 1

**HEAD المرجعي عند الإنشاء:** `7268692b6e85df90bb800129ff8f99727bb5c168`

تم إنشاء السجل وجمع نتائج التدقيق المكتشفة حتى هذه النقطة، بما فيها:

- مشاكل Interaction contracts.
- الصوت.
- Product readiness.
- seed/bootstrap.
- scoring robustness.
- auth hardening.
- mobile/performance.
- CI/CD.
- Vercel/Railway/Supabase operational findings.
- المشاكل التاريخية التي أُصلحت مع إبقاء أثرها لمنع التكرار.

**ملاحظة:** بعض المشاكل التي كانت مؤكدة على نسخ أقدم وحدثت بعدها تغييرات كبيرة في Content/Renderer تم تحويلها إلى `NEEDS-REVALIDATION` بدل الادعاء بأنها ما زالت مفتوحة على HEAD الحالي.

---

# 12) قاعدة العمل من الآن

هذا الملف هو **مرجع التدقيق المستمر الرسمي**.

عند أي فحص لاحق:

- تُضاف المشاكل الجديدة هنا.
- تُحدّث حالات المشاكل القديمة هنا.
- تُوثق الإصلاحات هنا.
- تُوثق إعادة الاختبار هنا.
- لا نعتمد الذاكرة أو المحادثة وحدهما لتحديد ما بقي من المشاكل.

الهدف النهائي أن يتحول هذا السجل تدريجيًا من قائمة اكتشافات إلى سجل إثبات أن كل Release Blocker تم إغلاقه والتحقق منه قبل الإطلاق.
