"use client";

import { useEffect, useState } from "react";

type Screen =
  | "welcome"
  | "student-login"
  | "student-home"
  | "pretest"
  | "activity"
  | "record"
  | "success"
  | "researcher-login"
  | "researcher-dashboard";

function Icon({ name, alt = "" }: { name: string; alt?: string }) {
  return <img className="ui-icon" src={`/himma/icons/${name}.svg`} alt={alt} />;
}

function BrandHeader({
  onHome,
  studentName,
}: {
  onHome: () => void;
  studentName?: string;
}) {
  return (
    <header className="brand-header">
      <button className="brand-button" type="button" onClick={onHome} aria-label="العودة إلى الصفحة الرئيسية">
        <img src="/himma/logo.svg" alt="هِمّة — أتعلم، أتطور، أصل إلى القمة" />
      </button>

      <div className="header-actions">
        {studentName ? (
          <div className="student-pill" aria-label={`الطالب ${studentName}`}>
            <span className="student-avatar">س</span>
            <span>
              <small>مرحبًا</small>
              <strong>{studentName}</strong>
            </span>
          </div>
        ) : (
          <span className="prototype-label">نموذج تفاعلي</span>
        )}
      </div>
    </header>
  );
}

function WelcomeScreen({
  onStudentLogin,
  onResearcherLogin,
}: {
  onStudentLogin: () => void;
  onResearcherLogin: () => void;
}) {
  return (
    <main className="page-shell welcome-page">
      <BrandHeader onHome={() => undefined} />

      <section className="welcome-grid">
        <div className="welcome-copy">
          <span className="eyebrow">
            <span className="eyebrow-dot" />
            رحلة قراءة تناسب كل طالب
          </span>
          <h1>
            نتعلّم بهدوء،
            <span>ونتقدّم بثقة.</span>
          </h1>
          <p className="welcome-lead">
            أنشطة قصيرة وممتعة تساعدك على القراءة خطوةً خطوة، وتختار لك هِمّة ما يناسب تقدّمك.
          </p>

          <div className="welcome-actions">
            <button className="primary-button large-button" type="button" onClick={onStudentLogin}>
              <Icon name="student" />
              دخول الطالب
              <span className="button-arrow" aria-hidden="true">←</span>
            </button>
            <button className="researcher-link" type="button" onClick={onResearcherLogin}>
              <Icon name="researcher" />
              دخول الباحثة
            </button>
          </div>

          <div className="trust-row" aria-label="مزايا المنصة">
            <span><Icon name="success" /> واضحة وسهلة</span>
            <span><Icon name="progress" /> تتدرّج معك</span>
            <span><Icon name="star" /> تشجيع في كل خطوة</span>
          </div>
        </div>

        <div className="welcome-visual" aria-label="شخصيتا هِمّة ترحبان بالطالب">
          <div className="visual-orbit orbit-one" />
          <div className="visual-orbit orbit-two" />
          <div className="welcome-bubble bubble-one">أهلًا بك 👋</div>
          <div className="welcome-bubble bubble-two">جاهز نبدأ؟</div>
          <img className="welcome-character boy" src="/himma/characters/boy-welcome.webp" alt="شخصية ولد من هِمّة يرحب بالطالب" />
          <img className="welcome-character girl" src="/himma/characters/girl-welcome.webp" alt="شخصية بنت من هِمّة ترحب بالطالب" />
          <div className="visual-floor" />
        </div>
      </section>
    </main>
  );
}

function StudentLoginScreen({
  onBack,
  onLogin,
}: {
  onBack: () => void;
  onLogin: () => void;
}) {
  const [studentCode, setStudentCode] = useState("هـم-٢٠٤٨");

  return (
    <main className="page-shell login-page">
      <BrandHeader onHome={onBack} />

      <section className="login-layout">
        <div className="login-card">
          <button className="back-button" type="button" onClick={onBack}>
            <span aria-hidden="true">→</span>
            رجوع
          </button>
          <span className="mini-mark"><img src="/himma/mark.svg" alt="" /></span>
          <p className="section-kicker">دخول الطالب</p>
          <h1>اكتب رمزك لنبدأ</h1>
          <p className="login-copy">ستجد الرمز في البطاقة التي أعطتك إياها الباحثة.</p>

          <label className="code-label" htmlFor="student-code">رمز الطالب</label>
          <input
            id="student-code"
            className="code-input"
            value={studentCode}
            onChange={(event) => setStudentCode(event.target.value)}
            inputMode="text"
            autoComplete="off"
            aria-describedby="code-help"
          />
          <p id="code-help" className="field-help"><Icon name="success" /> لن نطلب منك بريدًا أو كلمة مرور.</p>

          <button className="primary-button login-button" type="button" onClick={onLogin} disabled={!studentCode.trim()}>
            دخول
            <span className="button-arrow" aria-hidden="true">←</span>
          </button>
        </div>

        <aside className="login-companion" aria-label="مساعدة مرئية">
          <div className="companion-message">
            <strong>أنا معك يا بطل</strong>
            <span>كل خطوة قصيرة وواضحة.</span>
          </div>
          <img src="/himma/characters/boy-explain.webp" alt="شخصية هِمّة تشرح طريقة الدخول" />
        </aside>
      </section>
    </main>
  );
}

function ProgressPath() {
  const levels = [
    { number: "١", title: "الاستعداد للقراءة", icon: "readiness", state: "current" },
    { number: "٢", title: "بناء الكلمة", icon: "word-building", state: "locked" },
    { number: "٣", title: "الطلاقة والفهم", icon: "fluency", state: "locked" },
  ];

  return (
    <div className="progress-path" aria-label="مراحل التعلم الثلاث">
      {levels.map((level, index) => (
        <div className={`level-step ${level.state}`} key={level.number}>
          <div className="level-icon-wrap">
            <img src={`/himma/levels/${level.icon}.svg`} alt="" />
            <span className="level-number">{level.number}</span>
          </div>
          <span className="level-title">{level.title}</span>
          <small>{index === 0 ? "نبدأ من هنا" : "تفتح مع تقدّمك"}</small>
        </div>
      ))}
    </div>
  );
}

function StudentHomeScreen({
  onHome,
  onStart,
}: {
  onHome: () => void;
  onStart: () => void;
}) {
  return (
    <main className="page-shell student-home-page">
      <BrandHeader onHome={onHome} studentName="سالم" />

      <section className="student-home-grid">
        <div className="student-main-column">
          <div className="greeting-row">
            <div>
              <span className="eyebrow compact"><span className="eyebrow-dot" /> صباح التقدّم</span>
              <h1>مرحبًا يا سالم 👋</h1>
              <p>خطوتك الأولى جاهزة. خذ وقتك، وسنحفظ تقدّمك تلقائيًا.</p>
            </div>
            <div className="day-streak" aria-label="سلسلة التقدم يومان">
              <Icon name="star" />
              <span><strong>يومان</strong><small>من التقدّم</small></span>
            </div>
          </div>

          <article className="current-task-card">
            <div className="task-content">
              <span className="task-badge"><Icon name="pretest" /> خطوتك الحالية</span>
              <h2>الاختبار القبلي</h2>
              <p>أسئلة قصيرة تساعد هِمّة على اختيار البداية المناسبة لك.</p>
              <div className="task-meta">
                <span><strong>٣٠</strong> سؤالًا</span>
                <i />
                <span><strong>١٥</strong> دقيقة تقريبًا</span>
                <i />
                <span>حفظ تلقائي</span>
              </div>
              <button className="primary-button task-button" type="button" onClick={onStart}>
                ابدأ الاختبار
                <span className="button-arrow" aria-hidden="true">←</span>
              </button>
            </div>
            <div className="task-character">
              <span className="character-note">سنأخذها سؤالًا سؤالًا</span>
              <img src="/himma/characters/girl-explain.webp" alt="شخصية هِمّة تشرح الخطوة الحالية" />
            </div>
          </article>

          <section className="journey-card">
            <div className="section-heading-row">
              <div>
                <p className="section-kicker">رحلتك في هِمّة</p>
                <h2>ثلاث خطوات تصعد بك</h2>
              </div>
              <span className="safe-progress">نبدأ من مستواك المناسب</span>
            </div>
            <ProgressPath />
          </section>
        </div>

        <aside className="student-side-column">
          <article className="calm-tip-card">
            <span className="tip-icon">🎧</span>
            <div>
              <p className="section-kicker">قبل أن تبدأ</p>
              <h3>اختر مكانًا هادئًا</h3>
              <p>بعض الأسئلة تحتاج إلى الاستماع أو تسجيل القراءة.</p>
            </div>
          </article>
          <article className="progress-summary-card">
            <div className="summary-ring" aria-label="التقدم صفر بالمئة"><span>٠٪</span></div>
            <div>
              <p>تقدّم اليوم</p>
              <strong>البداية الآن</strong>
              <small>كل نشاط مكتمل يضيف خطوة.</small>
            </div>
          </article>
          <button className="quiet-link" type="button" onClick={onHome}>تسجيل الخروج</button>
        </aside>
      </section>
    </main>
  );
}

function LearningHeader({
  label,
  current,
  total,
  onExit,
}: {
  label: string;
  current: number;
  total: number;
  onExit: () => void;
}) {
  const progress = Math.max(0, Math.min(100, (current / total) * 100));

  return (
    <header className="learning-header">
      <button className="brand-button learning-logo" type="button" onClick={onExit} aria-label="العودة إلى لوحة الطالب">
        <img src="/himma/logo.svg" alt="هِمّة" />
      </button>
      <div className="learning-progress-wrap">
        <div className="learning-progress-copy">
          <span>{label}</span>
          <strong>{current} من {total}</strong>
        </div>
        <div className="learning-progress-track" aria-label={`التقدم ${Math.round(progress)} بالمئة`}>
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>
      <button className="exit-session-button" type="button" onClick={onExit}>خروج</button>
    </header>
  );
}

function PretestScreen({
  onExit,
  onContinue,
}: {
  onExit: () => void;
  onContinue: () => void;
}) {
  const [selectedLetter, setSelectedLetter] = useState<string | null>(null);

  return (
    <main className="learning-page">
      <LearningHeader label="الاختبار القبلي" current={1} total={30} onExit={onExit} />
      <section className="learning-stage">
        <aside className="instruction-companion">
          <div className="companion-copy">
            <span className="small-blue-label">السؤال الأول</span>
            <strong>خذ وقتك يا سالم</strong>
            <p>اختر إجابة واحدة، وسنحفظها مباشرة.</p>
          </div>
          <img src="/himma/characters/boy-encourage.webp" alt="شخصية هِمّة تشجع الطالب" />
        </aside>

        <article className="question-card">
          <div className="question-topline">
            <span className="question-type"><Icon name="pretest" /> تمييز الحروف</span>
            <button className="audio-help-button" type="button" aria-label="تشغيل التعليمة الصوتية">
              <Icon name="play-audio" />
              استمع للتعليمة
            </button>
          </div>
          <div className="question-prompt">
            <span>اضغط على الحرف</span>
            <strong>ب</strong>
          </div>
          <div className="letter-options" role="radiogroup" aria-label="اختر الحرف المطلوب">
            {["ت", "ب", "ث", "ن"].map((letter) => (
              <button
                key={letter}
                className={`letter-option ${selectedLetter === letter ? "selected" : ""}`}
                type="button"
                role="radio"
                aria-checked={selectedLetter === letter}
                onClick={() => setSelectedLetter(letter)}
              >
                {letter}
              </button>
            ))}
          </div>
          <div className="question-footer">
            <span className={`autosave-note ${selectedLetter ? "saved" : ""}`}>
              <Icon name={selectedLetter ? "success" : "progress"} />
              {selectedLetter ? "تم حفظ إجابتك" : "اختر إجابة للمتابعة"}
            </span>
            <button className="primary-button continue-button" type="button" disabled={!selectedLetter} onClick={onContinue}>
              السؤال التالي
              <span className="button-arrow" aria-hidden="true">←</span>
            </button>
          </div>
        </article>
      </section>
    </main>
  );
}

function ActivityScreen({
  onExit,
  onContinue,
}: {
  onExit: () => void;
  onContinue: () => void;
}) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const correct = selectedImage === "banana";
  const choices = [
    { id: "banana", label: "موزة", src: "/himma/vocabulary/banana.webp" },
    { id: "book", label: "كتاب", src: "/himma/vocabulary/book.webp" },
    { id: "door", label: "باب", src: "/himma/vocabulary/door.webp" },
  ];

  const playAudio = () => {
    setAudioPlaying(true);
    window.setTimeout(() => setAudioPlaying(false), 1200);
  };

  return (
    <main className="learning-page activity-page">
      <LearningHeader label="نشاط: الصوت الأول" current={4} total={10} onExit={onExit} />
      <section className="activity-stage">
        <article className="activity-card">
          <div className="activity-intro">
            <span className="task-badge"><Icon name="listen" /> الاستعداد للقراءة</span>
            <h1>استمع، ثم اختر الصورة</h1>
            <p>ما الصورة التي تبدأ بصوت <strong>«م»</strong>؟</p>
          </div>

          <button className={`sound-orb ${audioPlaying ? "playing" : ""}`} type="button" onClick={playAudio} aria-label="تشغيل صوت الحرف م">
            <span className="sound-ring ring-a" />
            <span className="sound-ring ring-b" />
            <Icon name="play-audio" />
            <strong>{audioPlaying ? "مـ..." : "استمع"}</strong>
          </button>

          <div className="image-choices" role="radiogroup" aria-label="اختر الصورة التي تبدأ بصوت م">
            {choices.map((choice) => {
              const isSelected = selectedImage === choice.id;
              const stateClass = !isSelected ? "" : choice.id === "banana" ? "correct" : "try-again";
              return (
                <button
                  className={`image-choice ${stateClass}`}
                  key={choice.id}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  onClick={() => setSelectedImage(choice.id)}
                >
                  <span className="choice-image-wrap"><img src={choice.src} alt={choice.label} /></span>
                  <strong>{choice.label}</strong>
                  {isSelected && <span className="choice-state"><Icon name={correct ? "success" : "retry"} /></span>}
                </button>
              );
            })}
          </div>

          <div className={`activity-feedback ${selectedImage ? "visible" : ""} ${correct ? "positive" : "gentle"}`}>
            <Icon name={correct ? "success" : "retry"} />
            <div>
              <strong>{correct ? "أحسنت، «موزة» تبدأ بصوت م" : "قريب جدًا، استمع إلى الصوت مرة أخرى"}</strong>
              <span>{correct ? "تقدّمت خطوة في تمييز الأصوات." : "يمكنك المحاولة من جديد بهدوء."}</span>
            </div>
            <button className="primary-button" type="button" disabled={!correct} onClick={onContinue}>
              {correct ? "انتقل إلى القراءة" : "اختر مرة أخرى"}
              {correct && <span className="button-arrow" aria-hidden="true">←</span>}
            </button>
          </div>
        </article>
      </section>
    </main>
  );
}

type RecordingState = "ready" | "recording" | "analyzing" | "complete";

function RecordScreen({
  onExit,
  onComplete,
}: {
  onExit: () => void;
  onComplete: () => void;
}) {
  const [recordingState, setRecordingState] = useState<RecordingState>("ready");
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (recordingState !== "recording") return;
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [recordingState]);

  const startRecording = () => {
    setSeconds(0);
    setRecordingState("recording");
  };

  const stopRecording = () => {
    setRecordingState("analyzing");
    window.setTimeout(() => setRecordingState("complete"), 1800);
  };

  return (
    <main className="learning-page record-page">
      <LearningHeader label="نشاط: قراءة كلمة" current={7} total={10} onExit={onExit} />
      <section className="record-stage">
        <article className="record-card">
          <div className="record-copy">
            <span className="task-badge"><Icon name="read" /> قراءة بصوت واضح</span>
            <h1>اقرأ الكلمة الآتية</h1>
            <p>اضغط زر التسجيل، ثم اقرأ بهدوء.</p>
          </div>

          <div className="reading-word" aria-label="الكلمة المطلوب قراءتها">قِطَّةٌ</div>

          <div className={`recorder-panel state-${recordingState}`}>
            <div className="waveform" aria-hidden="true">
              {Array.from({ length: 25 }).map((_, index) => <span key={index} style={{ animationDelay: `${index * 34}ms` }} />)}
            </div>

            {recordingState === "ready" && (
              <>
                <button className="record-button" type="button" onClick={startRecording}>
                  <span className="mic-circle"><Icon name="record" /></span>
                  <strong>ابدأ التسجيل</strong>
                </button>
                <small>التسجيل تجريبي في نموذج الواجهة</small>
              </>
            )}

            {recordingState === "recording" && (
              <>
                <div className="recording-status"><span className="live-dot" /> جارٍ التسجيل <strong>00:{String(seconds).padStart(2, "0")}</strong></div>
                <button className="stop-record-button" type="button" onClick={stopRecording}>إنهاء التسجيل</button>
              </>
            )}

            {recordingState === "analyzing" && (
              <div className="analysis-state">
                <span className="analysis-spinner" />
                <strong>جاري تحليل القراءة…</strong>
                <small>لا تغلق الصفحة.</small>
              </div>
            )}

            {recordingState === "complete" && (
              <div className="record-complete-state">
                <span className="complete-check"><Icon name="success" /></span>
                <div><strong>وصلتنا قراءتك بوضوح</strong><small>أصبحت النتيجة جاهزة.</small></div>
                <button className="primary-button" type="button" onClick={onComplete}>شاهد النتيجة <span className="button-arrow" aria-hidden="true">←</span></button>
              </div>
            )}
          </div>
        </article>

        <aside className="record-companion">
          <span className="record-tip">قرّب الجهاز وتكلم بصوتك الطبيعي</span>
          <img src="/himma/characters/girl-explain.webp" alt="شخصية هِمّة تشرح طريقة التسجيل" />
        </aside>
      </section>
    </main>
  );
}

function SuccessScreen({
  onStudentHome,
  onResearcher,
}: {
  onStudentHome: () => void;
  onResearcher: () => void;
}) {
  return (
    <main className="result-page">
      <button className="result-logo" type="button" onClick={onStudentHome} aria-label="العودة إلى لوحة الطالب">
        <img src="/himma/logo.svg" alt="هِمّة" />
      </button>
      <section className="result-card">
        <div className="confetti-dot dot-a" />
        <div className="confetti-dot dot-b" />
        <div className="confetti-dot dot-c" />
        <div className="result-art">
          <img className="result-stars" src="/himma/rewards/stars-three.svg" alt="ثلاث نجوم" />
          <img className="result-character" src="/himma/characters/girl-success.webp" alt="شخصية هِمّة تحتفل بنجاح الطالب" />
        </div>
        <div className="result-copy">
          <span className="success-label"><Icon name="success" /> اكتمل النشاط</span>
          <h1>أحسنت يا سالم!</h1>
          <p>قرأت الكلمة بوضوح، وتقدّمت خطوة جميلة في مسارك.</p>
          <div className="earned-row">
            <div><span>⭐</span><strong>٣ نجوم</strong><small>مكافأة النشاط</small></div>
            <i />
            <div><span>↗</span><strong>خطوة جديدة</strong><small>في الاستعداد للقراءة</small></div>
          </div>
          <button className="primary-button result-continue" type="button" onClick={onStudentHome}>متابعة رحلتي <span className="button-arrow" aria-hidden="true">←</span></button>
          <button className="researcher-preview-link" type="button" onClick={onResearcher}>معاينة لوحة الباحثة في النموذج</button>
        </div>
      </section>
    </main>
  );
}

function ResearcherLoginScreen({
  onBack,
  onLogin,
}: {
  onBack: () => void;
  onLogin: () => void;
}) {
  return (
    <main className="researcher-login-page">
      <section className="researcher-login-brand">
        <button className="brand-button" type="button" onClick={onBack}><img src="/himma/logo.svg" alt="هِمّة" /></button>
        <div>
          <span className="researcher-secure-label"><Icon name="success" /> دخول آمن للباحثة</span>
          <h1>بيانات الدراسة واضحة،<br />وقراراتك موثّقة.</h1>
          <p>تابعي الطلاب والتسجيلات والتقدّم من لوحة واحدة منظّمة.</p>
        </div>
        <div className="researcher-login-features">
          <span><Icon name="student" /> ملفات الطلاب</span>
          <span><Icon name="record" /> مراجعة التسجيلات</span>
          <span><Icon name="reports" /> التقارير والتصدير</span>
        </div>
      </section>

      <section className="researcher-login-form-wrap">
        <div className="researcher-login-card">
          <button className="back-button" type="button" onClick={onBack}><span>→</span> عودة</button>
          <span className="researcher-card-icon"><Icon name="researcher" /></span>
          <p className="section-kicker">لوحة الباحثة</p>
          <h2>تسجيل الدخول</h2>
          <p>استخدمي بيانات الحساب المخصص للدراسة.</p>
          <label htmlFor="researcher-email">البريد الإلكتروني</label>
          <input id="researcher-email" type="email" defaultValue="researcher@himma.om" />
          <label htmlFor="researcher-password">كلمة المرور</label>
          <input id="researcher-password" type="password" defaultValue="himma-demo" />
          <button className="primary-button researcher-login-button" type="button" onClick={onLogin}>دخول اللوحة <span className="button-arrow">←</span></button>
          <small className="demo-data-note"><Icon name="warning" /> هذه بيانات عرض تجريبية وليست حسابًا حقيقيًا.</small>
        </div>
      </section>
    </main>
  );
}

const researchStudents = [
  { code: "هـم-٢٠٤٨", name: "سالم", level: "بناء الكلمة", pre: "٦٤٪", current: "٨١٪", status: "نشط", statusClass: "active" },
  { code: "هـم-١٧٣٢", name: "مريم", level: "الطلاقة والفهم", pre: "٨٢٪", current: "٨٩٪", status: "نشط", statusClass: "active" },
  { code: "هـم-٣١٩٠", name: "ماجد", level: "الاستعداد للقراءة", pre: "٤٢٪", current: "٥٨٪", status: "دعم إضافي", statusClass: "support" },
  { code: "هـم-٢٦٥١", name: "هند", level: "بناء الكلمة", pre: "٦٩٪", current: "٨٤٪", status: "مؤهلة للبعدي", statusClass: "ready" },
];

function MetricCard({ icon, label, value, note, tone }: { icon: string; label: string; value: string; note: string; tone: string }) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <span className="metric-icon"><Icon name={icon} /></span>
      <div><p>{label}</p><strong>{value}</strong><small>{note}</small></div>
    </article>
  );
}

function ResearcherDashboard({ onExit }: { onExit: () => void }) {
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 2200);
  };

  return (
    <main className="researcher-dashboard" dir="rtl">
      <aside className="researcher-sidebar">
        <img className="sidebar-logo" src="/himma/logo.svg" alt="هِمّة" />
        <nav aria-label="تنقل لوحة الباحثة">
          <button className="active" type="button"><Icon name="home" /> نظرة عامة</button>
          <button type="button"><Icon name="student" /> الطلاب <span>١٥</span></button>
          <button type="button"><Icon name="activity" /> الأنشطة</button>
          <button type="button"><Icon name="pretest" /> الاختبارات</button>
          <button type="button"><Icon name="record" /> مراجعة الصوت <span className="alert-count">٣</span></button>
          <button type="button"><Icon name="reports" /> التقارير</button>
        </nav>
        <div className="sidebar-bottom">
          <button type="button"><Icon name="settings" /> الإعدادات</button>
          <button type="button" onClick={onExit}>تسجيل الخروج</button>
        </div>
      </aside>

      <section className="researcher-content">
        <header className="dashboard-header">
          <div>
            <span className="demo-dataset-label">بيانات تجريبية للنموذج</span>
            <h1>نظرة عامة على الدراسة</h1>
            <p>الخميس، ٦ أغسطس ٢٠٢٦ · آخر تحديث منذ دقيقتين</p>
          </div>
          <div className="dashboard-header-actions">
            <button type="button" onClick={() => showToast("سيُجهّز ملف PDF عند ربط بيانات الدراسة.")}><Icon name="export-pdf" /> PDF</button>
            <button className="export-main" type="button" onClick={() => showToast("سيُجهّز ملف Excel عند ربط بيانات الدراسة.")}><Icon name="export-spreadsheet" /> تصدير Excel</button>
          </div>
        </header>

        <section className="metrics-grid" aria-label="ملخص الدراسة">
          <MetricCard icon="student" label="إجمالي الطلاب" value="١٥" note="جميع أفراد العينة" tone="blue" />
          <MetricCard icon="activity" label="طلاب نشطون" value="١١" note="أكملوا نشاطًا هذا الأسبوع" tone="green" />
          <MetricCard icon="record" label="تحتاج مراجعة" value="٣" note="تسجيلات منخفضة الثقة" tone="yellow" />
          <MetricCard icon="success" label="مكتملون" value="١" note="أنهى الاختبار البعدي" tone="navy" />
        </section>

        <section className="dashboard-insights-grid">
          <article className="improvement-card">
            <div className="panel-heading">
              <div><span>مؤشر التحسن</span><h2>متوسط أداء العينة</h2></div>
              <span className="positive-chip">+١٨٫٤٪</span>
            </div>
            <div className="score-comparison">
              <div><span>الاختبار القبلي</span><strong>٥٨٫٢٪</strong><i style={{ width: "58.2%" }} /></div>
              <div><span>الأداء الحالي</span><strong>٧٦٫٦٪</strong><i className="current-score" style={{ width: "76.6%" }} /></div>
            </div>
            <p><Icon name="progress" /> ارتفع المتوسط منذ بداية التدخل، والبيانات النهائية تُحسب بعد اكتمال الاختبار البعدي.</p>
          </article>

          <article className="levels-chart-card">
            <div className="panel-heading"><div><span>التوزيع الحالي</span><h2>الطلاب حسب المستوى</h2></div></div>
            <div className="level-bars">
              <div><span>الاستعداد للقراءة</span><i><b style={{ width: "53%" }} /></i><strong>٤</strong></div>
              <div><span>بناء الكلمة</span><i><b style={{ width: "93%" }} /></i><strong>٧</strong></div>
              <div><span>الطلاقة والفهم</span><i><b style={{ width: "53%" }} /></i><strong>٤</strong></div>
            </div>
          </article>
        </section>

        <section className="dashboard-lower-grid">
          <article className="students-panel">
            <div className="panel-heading panel-heading-with-action">
              <div><span>المتابعة اليومية</span><h2>حالة الطلاب</h2></div>
              <button type="button" onClick={() => showToast("ستفتح صفحة إدارة الطلاب في النسخة الكاملة.")}>عرض الجميع <span>←</span></button>
            </div>
            <div className="students-table-wrap">
              <table>
                <thead><tr><th>الطالب</th><th>المستوى الحالي</th><th>القبلي</th><th>الأداء الحالي</th><th>الحالة</th></tr></thead>
                <tbody>
                  {researchStudents.map((student) => (
                    <tr key={student.code}>
                      <td><span className="table-avatar">{student.name[0]}</span><div><strong>{student.name}</strong><small>{student.code}</small></div></td>
                      <td>{student.level}</td><td>{student.pre}</td><td><strong>{student.current}</strong></td>
                      <td><span className={`status-pill ${student.statusClass}`}>{student.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="review-panel">
            <div className="panel-heading"><div><span>إجراء مطلوب</span><h2>مراجعة الصوت</h2></div><span className="review-count">٣</span></div>
            <p className="review-intro">تسجيلات لم تصل إلى حد الثقة المعتمد.</p>
            <div className="review-list">
              {[{name:"سالم",word:"قِطَّةٌ",confidence:"٦١٪"},{name:"ماجد",word:"شَمْسٌ",confidence:"٥٧٪"},{name:"مريم",word:"يَقْرَأُ",confidence:"٦٤٪"}].map((item) => (
                <div className="review-item" key={`${item.name}-${item.word}`}>
                  <button type="button" aria-label={`تشغيل تسجيل ${item.name}`} onClick={() => showToast(`تشغيل تسجيل ${item.name} تجريبيًا.`)}><Icon name="play-audio" /></button>
                  <div><strong>{item.name} · {item.word}</strong><span>ثقة التحليل {item.confidence}</span></div>
                  <button className="review-action" type="button" onClick={() => showToast("ستفتح شاشة المراجعة التفصيلية.")}>مراجعة</button>
                </div>
              ))}
            </div>
          </article>
        </section>
      </section>
      {toast && <div className="dashboard-toast" role="status"><Icon name="success" /> {toast}</div>}
    </main>
  );
}

export default function Home() {
  const [screen, setScreen] = useState<Screen>("welcome");

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [screen]);

  return (
    <div className="himma-app" dir="rtl">
      <div className="ambient-shape ambient-one" />
      <div className="ambient-shape ambient-two" />
      {screen === "welcome" && (
        <WelcomeScreen
          onStudentLogin={() => setScreen("student-login")}
          onResearcherLogin={() => setScreen("researcher-login")}
        />
      )}
      {screen === "student-login" && (
        <StudentLoginScreen onBack={() => setScreen("welcome")} onLogin={() => setScreen("student-home")} />
      )}
      {screen === "student-home" && (
        <StudentHomeScreen onHome={() => setScreen("welcome")} onStart={() => setScreen("pretest")} />
      )}
      {screen === "pretest" && <PretestScreen onExit={() => setScreen("student-home")} onContinue={() => setScreen("activity")} />}
      {screen === "activity" && <ActivityScreen onExit={() => setScreen("student-home")} onContinue={() => setScreen("record")} />}
      {screen === "record" && <RecordScreen onExit={() => setScreen("student-home")} onComplete={() => setScreen("success")} />}
      {screen === "success" && (
        <SuccessScreen onStudentHome={() => setScreen("student-home")} onResearcher={() => setScreen("researcher-dashboard")} />
      )}
      {screen === "researcher-login" && (
        <ResearcherLoginScreen onBack={() => setScreen("welcome")} onLogin={() => setScreen("researcher-dashboard")} />
      )}
      {screen === "researcher-dashboard" && <ResearcherDashboard onExit={() => setScreen("welcome")} />}
    </div>
  );
}
