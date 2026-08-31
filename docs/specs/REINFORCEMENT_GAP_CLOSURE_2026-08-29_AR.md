# إغلاق فجوات التقوية — 2026-08-29

الحالة: **APPROVED / IMPLEMENTED — pending final CI evidence**

هذا القرار جاء من اعتماد المستخدم الصريح بتاريخ 2026-08-29، ولا يغيّر قواعد التصنيف أو حدود النجاح أو منطق 10/10 أو قاعدة عدم الاختيار العشوائي.

## 1) قراءة كلمات السكون — L2

المهارة: `sukoon_word_reading`.

القرار المعتمد: **لا نضيف نشاطًا جديدًا** ما دام المحتوى الموجود يعالج المهارة بشكل مناسب. تم ربط المهارة بالنشاط الموجود `L2-REIN-02` كـ supporting coverage بدل Safe Hold غير الضروري.

القاعدة تظل: نفس المستوى فقط، نشاط معتمد فقط، ثم إعادة تحقق بعد التقوية.

## 2) الفهم المباشر — L3

المهارة: `literal_comprehension`.

تمت إضافة نشاط مباشر جديد:

- `L3-REIN-11` — **أجب من النص**
- 5 جولات.
- جملة قصيرة ومعلومة صريحة.
- سؤال مباشر: أين/ماذا/من/بماذا.
- 3 بدائل لكل جولة.
- حد النجاح يبقى 80% وفق السياسة المعتمدة.
- إعادة التحقق مطلوبة.

المصدر التنفيذي: `packages/content/src/reinforcement_additions_v2.json`.

## 3) بناء الجملة — L3

المهارة: `sentence_building`.

تمت إضافة نشاط مباشر جديد:

- `L3-REIN-12` — **رتّب كلمات الجملة**
- 5 جولات.
- ترتيب كلمات لتكوين جملة عربية بسيطة وصحيحة.
- interaction: `sequence`.
- حد النجاح يبقى 80%.
- إعادة التحقق مطلوبة.

المصدر التنفيذي: `packages/content/src/reinforcement_additions_v2.json`.

## 4) الخريطة بعد الاعتماد

تم تحديث `packages/content/src/reinforcement_skill_map_v1.json` إلى map version `HIMMA-REINFORCEMENT-MAP-1.1`:

- `L2 / sukoon_word_reading` → `L2-REIN-02` (supporting).
- `L3 / literal_comprehension` → `L3-REIN-11` (direct).
- `L3 / sentence_building` → `L3-REIN-12` (direct).

لم يعد أي من هذه الثلاثة يعتمد على random fallback.

## 5) أثر الكتالوج

الكتالوج الأصلي 105 عنصرًا لا يتغير.

قبل هذا القرار:
- 15 تقوية أصلية.
- 18 إضافة v1.
- إجمالي التقوية = 33.
- إجمالي runtime = 123.

بعد القرار:
- +2 تقوية v2.
- إجمالي التقوية = **35**.
- إجمالي runtime = **125**.

## 6) ما لم يتغير

لم يتم تغيير:

- Placement.
- أوزان 20/40/40.
- readiness gate.
- 80/70 thresholds.
- 10 core activities per level.
- قواعد الترقية.
- قواعد التحليل الصوتي.
- قاعدة same-level-only.
- قاعدة no-random-fallback.

## 7) شرط الإغلاق النهائي

لا يتحول هذا الملف إلى CLOSED نهائيًا إلا بعد نجاح:

1. seed idempotency على 125 عنصرًا.
2. Backend tests.
3. Frontend tests/build.
4. Integration / Playwright.
5. التحقق من أن مهارات الفجوات الثلاث تعيد candidate معتمدًا بدل Safe Hold غير المبرر.
