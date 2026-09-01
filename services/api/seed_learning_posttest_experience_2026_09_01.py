"""2026-09-01 student-facing learning and posttest projection for sandbox.

This overlay preserves the academic/scoring catalog, item IDs, skills, adaptive policy,
and Student Experience v2 corrections. It stores explicit display metadata for every
Core/Reinforcement round and every Posttest question so the UI never has to expose
source-document prose or guess hints from raw prompts.
"""
from __future__ import annotations

from typing import Any

from db.database import SessionLocal
from db.models import ContentItem

LEARNING_VERSION = "HIMMA-LEARNING-2026-09-01"
POSTTEST_VERSION = "HIMMA-POSTTEST-2026-09-01"
READ = {"read_aloud", "timed_read_aloud"}
LISTEN = {"listen_choose_one", "listen_choose_image", "listen_choose_many"}

ITEM_OVERRIDES: dict[str, dict[str, str]] = {
    "L1-CORE-01":{"skill":"الانتباه والتمييز البصري","question":"ابحث عن الحرف المطلوب، ثم اضغط عليه.","instruction":"انظر إلى الحرف المطلوب، ثم اختره من الحروف المعروضة.","hint":"ركّز على شكل الحرف وعدد النقاط ومكانها."},
    "L1-CORE-02":{"skill":"ربط الصوت بالحرف","question":"استمع إلى صوت الحرف، ثم اختر الحرف الذي سمعته.","instruction":"اضغط زر الاستماع، ثم اختر الحرف المطابق للصوت.","hint":"استمع مرة أخرى، وركّز في الصوت من بدايته."},
    "L1-CORE-03":{"skill":"التعرف إلى أشكال الحرف","question":"انظر إلى الحرف، ثم اختر الشكل الآخر للحرف نفسه.","instruction":"لاحظ الحرف المعروض، ثم اختر الشكل المناسب له من الخيارات.","hint":"قارن بين الحرف المعروض والخيارات، وركّز في شكل الحرف."},
    "L1-CORE-04":{"skill":"تحديد الصوت الأول","question":"استمع إلى الصوت، ثم اختر الصورة التي يبدأ اسمها بهذا الصوت.","instruction":"اضغط زر الاستماع، ثم انظر إلى الصور واختر الصورة المناسبة.","hint":"قل أسماء الصور في ذهنك، ثم ركّز على أول صوت."},
    "L1-CORE-05":{"skill":"عزل الصوت الأخير","question":"استمع إلى الكلمة، ثم اختر الحرف الذي تسمعه في آخرها.","instruction":"اضغط زر الاستماع، ثم ركّز في نهاية الكلمة واختر آخر صوت.","hint":"استمع إلى نهاية الكلمة جيدًا قبل أن تختار."},
    "L1-CORE-06":{"skill":"التمييز السمعي بين بدايات الكلمات","question":"هل الصوت يطابق بداية الكلمة؟","instruction":"استمع إلى الصوت أولًا، ثم انظر إلى بداية الكلمة وقارن بينهما.","hint":"ركّز على أول صوت في الكلمة المعروضة وقارنه بالصوت الذي سمعته."},
    "L1-CORE-07":{"skill":"مفاهيم المادة المطبوعة","question":"هل العنصر حرف أم كلمة أم جملة؟","instruction":"انظر إلى العنصر، ثم اختر التصنيف المناسب.","hint":"الحرف رمز واحد، والكلمة لفظ واحد، والجملة تعطي معنى كاملًا."},
    "L1-CORE-08":{"skill":"الذاكرة البصرية والتسلسل","question":"تذكّر ترتيب الصور.","instruction":"شاهد الصور جيدًا، ثم اضغط «التالي» عندما تكون مستعدًا لإعادة ترتيبها.","hint":"تذكّر الصورة الأولى، ثم التي بعدها."},
    "L1-CORE-09":{"skill":"اتجاه القراءة العربية من اليمين إلى اليسار","question":"من أين نبدأ القراءة؟","instruction":"اقرأ السؤال، ثم اختر جهة القراءة الصحيحة.","hint":"في العربية نبدأ القراءة من جهة اليمين ثم نتابع نحو اليسار."},
    "L1-CORE-10":{"skill":"فهم التسلسل","question":"رتّب الصور أو الأحداث من البداية إلى النهاية.","instruction":"اضغط على ما حدث أولًا، ثم ما حدث بعده، ثم الحدث الأخير.","hint":"ابدأ بالحدث الأول، ثم أكمل التسلسل خطوة خطوة."},
    "L1-REIN-10":{"skill":"ذاكرة بصرية مخففة","question":"تذكّر ترتيب الصور.","instruction":"شاهد الصور جيدًا، ثم اضغط «التالي» عندما تكون مستعدًا لإعادة ترتيبها.","hint":"تذكّر الصورة الأولى ثم الثانية."},
    "L1-REIN-11":{"skill":"اتجاه القراءة العربية","question":"يمين أم يسار؟","instruction":"اختر جهة بداية القراءة أو اتجاهها الصحيح.","hint":"ابدأ من اليمين ثم تابع القراءة نحو اليسار."},
    "L2-CORE-01":{"skill":"تمييز الحركات القصيرة","question":"استمع إلى المقطع، ثم اختر المقطع الذي سمعته.","instruction":"اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.","hint":"ركّز على الحركة المسموعة في المقطع."},
    "L2-CORE-02":{"skill":"قراءة المقاطع","question":"اقرأ المقطع بصوت واضح.","instruction":"اضغط زر التسجيل، اقرأ المقطع المعروض، ثم أرسل التسجيل.","hint":"اقرأ الحرف مع حركته دون إضافة صوت آخر."},
    "L2-CORE-09":{"skill":"بناء كلمة من حروف","question":"ابنِ الكلمة.","instruction":"اضغط الحروف بالترتيب الصحيح حتى تكتمل الكلمة.","hint":"قل الكلمة في ذهنك، ثم ابدأ بالحرف الأول وأكمل بالترتيب."},
    "L2-CORE-10":{"skill":"قراءة جملة","question":"اقرأ الجملة بصوت واضح.","instruction":"اضغط زر التسجيل، اقرأ الجملة المعروضة، ثم أرسل التسجيل.","hint":"اقرأ الكلمات بالترتيب وبوضوح."},
    "L2-REIN-10":{"skill":"تمييز التنوين","question":"استمع إلى الكلمة، ثم اختر كتابتها بالتنوين الذي سمعته.","instruction":"اضغط زر الاستماع، ثم اختر الكتابة المطابقة.","hint":"ركّز على صوت نهاية الكلمة."},
    "L2-REIN-11":{"skill":"قراءة الجملة مع تخفيف الحمل","question":"اقرأ الجملة القصيرة بصوت واضح.","instruction":"اضغط زر التسجيل، اقرأ الجملة، ثم أرسل التسجيل.","hint":"اقرأ الكلمات ببطء ووضوح ثم صِلها في جملة واحدة."},
    "L3-CORE-01":{"skill":"قراءة الكلمات بدقة","question":"اقرأ الكلمة بصوت واضح.","instruction":"اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.","hint":"اقرأ الحروف والحركات بهدوء دون استعجال."},
    "L3-CORE-02":{"skill":"قراءة العبارات كوحدات معنى","question":"اقرأ العبارة بصوت واضح.","instruction":"اضغط زر التسجيل، اقرأ العبارة المعروضة، ثم أرسل التسجيل.","hint":"اقرأ الكلمات معًا بهدوء، ولا تفصل بينها كثيرًا."},
    "L3-CORE-03":{"skill":"قراءة الجمل","question":"اقرأ الجملة بصوت واضح.","instruction":"اضغط زر التسجيل، اقرأ الجملة كاملة، ثم أرسل التسجيل.","hint":"اقرأ الكلمات بالترتيب وحافظ على معنى الجملة."},
    "L3-CORE-10":{"skill":"فهم التسلسل وترتيب الأحداث","question":"رتّب الأحداث من البداية إلى النهاية.","instruction":"اضغط على الحدث الأول، ثم الذي بعده، ثم الحدث الأخير.","hint":"فكّر: ماذا حدث أولًا؟ ثم أكمل الأحداث بالترتيب."},
    "L3-REIN-11":{"skill":"الفهم المباشر","question":"اقرأ الجملة والسؤال، ثم اختر الإجابة الموجودة في الجملة.","instruction":"اقرأ الجملة أولًا، ثم السؤال، واختر الإجابة الصحيحة.","hint":"ابحث داخل الجملة عن الكلمة التي تجيب عن السؤال."},
    "L3-REIN-12":{"skill":"بناء الجملة وترتيب كلماتها","question":"رتّب الكلمات لتكوين جملة صحيحة.","instruction":"اضغط الكلمات بحسب ترتيبها الصحيح حتى تكتمل الجملة.","hint":"ابدأ بالفعل، ثم أكمل من قام به وما يتعلق به."},
}

POST_QUESTIONS: list[dict[str, Any]] = [
{"n":1,"skill":"تمييز الحرف بصريًا","q":"اضغط على الحرف التالي.","kind":"text","text":"ت","instruction":"انظر إلى الحروف المعروضة، ثم اختر الحرف المطلوب.","enc":"ممتاز، ابدأ بثقة!"},
{"n":2,"skill":"التمييز بين الحروف المتشابهة بصريًا","q":"اضغط على الحرف التالي.","kind":"text","text":"خ","instruction":"انظر إلى الحروف جيدًا، ثم اختر الحرف المطلوب.","enc":"رائع، أنت قادر عليها!"},
{"n":3,"skill":"التعرف إلى أشكال الحرف","q":"انظر إلى الحرف، ثم اختر الشكل الآخر للحرف نفسه.","kind":"text","text":"س","instruction":"لاحظ الحرف المعروض، ثم اختر شكله المناسب من الخيارات.","enc":"أحسنت، واصل تقدمك!"},
{"n":4,"skill":"ربط الصوت بالحرف","q":"استمع إلى صوت الحرف، ثم اختر الحرف الذي سمعته.","kind":"audio","audio":"ق","instruction":"اضغط زر الاستماع، ثم اختر الحرف المطابق للصوت.","enc":"ممتاز، ركّز في الصوت!"},
{"n":5,"skill":"تحديد الصوت الأول في الكلمة","q":"استمع إلى صوت الحرف، ثم اختر الصورة التي يبدأ اسمها بهذا الصوت.","kind":"audio","audio":"ب","instruction":"اضغط زر الاستماع، ثم انظر إلى الصور واختر الصورة المناسبة.","enc":"رائع، واصل!"},
{"n":6,"skill":"تحديد الصوت الأول في الكلمة المسموعة","q":"استمع إلى الكلمة، ثم اختر الحرف الذي تبدأ به.","kind":"audio","audio":"نَخْلَة","instruction":"اضغط زر الاستماع، ثم ركّز في أول صوت تسمعه واختر الحرف المناسب.","enc":"أحسنت، أنت تتقدم!"},
{"n":7,"skill":"تحديد الصوت الأخير في الكلمة المسموعة","q":"استمع إلى الكلمة، ثم اختر الحرف الذي تنتهي به.","kind":"audio","audio":"قَمَر","instruction":"اضغط زر الاستماع، ثم ركّز في آخر صوت تسمعه واختر الحرف المناسب.","enc":"ممتاز، استمر!"},
{"n":8,"skill":"مفاهيم المادة المطبوعة — تمييز الحرف","q":"انظر إلى العناصر، ثم اضغط على الحرف فقط.","kind":"none","instruction":"اختر العنصر الذي يمثل حرفًا واحدًا، وليس كلمة أو جملة.","enc":"رائع، اختر بهدوء!"},
{"n":9,"skill":"مفاهيم المادة المطبوعة — تمييز الكلمة","q":"انظر إلى العناصر، ثم اضغط على الكلمة فقط.","kind":"none","instruction":"اختر العنصر الذي يمثل كلمة، وليس حرفًا منفردًا أو جملة كاملة.","enc":"أحسنت، واصل!"},
{"n":10,"skill":"فهم التسلسل وترتيب الأحداث","q":"رتّب الصور بحسب ترتيب الحدث من البداية إلى النهاية.","kind":"none","instruction":"اضغط على الصورة التي حدثت أولًا، ثم الصورة التي بعدها، ثم الصورة الأخيرة.","enc":"رائع، أنت جاهز لهذه الجولة!"},
{"n":11,"skill":"تمييز الحركات القصيرة","q":"استمع إلى المقطع، ثم اختر المقطع الذي سمعته.","kind":"audio","audio":"مِ","instruction":"اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.","enc":"ممتاز، واصل تقدمك!"},
{"n":12,"skill":"التمييز بين الصوت القصير والصوت الطويل","q":"استمع إلى المقطع، ثم اختر المقطع الذي سمعته.","kind":"audio","audio":"نُو","instruction":"اضغط زر الاستماع، ثم اختر المقطع المطابق للصوت.","enc":"رائع، استمر بنفس الثقة!"},
{"n":13,"skill":"دمج المقاطع لتكوين كلمة","q":"اختر المقطعين اللذين يكوّنان الكلمة التالية.","kind":"text","text":"مَكْتَب","instruction":"اضغط على المقطع الأول، ثم اضغط على المقطع الثاني لإكمال الكلمة.","enc":"أحسنت، أنت تتقدم خطوة خطوة!"},
{"n":14,"skill":"بناء كلمة من حروف","q":"انظر إلى الصورة، ثم اضغط الحروف بالترتيب لتكوّن الكلمة.","kind":"image","text":"نَخْلَة","instruction":"ابدأ بالحرف الأول من كلمة «نَخْلَة»، ثم أكمل الحروف بالترتيب.","enc":"ممتاز، ركّز في اسم الصورة!"},
{"n":15,"skill":"ترتيب الحروف لتكوين كلمة","q":"رتّب الحروف لتكوين الكلمة التالية.","kind":"text","text":"فِيل","instruction":"اضغط على الحروف بالترتيب الصحيح حتى تكتمل الكلمة.","enc":"رائع، رتّبها بهدوء!"},
{"n":16,"skill":"إكمال الكلمة بحرف ناقص","q":"اختر الحرف الناقص لتكتمل الكلمة.","kind":"text","text":"بَـ _ ـر","instruction":"اقرأ ما قبل الفراغ وما بعده، ثم اختر الحرف المناسب.","enc":"أحسنت، ركّز في شكل الكلمة!"},
{"n":17,"skill":"ربط الكلمة المكتوبة بالصورة","q":"اقرأ الكلمة، ثم اختر الصورة المطابقة لها.","kind":"text","text":"قَمَر","instruction":"انظر إلى الكلمة جيدًا، ثم اختر الصورة التي تدل عليها.","enc":"ممتاز، واصل!"},
{"n":18,"skill":"مطابقة الكلمة المسموعة بالكلمة المكتوبة","q":"استمع إلى الكلمة، ثم اختر الكلمة التي سمعتها.","kind":"audio","audio":"سُوق","instruction":"اضغط زر الاستماع، ثم اختر الكلمة المطابقة للصوت.","enc":"رائع، أنت تقوم بعمل جميل!"},
{"n":19,"skill":"قراءة كلمة","q":"اقرأ الكلمة بصوت واضح.","kind":"reading","text":"رَسَمَ","instruction":"اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.","enc":"ممتاز، اقرأ بثقة!"},
{"n":20,"skill":"قراءة كلمة تحتوي على سكون","q":"اقرأ الكلمة بصوت واضح.","kind":"reading","text":"نَجْم","instruction":"اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.","enc":"رائع، واصل تقدمك!"},
{"n":21,"skill":"قراءة كلمة تحتوي على مد","q":"اقرأ الكلمة بصوت واضح.","kind":"reading","text":"نُور","instruction":"اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.","enc":"أحسنت، أنت تتقدم!"},
{"n":22,"skill":"قراءة كلمة تحتوي على شدة","q":"اقرأ الكلمة بصوت واضح.","kind":"reading","text":"سُلَّم","instruction":"اضغط زر التسجيل، اقرأ الكلمة المعروضة، ثم أرسل التسجيل.","enc":"ممتاز، اقرأ كما تراها!"},
{"n":23,"skill":"قراءة جملة قصيرة","q":"اقرأ الجملة بصوت واضح.","kind":"reading","text":"تَلْعَبُ مَرْيَمُ بِالْكُرَةِ.","instruction":"اضغط زر التسجيل، اقرأ الجملة كاملة، ثم أرسل التسجيل.","enc":"رائع، اقرأ الكلمات بالترتيب!"},
{"n":24,"skill":"قراءة نص قصير وقياس الطلاقة","q":"اقرأ النص كاملًا بصوت واضح.","kind":"reading","text":"فِي صَبَاحٍ مُشْمِسٍ، ذَهَبَ مَاجِدٌ مَعَ وَالِدِهِ إِلَى الشَّاطِئِ. أَخَذَ دَلْوًا صَغِيرًا، وَحَمَلَ وَالِدُهُ مَاءً وَمِظَلَّةً. بَنَى مَاجِدٌ بَيْتًا مِنَ الرَّمْلِ، ثُمَّ جَمَعَ أَصْدَافًا مُلَوَّنَةً. قَبْلَ الْعَوْدَةِ، نَظَّفَا مَكَانَهُمَا.","instruction":"اضغط زر التسجيل، اقرأ النص كاملًا، ثم أرسل التسجيل.","enc":"اقرأ بهدوء، وحاول أن تكون قراءتك واضحة."},
{"n":25,"skill":"فهم معلومة مباشرة من النص","q":"إلى أين ذهب ماجد؟","kind":"reference","instruction":"اقرأ السؤال، ثم اختر الإجابة الصحيحة من الخيارات.","enc":"ممتاز، ابحث في بداية النص!"},
{"n":26,"skill":"فهم معلومة مباشرة من النص","q":"مع من ذهب ماجد؟","kind":"reference","instruction":"اقرأ السؤال، ثم اختر الإجابة الصحيحة من الخيارات.","enc":"رائع، واصل تقدمك!"},
{"n":27,"skill":"فهم معلومة مباشرة من النص","q":"ماذا بنى ماجد؟","kind":"reference","instruction":"اقرأ السؤال، ثم اختر الإجابة الصحيحة من الخيارات.","enc":"أحسنت، أنت قريب من النهاية!"},
{"n":28,"skill":"فهم استنتاجي من النص","q":"لماذا نظف ماجد ووالده المكان؟","kind":"reference","instruction":"فكّر في سبب هذا التصرف، ثم اختر الإجابة الأنسب.","enc":"ممتاز، فكّر بثقة!"},
{"n":29,"skill":"ترتيب أحداث من نص مقروء","q":"رتّب الأحداث بحسب ترتيبها في القصة.","kind":"reference","instruction":"اضغط على الحدث الذي حدث أولًا، ثم الذي بعده، ثم الحدث الأخير.","enc":"رائع، تذكّر تسلسل القصة!"},
{"n":30,"skill":"فهم معنى كلمة من السياق","q":"ما معنى كلمة «مُلَوَّنَة»؟","kind":"text","text":"أَصْدَافًا مُلَوَّنَةً","instruction":"اقرأ العبارة، ثم اختر معنى الكلمة من الخيارات.","enc":"أحسنت، أكمل السؤال الأخير بثقة!"},
]

def canonical(item: ContentItem) -> str:
    return str((item.template_data or {}).get("canonical_id") or item.stable_key)

def encouragement(index: int, total: int) -> str:
    if total >= 8:
        if index == 1: return "ممتاز، ابدأ بثقة!"
        if index == 2: return "رائع، واصل!"
        if index == 3: return "أحسنت، تقدم جميل!"
        if index == total: return "رائع، أكملها بقوة!"
        if index == total - 1: return "ممتاز، أنت قريب جدًا!"
        if index >= total - 2: return "رائع، بقي القليل!"
        return "ممتاز، واصل بنفس الثقة!"
    phrases = ["ممتاز، أنت جاهز لهذه الجولة!","رائع، واصل تقدمك!","أحسنت، أنت تتقدم بشكل جميل!","ممتاز، بقي القليل!","رائع، أكمل الجولة الأخيرة بثقة!"]
    if total <= 1: return "ممتاز، أنت قادر عليها!"
    pos = round((index - 1) * 4 / max(1, total - 1))
    return phrases[max(0, min(4, pos))]

def generic_question(interaction: str, instruction: str, prompt: str) -> str:
    text = (instruction or "").strip()
    if text.startswith("التعليمات:"): text = text.split(":", 1)[1].strip()
    if text: return text
    if interaction in LISTEN: return "استمع جيدًا، ثم اختر الإجابة المناسبة."
    if interaction in READ: return "اقرأ النص المعروض بصوت واضح."
    if interaction == "memory_sequence": return "تذكّر ترتيب الصور."
    if interaction in {"sequence", "build_word"}: return "رتّب العناصر بالترتيب الصحيح."
    return (prompt or "اختر الإجابة المناسبة.").strip()

def generic_instruction(interaction: str, question: str) -> str:
    if interaction in LISTEN: return "اضغط زر الاستماع، ثم اختر الإجابة المطابقة."
    if interaction in READ: return "اضغط زر التسجيل، اقرأ النص المعروض، ثم أرسل التسجيل."
    if interaction == "memory_sequence": return "شاهد الصور جيدًا، ثم اضغط «التالي» عندما تكون مستعدًا لإعادة ترتيبها."
    if interaction == "sequence": return "اضغط العناصر بحسب ترتيبها الصحيح."
    if interaction == "build_word": return "اضغط الحروف أو المقاطع بالترتيب حتى تكتمل الكلمة."
    return question

def generic_hint(interaction: str, question: str) -> str:
    if interaction == "memory_sequence": return "تذكّر الصورة الأولى، ثم التي بعدها."
    if interaction == "sequence": return "ابدأ بما حدث أولًا، ثم أكمل الترتيب خطوة خطوة."
    if interaction == "build_word": return "ابدأ بالحرف أو المقطع الذي تبدأ به الكلمة."
    if interaction in READ: return "اقرأ ببطء ووضوح، وركّز في الحروف والحركات."
    if interaction in LISTEN:
        return "استمع مرة أخرى، وركّز على آخر صوت." if ("آخر" in question or "نهاية" in question) else "استمع مرة أخرى، وركّز في الصوت المطلوب."
    if "حرف" in question: return "ركّز في شكل الحرف ونقاطه."
    if "نص" in question or "سؤال" in question: return "ارجع إلى النص وابحث عن الجزء الذي يساعدك على الإجابة."
    return "اقرأ المطلوب بهدوء، ثم جرّب من جديد."

def learning_round(item: ContentItem, step, total: int) -> dict[str, Any]:
    key = canonical(item)
    override = ITEM_OVERRIDES.get(key, {})
    interaction = str((item.template_data or {}).get("canonical_interaction_type") or item.interaction_type)
    raw_instruction = str(step.instruction_text or "")
    raw_prompt = str(step.prompt_text or "")
    question = override.get("question") or generic_question(interaction, raw_instruction, raw_prompt)
    instruction = override.get("instruction") or generic_instruction(interaction, question)
    return {"round_number":int(step.order_index),"round_total":total,"skill":override.get("skill") or str((item.template_data or {}).get("title") or item.title or "مهارة تعليمية"),"encouragement":encouragement(int(step.order_index), total),"hint":override.get("hint") or generic_hint(interaction, question),"question_text":question,"instruction_text":instruction}

def apply_learning(db) -> int:
    items = db.query(ContentItem).filter(ContentItem.kind.in_(["core_activity", "reinforcement_activity"])).all()
    if len(items) != 65: raise RuntimeError(f"Expected 65 learning items, got {len(items)}")
    changed = 0
    for item in items:
        steps = sorted(item.steps, key=lambda step: step.order_index)
        if not steps: raise RuntimeError(f"{canonical(item)} has no rounds")
        data = dict(item.template_data or {})
        projected = dict(data)
        projected["learning_experience_version"] = LEARNING_VERSION
        projected["learning_experience"] = {"version":LEARNING_VERSION,"rounds":[learning_round(item, step, len(steps)) for step in steps]}
        if projected != data: item.template_data = projected; changed += 1
    return changed

def post_stimulus(spec: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"kind":str(spec.get("kind") or "none")}
    if spec.get("text"): result["text"] = str(spec["text"])
    if spec.get("audio"): result["audio_target"] = str(spec["audio"])
    return result

def apply_posttest(db) -> int:
    items = db.query(ContentItem).filter(ContentItem.kind == "posttest_question").all()
    if len(items) != 30: raise RuntimeError(f"Expected 30 posttest items, got {len(items)}")
    by_key = {canonical(item): item for item in items}
    changed = 0
    for spec in POST_QUESTIONS:
        key = f"POST-Q{spec['n']:02d}"
        item = by_key.get(key)
        if item is None: raise RuntimeError(f"Missing posttest item {key}")
        data = dict(item.template_data or {})
        projected = dict(data)
        projected["posttest_experience_version"] = POSTTEST_VERSION
        projected["posttest_experience"] = {"version":POSTTEST_VERSION,"question_number":int(spec["n"]),"section":"الاستعداد للقراءة" if spec["n"] <= 10 else ("بناء الكلمة وقراءتها" if spec["n"] <= 22 else "الطلاقة والفهم"),"skill":str(spec["skill"]),"encouragement":str(spec["enc"]),"question_text":str(spec["q"]),"instruction_text":str(spec["instruction"]),"stimulus":post_stimulus(spec),"interaction_type":str(data.get("canonical_interaction_type") or item.interaction_type)}
        if projected != data: item.template_data = projected; changed += 1
    return changed

def run_seed() -> dict[str, int]:
    db = SessionLocal()
    try:
        learning_changed = apply_learning(db)
        posttest_changed = apply_posttest(db)
        db.commit()
        return {"learning_items":65,"learning_changed":learning_changed,"posttest_items":30,"posttest_changed":posttest_changed}
    except Exception:
        db.rollback(); raise
    finally:
        db.close()

if __name__ == "__main__":
    print(f"Learning/posttest experience overlay OK: {run_seed()}")
