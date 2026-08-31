# الحالة الحالية لمنصة هِمّة — 2026-08-28 — تحديث M06

## 1. Git

المستودع: `7eaur/himma-`  
الفرع التنفيذي: `recovery/ui-media-admin-overhaul`

آخر **Implementation HEAD** قبل commits التوثيق الحالية:

`98fdc638737bdb8ab9be4937cff6155865998d1f`

Commit:

`test(M06): target visible dashboard heading across responsive layouts`

> ملاحظة: commits التوثيق بعد هذا السطر ستدفع HEAD للأمام. عند الاستئناف افحص HEAD الفعلي، ولا تعتبر SHA التوثيقية تغييرًا في منطق المنتج.

## 2. CI الفعلي الحالي

### Responsive Visual Gate

Run #18 / ID `33202256450` على `98fdc638...`: **SUCCESS**.

### Main Quality Gate

Run #298 / ID `33202256449` على `98fdc638...`:

- Backend: **SUCCESS**.
- Frontend: **SUCCESS**.
- Integration/Playwright: **FAILURE**.

الفشل الوحيد الموثق حاليًا داخل:

`tests/e2e/accessibility-integration.spec.ts`

الاختبار:

`mobile supervisor navigation keeps touch targets and layout intact`

الوقائع من log:

- dialog «قائمة لوحة المشرف» يظهر بنجاح.
- الاختبار يبحث عن `a.sidebar-nav-item` داخل الـdialog.
- لا يجد العنصر بهذا المحدد.
- الاختبار يفشل قبل قياس ارتفاع Touch Target.
- بقية اختبارات M06 في نفس التشغيل نجحت.
- الـVertical Slice الكامل نجح.

إذن الحالة الأقرب: **selector/markup contract mismatch في اختبار M06 للجوال**، وليس انهيارًا في الـBackend أو المحتوى أو رحلة الطالب.

## 3. برنامج الصيانة

| المرحلة | الحالة الحالية |
|---|---|
| M00 — Restore green baseline | CLOSED |
| M01 — Placement scoring & gates | CLOSED |
| M02 — Adaptation state machine | CLOSED |
| M03 — Reinforcement mapping/content | IMPLEMENTED؛ 3 residual content gaps موثقة |
| M04 — Student Product UI | REBUILT / baseline accepted |
| M05 — Supervisor Product UX | REBUILT / baseline accepted |
| M06 — Responsive/Accessibility/Design QA | **ACTIVE** |
| M07 — Research Reports | PENDING |
| M08 — Real Speech Analysis | PENDING / external gates |
| M09 — Release/UAT | PENDING |

## 4. المحتوى

المحتوى الأصلي المعتمد محفوظ:

- 30 سؤال قبلي.
- 30 سؤال بعدي.
- 30 نشاط أساسي.
- 15 نشاط تقوية أصلي.
- الإجمالي الأصلي: **105**.

إضافات M03 المعتمدة:

- L1: +7.
- L2: +6.
- L3: +5.
- الإجمالي الجديد: +18 تقوية.

Full runtime catalog بعد `seed_all.py`:

- baseline = 105.
- reinforcement total = 33.
- total items = **123**.
- skills = 44.

### فجوات التقوية المتبقية

موثقة في `M03_RESIDUAL_CONTENT_GAPS_2026-08-28_AR.md` ولا يجوز عمل random/cross-level fallback لها:

1. L2 قراءة كلمات السكون.
2. L3 الفهم المباشر.
3. L3 بناء الجملة.

إلى أن تعتمد معالجة تربوية: Safe Hold / supervisor path.

## 5. المنطق الأكاديمي الحالي

### Placement

- القبلي يحدد **نقطة البداية** وليس نهاية المسار.
- scoring مبني على أقسام 20/40/40.
- readiness أقل من 12/20 يفرض L1.
- أي بوابة L3 تعتمد دليل قراءة/صوت غير معاير لا يجوز اختراع threshold لها.
- عند غياب دليل صوتي لازم بسبب TEMP skip يكون القرار provisional/neutral حيث يلزم.

### Learning journey

- بداية L1 → L1 ثم L2 ثم L3 ثم Posttest.
- بداية L2 → L2 ثم L3 ثم Posttest.
- بداية L3 → L3 ثم Posttest.
- لا Posttest بعد L1/L2 فقط.

### Activity adaptation

- `>=80%` pass.
- `70–<80%` guided retry.
- `<70%` weakness + targeted reinforcement.
- mastery trend: آخر 3 محاولات صالحة بأوزان 50/30/20.
- mastery لا يلغي شرط 10/10 core.
- Level completion يحتاج إكمال الأنشطة وعدم وجود تقوية/ضعف غير محسوم.

### Reinforcement cycle

ضعف → reinforcement mapped by skill/family → completion → return-to-core verification → continue.  
محاولات التحقق bounded؛ عند التعثر ينتقل للمشرف بدل loop لا نهائي.

**Automatic Demotion:** لم يُحسم نهائيًا. لا تحذف policy القديمة صامتًا؛ الاتجاه المنتجّي الحالي يفضل support داخل المستوى + manual override للحالات الاستثنائية.

## 6. الصوت

- fixed audio assets الموجودة: 50.
- الفجوتان المؤكدتان فقط: «موز» و«سَا».
- الهدف بعد التسجيل: 52.
- التقويات الـ18 الجديدة تعيد استخدام المكتبة الحالية ولا تضيف فجوات ثابتة أخرى معروفة.
- `HIMMA_TEMP_AUDIO_SKIP=true` وضع تجريبي مؤقت:
  - لا mic permission.
  - لا ملف وهمي.
  - لا MinIO upload.
  - لا score/reward/mastery/weakness/adaptation evidence.
  - assessment denominator يستبعد skipped voice items.

## 7. ASR

الموجود تقنيًا:

- queue/worker/retries/dead-letter.
- provider adapter abstraction.
- reference-guided alignment.
- C/D/I/S representation.
- confidence/manual-review fallback infrastructure.

غير المنجز/غير المعتمد:

- real provider selection/connection.
- calibration على تسجيلات ممثلة.
- confidence thresholds.
- privacy/transfer/cost decision.
- child-audio retention policy.

لا يُقال إن ASR مكتمل.

## 8. Student UX بعد M04

- Learning Stage ممتدة باستخدام `100dvh`.
- assessment + activities + reinforcement أقرب لنظام موحد.
- الشخصية التعليمية أصبحت بارزة وتعليماتها contextual أكثر.
- responsive rules مضافة للهاتف/تابلت/desktop.
- reduced motion مدعوم.
- five-size responsive visual workflow موجود.

## 9. Supervisor UX بعد M05

- Admin shell وSidebar أُعيدا تنظيمهما.
- Dashboard أصبح Action Center ثم summary/stats.
- ملف الطالب تحول من صفحة طويلة إلى Workspace tabs.
- reinforcement review أصبح alert مختصرًا expandable بدل form ضخم دائم.
- Settings قسمت إلى account/security/supervisors.
- Vertical Slice عُدل ليتعامل مع tabs الجديدة ونجح في Run #298.

## 10. M06 المنجز حتى الآن

- global focus safeguards.
- reduced-motion safeguards.
- accessible primary/success contrast tokens.
- integration accessibility suite.
- checks نجحت لـ:
  - RTL/keyboard/focus/overflow.
  - reduced motion.
  - 200% zoom equivalent.
  - contrast tokens.
  - عدم كشف implementation vocabulary للطفل.
- Responsive Visual Gate على المقاسات الإلزامية أصبح أخضر.

## 11. المهمة التالية الدقيقة

1. افحص markup الخاص بـMobile Admin Sidebar/Dialog واختبار `accessibility-integration.spec.ts`.
2. وحّد selector بعقد semantic ثابت (يفضل role/link أو data-testid واضح) بدل الاعتماد على class غير موجودة.
3. أبقِ شرط touch target `>=44px` كما هو؛ لا تخفض الاختبار لإخضاره.
4. أعد Main Quality Gate حتى Backend + Frontend + Integration كلها SUCCESS.
5. بعدها أكمل M06: keyboard/focus/zoom/contrast/RTL/mobile screenshots النهائية ثم وثق closure.
6. ثم M07.
