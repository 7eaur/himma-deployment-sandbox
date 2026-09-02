# اقرأ أولًا — هِمّة Sandbox V3

**التاريخ:** 2026-09-02

هذا الملف هو نقطة الدخول الحالية لتوثيق تعديلات الـSandbox قبل أي محاولة نقل إلى المستودع الأصلي.

## ترتيب القراءة الإلزامي

1. `HIMMA_SANDBOX_FINAL_STATE_AND_MIGRATION_V3_2026-09-02_AR.md`
   - المرجع الأعلى للحالة المطلوبة الآن.
   - يحدد ما الذي يُنقل وما الذي لا يُنقل.
   - يحدد invariants وDefinition of Done.
   - ينتصر على Handoff الأقدم عند التعارض.

2. `HIMMA_SANDBOX_EXECUTION_CHANGELOG_V3_2026-09-02_AR.md`
   - السجل التفصيلي للمشاكل والتعديلات.
   - يشرح السبب الجذري لكل مشكلة مهمة.
   - يسجل المحاولات غير الكافية مثل إصلاح CTA الأول.
   - يسجل SHAs وCI evidence والحالة الحالية.

3. الوثائق الأقدم بتاريخ 2026-09-01 و2026-09-02
   - تستخدم كتاريخ وسياق فقط.
   - لا تتقدم على V3 عند التعارض.

## قرارات superseded يجب الانتباه لها

- path tracing القديم: ملغى.
- بديل اتجاه القراءة `من أين نبدأ القراءة؟ / يمين أم يسار؟`: ملغى.
- البديل النهائي: auditory literal comprehension story activity.
- أي ادعاء أن آخر Quality Gate Full Green: غير صحيح حاليًا.

## الحالة الحالية عند إنشاء هذا الفهرس

آخر functional/test SHA قبل commits التوثيق:

`cf679d86dad9750945fc5e55f12d207fbf4f86e6`

آخر Quality Gate تم تحليله:

`33582241449`

- Frontend SUCCESS.
- Backend FAILURE: 194 passed / 2 failed.
- Integration SKIPPED.
- السبب الحالي: completed assessment `/finish` يمر عبر authoritative retake/temporary-audio bridge قبل legacy assessment route، لذلك إصلاح replay داخل `assessment.py` وحده غير كافٍ.

## ممنوع

- Merge إلى الأصل لمجرد وجود هذه الوثائق.
- اعتبار Vercel/Railway READY بديلًا عن CI.
- cherry-pick أعمى لسلسلة Sandbox.
- إعادة القرارات المنسوخة المذكورة أعلاه.

**ابدأ دائمًا من V3، ثم قارن مع المستودع الأصلي قبل أي كتابة.**
