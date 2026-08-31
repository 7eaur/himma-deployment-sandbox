# توصية التعافي - RECOVERY RECOMMENDATION
# P01 Audit — 17 أغسطس 2026

## القرار: الاستمرار من HEAD الحالي (88c0e71)

لا يلزم إجراء `git reset` أو حذف commits. الكود الموجود قابل للإنقاذ والتطوير. نوصي بالمسار التالي في P02.

---

## مسار التعافي المقترح لـ P02

### الخطوة 1: تجهيز البيئة الإنتاجية في CI

**المطلوب:** تحديث `.github/workflows/ci.yml` ليُشغّل:
- `postgres:16-alpine` مع credentials محددة
- `minio/minio` مع bucket initialization
- `redis:7-alpine`

**السبب:** كل الاختبارات الحالية تعمل على SQLite وهمي مما يجعلها غير ذات قيمة للإنتاج.

**الأوامر اللازمة:**
```yaml
services:
  postgres:
    image: postgres:16-alpine
    env: { POSTGRES_PASSWORD: <set-in-ci>, POSTGRES_DB: himma_db }
  minio:
    image: minio/minio
    command: server /data
redis:
    image: redis:7-alpine
```

### الخطوة 2: إصلاح storage.py

**الملف:** `services/api/storage.py`  
**المطلوب:** استخدام `boto3` حقيقي مع MinIO في CI.

### الخطوة 3: إصلاح حلقة 307 في المصادقة

**الملف:** `apps/web/src/middleware.ts`  
**الجذر المشتبه به:** Cookie `HttpOnly + SameSite=Lax` لا يُرسله Playwright في redirect.

**الحلول المقترحة (تُختبر بالترتيب):**
1. التأكد من أن `set-cookie` يصل من Backend
2. تجربة `SameSite=None; Secure` لتجاوز قيد Lax في redirects
3. إضافة `storageState` في Playwright لحفظ واسترجاع Cookie
4. تغيير `next.config.ts` rewrites للتأكد من أن `/api/auth/login` يمر صحيحاً

### الخطوة 4: اختبار Alembic upgrade → downgrade → upgrade

**الأمر:** (يتطلب PostgreSQL)
```bash
alembic upgrade head
alembic downgrade base
alembic upgrade head
```
**الهدف:** التأكد من أن migrations قابلة للعكس وأن البنية متسقة.

### الخطوة 5: Seed مرتين والتأكد من Idempotency

**الأمر:** (يتطلب PostgreSQL)
```bash
python seed.py
python seed.py  # مرة ثانية — يجب ألا يُضاعف البيانات
```
**التأكد:** عدد content_items = عدد محدد، access_codes ثابتة، لا أخطاء.

### الخطوة 6: E2E كامل بدون Mock

**الهدف:** تشغيل السيناريو الكامل:
1. Admin Login
2. Create Student
3. Admin Logout
4. Student Login
5. Start Pretest (30 questions)
6. Record Audio (real blob)
7. Upload to MinIO (real)
8. Admin Review Audio
9. Grade Audio
10. Verify Level Assignment

---

## ما يجب الحفاظ عليه

| المكوّن | القرار |
|---|---|
| `packages/content/src/catalog.json` | يُحفظ |
| `services/api/db/models.py` | يُحفظ ويُطوَّر |
| `services/api/assessment.py` | يُحفظ |
| `services/api/auth.py` | يُحفظ |
| `apps/web/src/components/AssessmentRunner.tsx` | يُصلح |
| `apps/web/src/middleware.ts` | يُصلح |
| `services/api/storage.py` | يُستبدل بحقيقي |
| `docs/stages/STAGE_02_REVIEW.md` | يُوسم [SUPERSEDED] |

---

## ما لا يجوز فعله

- لا `git reset --hard` أو حذف commits تاريخية.
- لا استمرار استخدام `mock-s3-bucket.local` في أي اختبار يُحتسب.
- لا ادعاء اجتياز بوابة قبل تشغيل اختبارات حقيقية على PostgreSQL + MinIO.
