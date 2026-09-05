# نظام تصميم مهام الطالب — المرجع التنفيذي الموحّد

**التاريخ:** 2026-09-04  
**الحالة:** ACTIVE / CANONICAL  
**النطاق:** الاختبار القبلي، الاختبار البعدي، أنشطة المستويات، التقوية

## 1. القرار

قالب المهام الوحيد المعتمد هو:

`apps/web/src/app/student/session/[id]/session.module.css`

ويستخدمه كل من:

- `apps/web/src/app/student/session/[id]/page.tsx`
- `apps/web/src/app/student/activity/[id]/page.tsx`

لا يوجد قالب مستقل للاختبار وقالب مستقل للنشاط. الاختلافات الأكاديمية تأتي من **Structured API + interaction type + data**، وليس من نسخ واجهات متوازية.

## 2. ما أُلغي

ألغيت طبقات العرض التالية لأنها كانت Overrides/patches فوق القالب الأساسي:

- `student-experience.css`
- `activity-polish.css`
- DOM/Portal injection الخاص بـ`TemporaryAudioSkipControl`

كما أزيل `studentPath.module.css` لأنه Legacy وغير مستخدم بعد إلغاء `path_sequence` من العقد الأكاديمي.

## 3. قواعد ممنوعة

لا يضاف مستقبلًا أي حل يعتمد على واحد من الآتي لتصحيح تصميم المهمة:

- ملف `*-polish.css` يعيد تعريف القالب الأساسي.
- selectors من نوع `[class*="..."]` للوصول إلى CSS Module من الخارج.
- استخدام `data-testid` كـCSS hook بصري.
- `!important` لتجاوز تصميم مكوّن آخر بدل إصلاح مصدره.
- `MutationObserver` أو `querySelector` لإعادة كتابة السؤال أو الخيارات أو حقن عنصر وظيفي في موضع تخميني.
- parsing للنص الخام أو regex لاستخراج الخيارات/السؤال من prompt.
- إخفاء/إظهار محتوى أكاديمي لمعالجة خطأ في الـAPI.

إذا احتاج التصميم إلى تغيير، يعدل القالب أو المكوّن الأصلي مباشرة.

## 4. المعمارية الصحيحة

```text
Approved academic source
        ↓
Versioned projection / seed
        ↓
PostgreSQL runtime snapshot
        ↓
Structured student API
        ↓
Deterministic React renderer
        ↓
Canonical task CSS module
```

العرض لا يقرر صحة المحتوى، والمحتوى لا يحمل HTML/CSS لإجبار الواجهة على شكل معين.

## 5. Layout الأساسي

القالب الحالي يستخدم Grid طبيعيًا بدل التموضع المطلق:

```text
meta
content | coach
actions
```

وعلى الشاشات الأصغر يتحول إلى:

```text
meta
content
coach
actions
```

الهدف أن تكون الشخصية وCTA جزءًا من التدفق الطبيعي، فلا نحتاج هوامش وهمية أو absolute positioning ثم ملفات Patch لمنع القص.

## 6. عناصر القالب المشتركة

العناصر الأساسية التي يجب إعادة استخدامها:

- Header/logo/back action.
- Progress panel.
- Assessment/level badge.
- Skill chip.
- Question title.
- Text/letter stimulus.
- Context image.
- Listen control.
- Instruction row.
- Text choices.
- Image choices.
- Sequence board.
- Memory preview/recall.
- Reading text.
- Recording panel.
- Neutral media-gap notice.
- Coach/mascot message.
- Primary/secondary actions.
- Loading/error/result states.

## 7. Responsive contract

القالب يستهدف Desktop وTablet وMobile من نفس الملف.

قواعد إلزامية:

- لا horizontal overflow.
- CTA يبقى ظاهرًا وقابلًا للوصول.
- minimum touch target = 44px.
- النص العربي يلتف طبيعيًا عند الحاجة؛ لا يجبر على سطر واحد إذا كان ذلك يسبب قصًا.
- الصور تحافظ على semantic visibility و`object-fit: contain` عند الحاجة التعليمية.
- Mobile لا يخفي الماسكوت أو التعليمات لحل مشكلة المساحة؛ يعاد ترتيبها.
- short viewport يسمح بالتمرير بدل قص المهمة.
- `prefers-reduced-motion` محترم.

## 8. عقود الاختبارات

`data-testid` وARIA مخصصة للاختبار وإمكانية الوصول، لا للتصميم.

العقود الحالية للأنشطة تشمل أمثلة مثل:

- `activity-session`
- `activity-option`
- `activity-image-options`
- `activity-text-options`
- `activity-sequence-options`
- `activity-sequence-image-options`
- `activity-memory-preview`
- `activity-reading-text`
- `activity-listen-prompt`
- `declared-media-gap`

الخيار القابل للتحديد يستخدم `aria-pressed` بدل أن يضطر E2E لتخمين DOM.

## 9. Memory activity

العقد المعتمد:

1. تظهر صور الذاكرة كاملة.
2. لا تختفي بتايمر خفي.
3. الطالب يضغط `التالي` صراحة.
4. ينتقل إلى recall/reorder.
5. لا يعرض النظام الإجابة الصحيحة تلقائيًا.

## 10. Assessment neutrality

في الاختبار القبلي/البعدي:

- لا feedback يكشف الصواب/الخطأ.
- لا hint يكشف الإجابة.
- لا reward مبني على إجابة سؤال منفرد.
- حالة انتظار مراجعة الصوت منفصلة عن answering/done.

## 11. Media gaps

إذا كان أصل ثابت مطلوب غير موجود:

- Structured API يعلن `media_gaps`.
- الواجهة تعرض حالة محايدة.
- لا تعرض نص القصة الداخلي بدل التسجيل.
- لا تستخدم substitute audio.
- لا تولد أصلًا مزيفًا داخل renderer.

المرجع الحالي للفجوات:

`docs/specs/AUDIO_INVENTORY_AND_GAPS_2026-08-28_AR.md`

## 12. Temporary development tools

أي أداة خاصة بالتطوير يجب أن تكون:

- explicit component/service؛
- fail-closed خارج development؛
- غير مستخدمة لإنتاج score/mastery/reward؛
- منفصلة عن منطق التقييم الدائم؛
- قابلة للحذف دون إعادة تصميم المنتج.

لهذا أصبح التحكم المؤقت بالصوت Component صريحًا داخل لوحة التسجيل بدل Portal/MutationObserver.

## 13. Definition of Done لأي تعديل بصري

لا يعد التعديل منتهيًا إلا إذا:

1. لم يضف Patch layer جديدًا.
2. TypeScript وlint وunit tests ناجحة.
3. Build ناجح.
4. Responsive gate ناجح.
5. E2E للعقد المتأثر ناجح.
6. لا console/runtime errors واضحة.
7. الصور من نفس SHA تثبت Desktop/Mobile للشاشة المتأثرة عند التغيير الجوهري.
8. لا يتغير المحتوى الأكاديمي أو scoring عرضيًا.
