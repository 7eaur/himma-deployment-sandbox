# خطة إعادة بناء تجربة المنتج والواجهات — هِمّة

**التاريخ:** 2026-08-28  
**الحالة:** صيانة واجهات مطلوبة قبل التسليم النهائي

## الحكم

المنصة الحالية **Functional Recovery Baseline** وليست Final Product UI.

الـBackend والمسارات الأساسية قطعت شوطًا جيدًا، لكن تجربة الطالب والمشرف لا تزال أقل من مستوى منتج EdTech نهائي.

## 1. أهداف المنتج

- الطفل يشعر أنه داخل جلسة تعلم، لا يتصفح موقعًا.
- مهمة واحدة وتعليمة واحدة وإجراء رئيسي واحد.
- الشخصية مرافق تعليمي بارز ومفيد، لا زينة صغيرة.
- المشرف يرى ما يحتاج انتباهه أولًا، لا مجرد أرقام.
- كل شاشة متجاوبة وRTL وواضحة على الهاتف واللوحي والكمبيوتر.

## 2. أساس Styling

كان هناك خلط بين Tailwind-like classes وPure CSS utilities محدودة. أضيف Tailwind/PostCSS فعليًا في سلسلة commits الأخيرة، لكن يجب التحقق من النتيجة بصريًا وعدم الإبقاء على نظامين متعارضين.

المطلوب نظام واحد واضح + Design tokens.

الألوان:

- Blue `#347FD9`
- Green `#51B985`
- Yellow `#FFC857`
- Navy `#20364D`
- Background `#F7FBFF`
- Border `#DCE8F2`

الخطوط:

- Tajawal للطفل.
- IBM Plex Sans Arabic للمشرف والتقارير.
- Noto Sans Arabic fallback.

## 3. Student Full-Screen Learning Stage

الاختبار والنشاط والتقوية يجب أن تستخدم مساحة الشاشة كاملة بمرونة (`min-height: 100dvh`) بدل Card ضيقة وسط فراغ ضخم.

البنية المقترحة:

- Header: الشعار، التقدم، حفظ والخروج.
- Main stage: الشخصية + InstructionBubble + task interaction.
- Footer/action area: الإجراء الأساسي/المساعدة عند الحاجة.

لا يحتاج الطفل Navigation تقليديًا.

## 4. Student UI Kit

وحّد جميع القوالب حول:

- `StudentShell`
- `StudentTaskShell`
- `ProgressHeader`
- `CompanionPanel`
- `InstructionBubble`
- `AudioButton`
- `RecordingControl`
- `AnswerCard`
- `ImageAnswerCard`
- `SequenceBoard`
- `BuildWordBoard`
- `FeedbackState`
- `RewardScreen`
- `WaitingState`
- `ErrorState`

Pretest/Posttest/Core/Reinforcement تستخدم نفس النظام.

## 5. الشخصية

- في مهام desktop المهمة: حجم تقريبي 220–300px حسب المساحة.
- تكون في طرف الشاشة ولا تغطي السؤال.
- تعطي تعليمات سياقية: «استمع ثم اختر»، «رتب الحروف»، «اقرأ بصوت واضح».
- لا حركة مستمرة في Hero أو task view.
- الحركة القصيرة <400ms عند انتقال/نجاح فقط.

## 6. UX Writing

لا تستخدم تعليمات عامة داخل كل المهام.

أمثلة:

- «استمع إلى الصوت، ثم اختر الحرف الصحيح.»
- «رتب الحروف حتى تكوّن الكلمة.»
- «اقرأ الكلمة بصوت واضح.»
- «حاول مرة أخرى. استمع للصوت بهدوء.»
- «لم نسمع القراءة بوضوح. قرّب الجهاز وحاول مرة أخرى.»
- «أحسنت، أكملت النشاط.»
- «رائع، أنت مستعد للخطوة التالية.»

ممنوع للطفل: فشل، ضعيف، متأخر، الأسوأ، مصطلحات تقنية.

## 7. زر الخروج

في جلسة قابلة للاستئناف استخدم:

**«حفظ والخروج»**

وعند الضغط:

«حفظنا تقدمك. يمكنك العودة وإكماله لاحقًا.»

## 8. التسجيل الصوتي

حالات واجهة واضحة:

`ready → recording → recorded → preview → uploading → submitted → waiting_review`

وفشل:

- mic denied.
- upload failed.
- connection lost.
- rerecord required.

يجب ألا يفقد التسجيل المحلي فورًا إذا فشل الرفع ويمكن إعادة الإرسال بأمان.

## 9. شاشة النجاح

- شخصية نجاح.
- رسالة قصيرة.
- نتيجة/نجوم.
- حركة هادئة.
- زر «متابعة» فقط.

لا تحوّل شاشة النهاية إلى سؤال جديد.

## 10. Admin Information Architecture

Navigation مقترح:

### الرئيسية

Action Center + ملخص.

### الطلاب

- جميع الطلاب.
- إضافة طالب.

### المراجعات

- التسجيلات الصوتية.
- قرارات التقوية.

### النتائج

- الاختبارات.
- التقارير.

### إدارة المنصة

- المشرفون.
- الإعدادات.
- سجل العمليات.

## 11. Dashboard المشرف

الأولوية: «ماذا يحتاج انتباهي الآن؟»

مثال:

- تسجيلات تنتظر المراجعة.
- طالب يحتاج قرار تقوية.
- طلاب جاهزون للبعدي.
- طالب متوقف عن التقدم.
- آخر النشاطات.

بعدها تأتي KPIs والتوزيع.

## 12. ملف الطالب

لا تبقِ كل شيء في صفحة طويلة.

Header ثابت وواضح:

- الاسم.
- المستوى الحالي.
- الحالة.
- رمز الدخول + نسخ.
- progress summary.

Tabs:

1. نظرة عامة.
2. المسار والتقدم.
3. الاختبارات.
4. التسجيلات.
5. التقوية والتكيف.
6. الحساب.
7. السجل.

## 13. قرار التقوية للمشرف

في الملف: Alert مختصر:

«يحتاج هذا الطالب قرار تقوية.» [مراجعة]

ثم Drawer/Modal/Page تعرض:

- المهارة.
- evidence.
- recommendation candidates.
- سبب الاختيار.
- حفظ.

التفسير التقني الكامل يكون expandable لا يحتل أعلى الصفحة دائمًا.

## 14. Settings

قسمها إلى:

- الحساب.
- الأمان.
- المشرفون.

إعدادات الدراسة العامة تكون منطقة مستقلة مستقبلًا، وليست مختلطة بحساب المشرف.

## 15. Reports

الحالية Operating Summary فقط.

النهائية تحتاج:

- pre/post comparison.
- improvement.
- skill errors.
- levels.
- attempts/time.
- reinforcement history.
- audio review summary.
- filters.
- Excel/PDF exports.

## 16. Loading / Empty / Error

- Skeleton بدل spinner في صفحة فارغة.
- Empty state فيه معنى وCTA.
- Error بالعربية مع Retry آمن.
- Success states قصيرة وواضحة.

## 17. Responsive Gate

يجب أخذ Screenshots واختبار فعلي على الأقل:

- 390×844 mobile.
- 768×1024 tablet portrait.
- 1024×768 tablet landscape.
- 1440×900 desktop.

ولا horizontal overflow غير مقصود.

## 18. Accessibility Gate

- Touch >=44×44.
- text contrast 4.5:1 قدر الإمكان.
- focus visible.
- keyboard usable في admin.
- zoom 200% دون كسر.
- screen-reader labels للأزرار المهمة.
- لا اعتماد على اللون وحده.
- `prefers-reduced-motion`.

## 19. ترتيب التنفيذ

1. Styling foundation.
2. Student shell/UI kit.
3. Assessment templates.
4. Activity/reinforcement templates.
5. Journey transition/result screens.
6. Admin shell + IA.
7. Student profile tabs.
8. Review/settings/reports layouts.
9. Responsive/accessibility.
10. Screenshot review وإصلاح التفاصيل.

## 20. معيار القبول

لا تكفي لقطة واحدة جميلة. يجب أن تكون كل الحالات الأساسية متماسكة:

- normal.
- loading.
- empty.
- success.
- error.
- retry.
- waiting.
- mobile/tablet/desktop.
