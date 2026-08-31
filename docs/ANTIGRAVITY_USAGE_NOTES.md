# ملاحظات تشغيل Antigravity

تاريخ المراجعة: 6 أغسطس 2026.

## لماذا بنيت الحزمة بهذه الطريقة؟

- قواعد مساحة العمل في `.agents/rules/` توجه السلوك دائمًا، بينما workflows في `.agents/workflows/` برومبتات محفوظة تُشغّل عند الطلب. هذا يسمح بإبقاء القواعد الدائمة قصيرة ونقل العمليات الطويلة إلى أوامر منفصلة.
- Skills تستخدم الإفصاح التدريجي: يبقى محتواها ساكنًا ولا يُحمّل إلا عندما يطابق الطلب وصف المهارة. لذلك لا نضع 55 مهارة داخل البرومبت التأسيسي.
- Artifacts المناسبة للمراجعة هي خطة التنفيذ، قائمة المهام، walkthrough، الفروقات، الصور، وتسجيل المتصفح. نستخدمها كدليل بدل مطالبة الوكيل بسرد كل أوامر الطرفية.
- Review-driven development مناسب للجرد والمعمارية. بعد اعتماد مرحلة محددة، يعمل الوكيل ذاتيًا داخل حدودها ويرجع فقط عند بوابات القرار.

## مراجع رسمية

- [Getting Started with Antigravity IDE](https://codelabs.developers.google.com/getting-started-agy-ide)
- [Getting Started with Google Antigravity](https://codelabs.developers.google.com/getting-started-google-antigravity)
- [Spec-Driven Development in Antigravity](https://codelabs.developers.google.com/codelabs/getting-started-with-spec-driven-development-in-antigravity)
- [Autonomous pipelines with agents.md and skills.md](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity)
- [Google Developers Blog: Build with Google Antigravity](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/)

