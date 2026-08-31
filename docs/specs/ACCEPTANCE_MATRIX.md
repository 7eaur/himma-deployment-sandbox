# مصفوفة القبول

| ID | السلوك المقبول | المرحلة | دليل الإغلاق الأدنى |
|---|---|---:|---|
| AC-01 | RTL متجاوب دون كسر على الهاتف والكمبيوتر | 1/6 | E2E + screenshots + a11y smoke |
| AC-02 | إنشاء 15 طالبًا برموز مستقلة وآمنة | 1 | integration + authorization tests |
| AC-03 | قبلي 30 سؤالًا وتوزيع صحيح بالحدود والبوابات | 2 | seeded E2E + boundary unit tests |
| AC-04 | 10 أساسية و5 تقوية لكل مستوى من المحتوى المعتمد | 2 | schema/seed audit + UI sample per template |
| AC-05 | مهمة واحدة مع حفظ المحاولات والزمن والتلميحات | 2 | integration + E2E recovery |
| AC-06 | التسجيل يُحفظ ويرتبط بالمحاولة ويحلل عند الصلاحية | 2/4 | real adapter integration + E2E |
| AC-07 | نتيجة موثوقة أو «تحتاج مراجعة» دون تضليل | 2/4 | confidence boundary tests + review flow |
| AC-08 | الترقية/الثبات/الدعم/الخفض وفق القواعد | 3 | exhaustive boundary/property tests |
| AC-09 | سجل انتقال وتجاوز يدوي بسبب وتاريخ | 3 | audit integration + admin E2E |
| AC-10 | بعدي 30 سؤالًا ومؤشرات تحسن صحيحة | 5 | math tests + full E2E |
| AC-11 | اللوحة تعرض البيانات والتسجيلات والأخطاء والزمن | 5 | seeded dashboard E2E + authorization |
| AC-12 | Excel وPDF يطابقان مصدر بيانات اللوحة جوهريًا | 5 | golden export tests |
| AC-13 | الصوت الفاشل/المنخفض لا يؤثر في الدرجة أو التكيف | 2/4 | domain + queue failure tests |
| AC-14 | الاستئناف بعد الانقطاع دون ازدواج | 2/6 | idempotency + offline/retry E2E |
| AC-15 | تشغيل النطاق والدليل والنسخ الاحتياطي الأساسي | 6 | deployment smoke + restore drill |

أي إعفاء يحتاج قرارًا مكتوبًا، سببًا، أثرًا، وموعد إغلاق. لا يكفي أن يكتب الوكيل «تم».

