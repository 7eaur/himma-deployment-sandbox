# خطة التوحيد والتقوية الشاملة — منصة هِمّة

**التاريخ:** 2026-09-04  
**الحالة:** ACTIVE — architecture/content reconciliation complete; final exact-SHA verification remains  
**المستودع:** `7eaur/himma-`  
**الفرع:** `recovery/ui-media-admin-overhaul`

## الهدف المعماري

```text
Approved versioned source
  -> deterministic projection/seed
  -> PostgreSQL runtime
  -> structured API
  -> deterministic renderer
```

قواعد ملزمة:

- لا raw-prompt parsing أو DOM patching لحالة التطبيق.
- لا `*-polish.css` كطبقة علاج فوق قالب مكسور.
- لا duplicate FastAPI routes يعتمد حسمها على registration order.
- لا منطق أكاديمي دائم داخل ملف Temporary.
- لا تعديل Runtime بعد الإسقاط عبر patch لاحق.
- لا placeholder/substitution لأصل صوتي مفقود.
- لا تقرير ينشئ mastery evidence.

## منجز — Student Design System

- `session.module.css` هو القالب المشترك الحقيقي لمهام الاختبار والتعلم والتقوية.
- Coach/CTA في layout طبيعي responsive، وليس absolute + override.
- أزيلت طبقات `student-experience.css` و`activity-polish.css` والـDOM enhancers/MutationObserver state inference.
- عقود التفاعل والاختبار تعتمد semantic UI state و`data-phase`/`aria-pressed` بدل copy هش.

المرجع: `docs/architecture/STUDENT_TASK_DESIGN_SYSTEM_AR.md`.

## منجز — Assessment / Activities ownership

- `assessment_completion.py` هو المالك الدائم لإنهاء pre/post assessment.
- Retake يستخدم عقد الإنهاء canonical ويحافظ على attempt history والـofficial reporting index.
- Activities public routes لها مالك واحد؛ legacy helpers ليست Router runtime منافسًا.
- اختبارات regression تمنع عودة duplicate ownership.

## منجز — Auditory content source

- `packages/content/src/l1_auditory_comprehension_v1.json` هو المصدر versioned لقصتي ليان ونادر.
- أزيل `patch_db_runtime()`.
- `L1-CORE-09` و`L1-REIN-11` مرتبطان بـ`الفهم السمعي المباشر` مع الحفاظ على صف Skill التاريخي/FKs بدل حذف التاريخ.
- `path_sequence` القديم ليس interaction canonical في Runtime الحالي.

## منجز — الصوت الثابت

الحالة السابقة `EXTERNAL-GATED بسبب موز/سَا/القصتين` **مغلقة**.

الأصول المعتمدة الحالية:

- `LET-01` = **مَ**؛ بايتات المصدر المعتمد `SYL-15` منشورة تحت المعرّف التاريخي نفسه.
- `WRD-29` = **موز**.
- `SYL-13` = **سَا** ويخدم موضعي Core/Reinforcement المعتمدين.
- `INS-01` = قصة ليان في المزرعة.
- `INS-02` = قصة نادر في الشاطئ.

إجمالي الحزمة: 54 WAV + 54 MP3. Required static audio gaps = 0.

تم التحقق من الأزواج العشرة المتغيرة/الجديدة كملفات فعلية في GitHub ومطابقتها للحزمة المعتمدة بالحجم وGit blob SHA؛ SHA-256 موثق في:

`docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_2026-09-04_AR.md`.

`packages/content/src/audio_asset_requirements_v1.json` هو الإصدار 1.2 ويعلن `known_missing_required_assets=[]` وسياسة عدم substitution وعدم عرض نص القصة بدل الصوت.

## منجز — حذف Temporary Audio Skip

الحذف كامل، وليس تعطيلًا فقط:

- UI control: removed.
- related styles: removed.
- FastAPI router registration: removed.
- runtime feature flag: removed.
- backend module `temporary_audio_skip.py`: removed.
- env examples: لا تحتوي متغيرًا يعيده.

المسار الحالي للتسجيل:

`record -> persist/upload -> supervisor review -> accepted/rerecord required -> continue`

المشرف هو سلطة القرار الحالية حتى دمج النموذج الآلي المعتمد. `waiting_audio_review` لا يعني نجاحًا ولا ينشئ score/mastery.

## M08 — فصل حالتين كانتا مختلطتين

### M08-A Fixed Prompt/Story Audio

**CLOSED** — الأصول موجودة ومربوطة ولا توجد فجوة ثابتة متبقية.

### M08-B Automatic Speech Analysis

**OPEN / FUTURE PRODUCTION GATE**.

الهدف: Reference-Guided Arabic Reading Analysis = ASR + reference alignment + C/D/I/S + phonemic helper evidence.

المتبقي قبل جعل النموذج سلطة إنتاجية:

- provider integration/approval;
- calibration and confidence thresholds;
- privacy/retention agreement;
- human override/audit policy;
- regression/evaluation evidence.

لا يجوز إعادة وصف هذه البنود بأنها «أصوات ناقصة».

## Admin reconciliation

المكونات المشتركة والإشعارات في الرسمي تمت مراجعتها مقابل Sandbox؛ الفروق المتبقية غير الجوهرية لا تبرر نقل Sandbox أو commit شكلي. الرسمي يبقى Source of Truth.

## Critical legacy cleanup

أزيلت طبقات polish وDOM enhancers وTemporary Audio Skip و`scratch.py` وCSS الخاص بمسار القراءة القديم. أي ملف legacy متبقٍ خارج runtime الحرج يعالج فقط بدليل consumer/search/tests، لا purge أعمى.

## التحقق النهائي — P0

لا تعتبر الخطة CLOSED حتى يتوفر الدليل المناسب على المرشح التنفيذي الحالي:

1. `Himma CI — Quality Gate`: backend + frontend + integration.
2. M04 Responsive Visual Gate عند وجود تغييرات UI ذات صلة، مع artifact قابل للفحص.
3. M09 Release Readiness للمرشح المقصود للإطلاق.
4. عدم استخدام run قديم سبق رفع الباينري كدليل للحالة الحالية.

الـdocumentation-only SHA يمكن تمييزه عن executable candidate، لكن لا يجوز نسب نتيجة run لSHA آخر.

## P1/P2 المتبقي

- توسيع visual regression ليشمل authenticated student/admin flows بالكامل إذا لم تكن artifacts الحالية تغطيها.
- استكمال M09 full single-candidate UAT، monitoring/request correlation، support/rollback، وprivacy/retention final approval.
- استخراج Activity service module أنظف مستقبلًا إذا ثبتت فائدة الصيانة، دون إعادة duplicate router.
- Dead CSS audit بعد استقرار screenshots وبلا purge آلي أعمى.

## Source of Truth

- Official: `7eaur/himma-`.
- Branch العمل الحالي: `recovery/ui-media-admin-overhaul`.
- Sandbox: reference/history فقط؛ لا يصبح canonical بمجرد وجود وثائق أو CSS مختلفة.

## قاعدة الإغلاق

لا PASS/CLOSED دون evidence. لا production merge/release دون موافقة المستخدم الصريحة. لا حذف تاريخ/DB/attempt/mastery لإرضاء seed أو test. لا fabricate/substitute media.
