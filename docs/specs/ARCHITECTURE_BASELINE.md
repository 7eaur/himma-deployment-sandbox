# خط الأساس المعماري

هذه معمارية افتراضية قوية ومتناسبة مع المنصة. يجوز تعديلها في المرحلة 0 فقط بسبب موثق ومراجعة هندسية.

## الشكل العام

```text
Browser
  -> Reverse proxy / HTTPS
     -> apps/web (Arabic RTL UI)
     -> services/api (domain API)
        -> PostgreSQL
        -> private object storage
        -> Redis queue
           -> services/worker -> replaceable speech provider
```

## الوحدات

- `apps/web`: React/Next.js + TypeScript. تجربة الطالب والباحثة، ولا يحتوي قواعد درجات أو تكيف مرجعية.
- `services/api`: FastAPI/Python modular monolith. يملك المصادقة والصلاحيات والطلاب والمحتوى والمحاولات والتكيف والتقارير والتدقيق.
- `services/worker`: عامل Python يستخدم نفس حزمة المجال لمعالجة الصوت والتصدير الطويل.
- `packages/contracts`: OpenAPI/generated client and shared validation artifacts.
- `packages/content`: JSON/YAML versioned content bank with schema validation and idempotent seed tooling.
- PostgreSQL: source of transactional truth.
- Redis: queue and short-lived coordination only; never source of academic truth.
- S3-compatible private storage: recordings, generated reports, and immutable approved assets where appropriate.

## حدود إلزامية

- الواجهة لا تتصل بقاعدة البيانات مباشرة ولا تعيد حساب الدرجات أو قرارات التكيف.
- كل تغيير مؤثر في الدرجة/المستوى/المراجعة/المحتوى يمر بخدمة المجال ويسجل تدقيقًا.
- المحتوى التعليمي ليس JSX مبعثرًا؛ هو بيانات مُعرّفة ومتحقق منها ومُصدّرة بإصدار.
- مزود الصوت خلف interface واضح ويحفظ اسم المزود وإصدار النموذج والعتبة مع كل تحليل.
- نشر موحد عبر Docker Compose في التطوير والإنتاج الأولي، مع إمكانية استبدال البنية دون تغيير المجال.
- نفس الأصل يولد بيانات اللوحة وExcel وPDF لتجنب اختلاف الأرقام.

## اختبارات المعمارية

- Unit: قواعد الدرجات والتكيف والحالات والمحاذاة.
- Integration: API + PostgreSQL + queue/storage adapters.
- Contract: OpenAPI client compatibility and content schemas.
- Component: تفاعلات القوالب العربية والوصولية.
- E2E: UC-01..UC-12 في متصفح حقيقي.
- Restore drill: استعادة قاعدة وملف تسجيل/تقرير من نسخة احتياطية.

## لماذا لا نعتمد نموذج الواجهة مباشرة؟

النموذج الحالي جيد كتغذية بصرية، لكنه يحتوي منطق عرض في صفحة واحدة، بيانات تجريبية، مؤقتات تحاكي الصوت، ومخطط قاعدة بيانات فارغ. تنقل منه الأصول والتوكنات وأنماط التفاعل بعد تفكيكها، ولا تنقل محاكاة المجال.

