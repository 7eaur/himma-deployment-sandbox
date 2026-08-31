# سجل الفجوات - GAP REGISTER
# P01 Audit — 17 أغسطس 2026

## أولوية P0 — تمنع الاستخدام الإنتاجي وتخرق الثقة

### G-P0-01: MinIO Mock في مسار الصوت الإنتاجي
- **الملف:** `services/api/storage.py`
- **الدليل:** `storage.py` يرجع URLs بنمط `mock-s3-bucket.local`، و`STAGE_02_REVIEW.md` ادّعى وجود MinIO حقيقي.
- **الأثر:** كل عملية رفع صوتية تُكتب في قاعدة البيانات بـ key وهمي، مما يجعل بيانات الدراسة غير موثوقة.
- **الإصلاح اللازم في P02:** استبدال بـ MinIO/S3 حقيقي في CI وتثبيت الرفع والاسترجاع.

### G-P0-02: PostgreSQL مفقود في CI وبيئة الاختبار
- **الدليل:** `ci.yml` لا يُشغِّل PostgreSQL service، و`conftest.py` يستخدم SQLite.
- **الأثر:** اختبارات Backend لا تكتشف أي bug مرتبط بـ PostgreSQL-specific SQL أو Enum casting.
- **الإصلاح اللازم في P02:** إضافة PostgreSQL و MinIO service containers إلى CI.

### G-P0-03: ادعاء E2E ناجح في STAGE_02_REVIEW.md وهو كاذب
- **الدليل:** `vertical-slice.spec.ts` فشل بـ Timeout 30s (مُثبت بـ task-2016 logs).
- **الأثر:** بوابة المرحلة 02 أُغلقت على أدلة مزوّرة.
- **الإصلاح اللازم في P02:** إعادة تشغيل E2E حقيقي بعد إصلاح المصادقة.

---

## أولوية P1 — تعطل مسارات أساسية

### G-P1-01: حلقة 307 في المصادقة تكسر E2E
- **الملف:** `apps/web/src/middleware.ts`
- **الأعراض:** `middleware.ts` يُعيد توجيه أي طلب بدون Cookie إلى `/admin/login`، لكن Playwright لا يُرسل Cookie بعد Login في الطلب التالي بشكل صحيح.
- **السبب المحتمل:** Cookie `HttpOnly` + `SameSite=Lax` لا يُرسله المتصفح في Playwright عند Redirect أو URL change.
- **الإصلاح اللازم في P02:** تشخيص Network Trace في Playwright + فحص Cookie headers + اختبار `SameSite=None; Secure`.

### G-P1-02: الرفع الصوتي غير مثبت من نهاية لنهاية
- **الملفات:** `useAudioRecorder.ts`, `AssessmentRunner.tsx`, `storage.py`
- **الأثر:** لا يوجد دليل على أن Blob صوتياً حقيقياً وصل إلى MinIO bucket ثم استُرجع.
- **الإصلاح اللازم في P02:** إصلاح storage.py + اختبار رفع/استرجاع حقيقي.

---

## أولوية P2 — جودة وتصميم

### G-P2-01: Emoji في واجهة المستخدم
- **الملفات:** `student/session/[id]/page.tsx`, `AssessmentRunner.tsx`, `audio-review/page.tsx`
- **الأمثلة:** 🚀، 🎉، ✅، ❌، 👋
- **قاعدة الهوية:** "لا إيموجي إطلاقًا في الواجهة أو التنقل أو الحالات" (P03 Design Rules)
- **الإصلاح:** استبدال بأيقونات SVG من `assets/`

### G-P2-02: Inline Styles المتناثرة
- **الأمثلة:** عشرات `style={{ marginBottom: ..., color: ..., flex: 1 }}` في صفحات الإدارة.
- **الإصلاح:** نقل إلى CSS Modules أو Design Tokens.

### G-P2-03: غياب لقطات شاشة الاستجابة
- **المطلوب:** 360×800، 390×844، 768×1024، 1024×768، 1440×900
- **الحالة:** لم تُلتقط.

### G-P2-04: شعار نصي في بعض الصفحات
- **الأمثلة:** "هِمّة" كنص في بعض headers بدلاً من أصل الشعار الرسمي.

---

## أولوية P3 — تحسينات لا تمنع الاستخدام

### G-P3-01: صفحة student/activity/[id] Placeholder
- **الحالة:** تعرض "هذا النشاط قيد التطوير" فقط.

### G-P3-02: رسائل خطأ تسجيل الدخول غير دقيقة
- **المطلوب:** تمييز "كلمة مرور خاطئة" عن "مستخدم غير موجود" أو التوحيد للأمان.

### G-P3-03: أيقونات التنقل في Sidebar غير متوافقة مع assets معتمدة
