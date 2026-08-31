# تقرير تسليم مشروع هِمّة — 2026-08-24

> **تصحيح أمني بتاريخ 2026-08-24:** كانت النسخة الأصلية من هذا التقرير
> تتضمن قيم اتصال محلية، ولذلك نُقّحت القيم أدناه. يجب تدوير أي قيمة سبق
> استخدامها فعليًا وعدم إعادة استعمالها. المعلومات التالية تميّز بين ادعاء
> التسليم التاريخي وبين ما أُعيد التحقق منه على فرع الاستعادة.

## معلومات Git
- الفرع الحالي: stage/04-production-slice
- SHA النهائي للفرع البعيد وقت الاستلام: `aa89aa8e628247151bf2e4a97eac30b50f9ea238`
- Remote: himma-github -> git@github.com:7eaur/himma-.git
- رابط الفرع: https://github.com/7eaur/himma-/tree/stage/04-production-slice

## حالة Git
- Commits محلية غير موجودة في GitHub: لا يوجد (مطابق تماماً)
- Working tree: نظيف (nothing to commit, working tree clean)
- git status: clean

## الفروع
- محلي: main, recovery/p02-baseline, stage/01-foundation, stage/02-content, stage/03-design-routes, stage/04-production-slice (الحالي)
- بعيد: himma-github/recovery/p02-baseline, himma-github/stage/02-content, himma-github/stage/03-design-routes, himma-github/stage/04-production-slice

## البنية التقنية (مُفحوصة من الكود)
### Frontend
- Framework: Next.js 16.3.0 مع Turbopack
- TypeScript: نعم (tsconfig.json موجود)
- CSS: Pure CSS (globals.css 1762 سطر) — بدون Tailwind
- المنفذ: 3000
- أمر التشغيل: cd apps/web && npm run dev (مع NEXT_PUBLIC_API_URL=http://localhost:8000)

### Backend
- Framework: FastAPI >=0.100.0
- Python: 3.12.3
- المنفذ: 8000
- أمر التشغيل: cd services/api && python run_dev.py

## الخدمات بدون Docker
| الخدمة | طريقة التشغيل | المنفذ | الحالة وقت التدقيق |
| PostgreSQL 18 | Windows Service (postgresql-x64-18) | 5432 | Running |
| MinIO | عملية Windows يدوية (minio.exe) | 9000/9001 | لم يكن يعمل |
| Redis | عملية Windows (redis-server) | 6379 | Running (PID 6328) |
| FastAPI | يدوي (python run_dev.py) | 8000 | لم يكن يعمل |
| Next.js | يدوي (npm run dev) | 3000 | لم يكن يعمل |

## أوامر التشغيل
```powershell
# 1. PostgreSQL يعمل تلقائياً كـ Windows Service

# 2. MinIO
C:\himma-services\minio\minio.exe server E:\himma-services\minio-data --console-address :9001

# 3. Redis — يعمل (راجع)

# 4. FastAPI
cd services/api
$env:DATABASE_URL='<set-locally>'
$env:API_SECRET_KEY='<set-locally>'
$env:S3_ENDPOINT='http://localhost:9000'
$env:S3_ACCESS_KEY='<set-locally>'
$env:S3_SECRET_KEY='<set-locally>'
$env:S3_BUCKET_NAME='himma-audio'
$env:REDIS_URL='redis://localhost:6379/0'
python run_dev.py

# 5. Next.js
cd apps/web
$env:NEXT_PUBLIC_API_URL='http://localhost:8000'
npm run dev
```

## متغيرات البيئة (بدون قيم)
### Backend: DATABASE_URL | API_SECRET_KEY | MINIO_ENDPOINT | MINIO_ACCESS_KEY | MINIO_SECRET_KEY | MINIO_BUCKET | REDIS_URL
### Frontend: NEXT_PUBLIC_API_URL

## Migrations وSeed
`powershell
cd services/api
alembic upgrade head   # تطبيق الـ migrations
python seed.py         # زرع البيانات: researcher1 + محتوى + طلاب نموذج
`
بيانات الباحثة: username=researcher1 | URL الأدمن: http://localhost:3000/admin/login (مباشر فقط)
رمز الطالب: يُنشأ من لوحة الباحث

## نتائج الاختبارات عند التسليم وإعادة التحقق
| الاختبار | exit code | النتيجة |
| TypeScript (npx tsc --noEmit) | 1 | فشل — 2 errors في session/[id]/page.tsx:285,296 |
| ESLint | 1 | فشل — 8 أخطاء إنتاجية عند إعادة التحقق |
| Frontend Jest | 1 | فشل — اختبارات قديمة وخلط اختبارات Playwright مع Jest |
| Backend pytest test_api.py | 1 | إعادة التحقق النظيفة: 22 passed / 1 failed / 2 errors |
| Alembic check | 1 | ادعاء التسليم: schema drift؛ لم يُعد تشغيله بعد على PostgreSQL مستقل |
| Alembic current | 0 | ادعاء التسليم فقط |
| Seed import | 0 | نجح |
| API smoke | - | لم يُشغَّل (يدوي مطلوب) |
| Next.js build | - | لم يُشغَّل (يدوي مطلوب) |

## الملفات المستبعدة من الرفع
.env / .env.local / node_modules/ / .next/ / __pycache__/ / venv/ — جميعها في .gitignore

## Secret Scan
فشل ادعاء `CLEAN` في النسخة الأصلية: احتوى التقرير نفسه على قيم اتصال محلية.
نُقّحت القيم من النسخة الحالية، ويجب إجراء فحص جديد وتدوير أي قيمة حقيقية قبل النشر.

## هل GitHub يحتوي جميع التغييرات المقصودة؟
نعم وفق تسليم الجهاز؛ والتحقق من GitHub أثبت أن رأس الفرع كان
`aa89aa8e628247151bf2e4a97eac30b50f9ea238`. آخر التزامين بعد `9636eed`
عدّلا هذا التقرير فقط، ولم يضيفا تغييرات برمجية.

## الفجوات للمهندس القادم
1. [حرجة] interaction_type mismatch: catalog.json يستخدم read_aloud لكن session/[id]/page.tsx تتوقع audio_record -> أسئلة الصوتية لن تعمل
2. [عالية] 2 TypeScript errors تمنع build نظيف في session/[id]/page.tsx:285,296
3. [عالية] Alembic schema drift: يجب فحص الفرق ومراجعته قبل إنشاء migration؛ لا يُشغّل autogenerate بصورة عمياء
4. [عالية] P04 E2E Playwright test (السيناريو الكامل) لم يُكتب
5. [متوسطة] ألوان inline غير معتمدة في page.tsx: #7C3AED (بنفسجي) و #D97706 (كهرماني)
6. [منخفضة] إيموجي في سؤال واحد في packages/content/src/catalog.json
7. [منخفضة] مجلد tests/ غير موجود في services/api/ — pytest يبحث عنه هناك
8. [منخفضة] Cookie SameSite=none (الكود) vs SameSite=lax (التوقع في test_api.py)

## الملخص النهائي (لا يحتمل التأويل)
1. فرع المصدر: stage/04-production-slice
2. SHA المصدر المتحقق منه: aa89aa8e628247151bf2e4a97eac30b50f9ea238
3. الرابط: https://github.com/7eaur/himma-/tree/stage/04-production-slice
4. هل كل تغييرات الجهاز رُفعت؟ نعم
5. هل working tree نظيف؟ نعم
6. هل بُني للتشغيل بدون Docker؟ نعم. هل ثبت تشغيل المكدس كاملًا وقت التسليم؟ لا؛ MinIO وFastAPI وNext.js لم تكن تعمل وAPI smoke/build لم يُنفذا
7. قاعدة البيانات والتخزين: PostgreSQL 18 (Windows Service) + MinIO (عملية مستقلة)
8. نتيجة إعادة التحقق الأولية: TypeScript وESLint وJest وpytest غير خضراء، وAlembic يحتاج تحققًا مستقلاً
9. مسار التقرير: docs/handoff/LOCAL_HANDOFF_2026-08-24.md
10. ملفات غير مرفوعة: .env / node_modules / .next / __pycache__ / venv (مستبعدة بشكل مقصود)
