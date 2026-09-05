"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { BookOpenCheck, Check, Headphones, LogOut, Map, Star } from "lucide-react";
import styles from "./home.module.css";

interface StudentMe {
  id: number;
  full_name: string;
  grade_level: number;
  current_level: number;
  posttest_enabled: boolean;
  next_action: "resume" | "pretest" | "learning" | "posttest" | "completed";
  active_session: {
    id: number;
    session_type: "pretest" | "posttest" | "core";
    status: "in_progress" | "answering" | "waiting_audio_review" | "rerecord_required" | "ready_to_finalize" | string;
  } | null;
}

interface LearningStatus {
  available: boolean;
  reason?: string;
  level_id: number;
  completed_items: number;
  total_items: number;
  completed: boolean;
  session_id: number | null;
  pending_count?: number;
  rerecord_required_count?: number;
  unresolved_count?: number;
  audio_review_pending?: boolean;
}

interface RewardEvent {
  id: number;
  type: string;
  stars: number;
  label: string;
}

interface AudioReviewTask {
  id: number;
  status: "uploaded" | "pending" | "rerecord_required" | string;
  submitted_at: string;
  session_id: number;
  session_type: "pretest" | "posttest" | "core";
  level_id?: number | null;
  item_id: number;
  step_id: number;
  item_title?: string | null;
  expected_reading_text?: string | null;
  can_rerecord: boolean;
}

interface JourneyLevel {
  level_id: number;
  name: string;
  state: "locked" | "skipped" | "ready" | "active" | "completed";
  completed_items: number;
  total_items: number;
  session_id: number | null;
}

interface JourneySummary {
  pretest_completed: boolean;
  starting_level: number | null;
  current_level: number;
  levels: JourneyLevel[];
  learning_journey_completed: boolean;
  posttest_enabled: boolean;
  posttest_completed: boolean;
  posttest_ready: boolean;
}

const LEVEL_NAMES: Record<number, string> = {
  1: "الاستعداد للقراءة",
  2: "بناء الكلمة",
  3: "الطلاقة والفهم",
};

const LEVEL_STATE_LABELS: Record<JourneyLevel["state"], string> = {
  locked: "لاحقًا",
  skipped: "تجاوزته في الاختبار القبلي",
  ready: "جاهز للبدء",
  active: "أنت هنا",
  completed: "مكتمل",
};

export default function StudentHomePage() {
  const router = useRouter();
  const [student, setStudent] = useState<StudentMe | null>(null);
  const [learning, setLearning] = useState<LearningStatus | null>(null);
  const [journey, setJourney] = useState<JourneySummary | null>(null);
  const [rewards, setRewards] = useState<RewardEvent[]>([]);
  const [audioReviews, setAudioReviews] = useState<AudioReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const profileResponse = await fetch("/api/profile", { cache: "no-store" });
        const profileData = await profileResponse.json().catch(() => null);
        if (!profileResponse.ok) throw new Error(profileData?.detail || "تعذر تحميل مسارك");
        const profile: StudentMe = profileData;
        setStudent(profile);

        const requests: Promise<void>[] = [];
        if (profile.next_action === "learning" || profile.active_session?.session_type === "core") {
          requests.push(
            fetch("/api/activities/status", { cache: "no-store" }).then(async (response) => {
              if (response.ok) setLearning(await response.json());
            }),
          );
        }
        requests.push(
          fetch("/api/journey", { cache: "no-store" }).then(async (response) => {
            if (response.ok) setJourney(await response.json());
          }),
        );
        requests.push(
          fetch("/api/rewards", { cache: "no-store" }).then(async (response) => {
            if (response.ok) setRewards(await response.json());
          }),
        );
        requests.push(
          fetch("/api/review/student-audio", { cache: "no-store" }).then(async (response) => {
            if (response.ok) setAudioReviews(await response.json());
          }),
        );
        await Promise.all(requests);
      } catch (err) {
        setError(err instanceof Error ? err.message : "تعذر تحميل بياناتك. حدّث الصفحة وحاول مرة أخرى.");
      } finally {
        setLoading(false);
      }
    };
    void fetchData();
  }, []);

  const waitingForAudioReview = student?.active_session?.status === "waiting_audio_review";
  const rerecordTasks = audioReviews.filter((task) => task.status === "rerecord_required");
  const pendingReviewTasks = audioReviews.filter((task) => task.status === "uploaded" || task.status === "pending");

  const handlePrimaryAction = async () => {
    if (!student || waitingForAudioReview) return;
    setStarting(true);
    setError("");
    try {
      if (student.active_session?.session_type === "pretest" || student.active_session?.session_type === "posttest") {
        router.push(`/student/session/${student.active_session.id}`);
        return;
      }

      const isLearning = student.next_action === "learning" || student.active_session?.session_type === "core";
      if (isLearning) {
        const existingSession = student.active_session?.session_type === "core" ? student.active_session.id : learning?.session_id;
        if (existingSession) {
          router.push(`/student/activity/${existingSession}`);
          return;
        }
        if (learning?.completed) return;
        const response = await fetch("/api/activities/start", { method: "POST" });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.detail || "تعذر بدء الأنشطة التعليمية");
        router.push(`/student/activity/${data.session_id}`);
        return;
      }

      if (student.next_action === "pretest" || student.next_action === "posttest") {
        const response = await fetch("/api/assessment/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_type: student.next_action }),
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.detail || "تعذر بدء الاختبار");
        router.push(`/student/session/${data.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر الاتصال بالخادم");
      setStarting(false);
    }
  };

  const handleRerecord = async (task: AudioReviewTask) => {
    if (starting) return;
    setStarting(true);
    setError("");
    try {
      const response = await fetch(`/api/review/student-audio/${task.id}/begin-rerecord`, { method: "POST" });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر فتح إعادة التسجيل");
      if (data.session_type === "core") {
        router.push(`/student/activity/${data.session_id}`);
      } else {
        router.push(`/student/session/${data.session_id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر فتح إعادة التسجيل");
      setStarting(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      router.replace("/");
      router.refresh();
    }
  };

  const totalStars = useMemo(() => rewards.reduce((sum, reward) => sum + (reward.stars || 0), 0), [rewards]);

  if (loading) {
    return (
      <div className={styles.page} dir="rtl">
        <div className="min-h-screen flex flex-col items-center justify-center gap-4">
          <Image src="/brand/logo-gradient.svg" alt="هِمّة" width={130} height={44} priority />
          <div className="spinner w-12 h-12 border-4" />
          <p className="text-muted">جاري تجهيز رحلتك...</p>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className={styles.page} dir="rtl">
        <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-6 text-center">
          <h1 className="text-2xl font-bold">تعذر فتح حساب الطالب</h1>
          <p className="text-muted">{error || "سجّل الدخول مرة أخرى."}</p>
          <button className={styles.button} onClick={() => router.replace("/student/login")}>العودة إلى الدخول</button>
        </div>
      </div>
    );
  }

  const isLearning = student.next_action === "learning" || student.active_session?.session_type === "core";
  const learningCompleted = Boolean(learning?.completed);
  const learningProgress = learning ? Math.min(100, Math.round((learning.completed_items / Math.max(1, learning.total_items)) * 100)) : 0;
  const firstName = student.full_name.split(" ")[0] || "بطل هِمّة";

  let heroTitle = "الاختبار القبلي";
  let heroDescription = "أسئلة قصيرة ومتنوعة تساعد هِمّة على اختيار البداية المناسبة لك.";
  let primaryLabel = "ابدأ الاختبار";
  let phaseIndex = 0;
  let character = "/characters/girl/welcome.png";

  if (student.active_session?.session_type === "pretest") primaryLabel = "متابعة الاختبار";
  if (isLearning) {
    phaseIndex = 1;
    heroTitle = `مستواك: ${LEVEL_NAMES[student.current_level] || `المستوى ${student.current_level}`}`;
    if (learningCompleted && student.current_level < 3) {
      heroDescription = `أكملت ${LEVEL_NAMES[student.current_level]}. خطوتك التالية هي ${LEVEL_NAMES[student.current_level + 1]}.`;
    } else if (learningCompleted) {
      heroDescription = "أكملت المستوى الثالث. بقيت خطوة القياس البعدي عندما تصبح متاحة لك.";
    } else {
      heroDescription = "أنشطة قصيرة بالصوت والصورة والقراءة، وتتدخل التقوية عند الحاجة ثم تعيدك إلى مسارك.";
    }
    primaryLabel = learningCompleted ? "اكتمل هذا المستوى" : (student.active_session?.session_type === "core" || learning?.session_id ? "متابعة الأنشطة" : "ابدأ أنشطة مستواك");
    character = learningCompleted ? "/characters/girl/success.png" : "/characters/girl/explain.png";
  }
  if (student.next_action === "posttest" || student.active_session?.session_type === "posttest") {
    phaseIndex = 2;
    heroTitle = "الاختبار البعدي";
    heroDescription = "خطوتك الأخيرة لقياس التطور الذي حققته خلال رحلة هِمّة.";
    primaryLabel = student.active_session?.session_type === "posttest" ? "متابعة الاختبار" : "ابدأ الاختبار البعدي";
    character = "/characters/girl/encourage.png";
  }
  if (waitingForAudioReview) {
    phaseIndex = student.active_session?.session_type === "posttest" ? 2 : 0;
    heroTitle = "بانتظار مراجعة التسجيلات";
    heroDescription = "أنهيت جميع الأسئلة، وتم حفظ إجاباتك وتسجيلاتك. لا تحتاج إلى إعادة الاختبار؛ ستظهر نتيجتك ومسارك تلقائيًا بعد اكتمال مراجعة التسجيلات.";
    primaryLabel = "تم إرسال التسجيلات للمراجعة";
    character = "/characters/girl/encourage.png";
  }
  if (student.next_action === "completed") {
    phaseIndex = 3;
    heroTitle = "أكملت رحلتك";
    heroDescription = "أنهيت الاختبارين ومسار التعلم. أحسنت التقدم!";
    primaryLabel = "اكتمل المسار";
    character = "/characters/girl/success.png";
  }

  const primaryDisabled = starting || waitingForAudioReview || student.next_action === "completed" || (isLearning && learningCompleted);

  return (
    <div className={styles.page} dir="rtl" data-testid="student-home">
      <header className={styles.header}>
        <Image src="/brand/logo-gradient.svg" alt="هِمّة" width={132} height={44} priority />
        <div className={styles.userChip}>
          <div className={styles.avatar}>{firstName.charAt(0)}</div>
          <div><strong>{firstName}</strong><button className={styles.logout} onClick={() => void handleLogout()}><LogOut size={14} /> خروج</button></div>
        </div>
      </header>

      <main className={styles.container}>
        <section className={styles.welcome}>
          <div>
            <span className={styles.eyebrow}><Star size={14} fill="currentColor" /> جاهز للتقدم</span>
            <h1>مرحبًا يا {firstName}</h1>
            <p>خطوتك التالية واضحة أمامك، وهِمّة تحفظ تقدمك تلقائيًا.</p>
          </div>
          <div className={styles.stars} aria-label={`لديك ${totalStars} نجمة`}><strong>{totalStars} ⭐</strong><span>نجومك حتى الآن</span></div>
        </section>

        <div className={styles.grid}>
          <section className={`${styles.hero} ${student.next_action === "completed" ? styles.completed : ""}`}>
            <div className={styles.heroContent}>
              <span className={styles.stepLabel}><BookOpenCheck size={15} /> خطوتك الحالية</span>
              <h2>{heroTitle}</h2>
              <p>{heroDescription}</p>
              <div className={styles.meta}>
                {waitingForAudioReview
                  ? <><span>30 من 30 سؤالًا</span><span>•</span><span>بانتظار التقييم الصوتي</span></>
                  : isLearning
                    ? <><span>{learning?.completed_items ?? 0} من {learning?.total_items ?? 10} أنشطة</span><span>•</span><span>مهمة واحدة في كل شاشة</span></>
                    : <><span>30 سؤالًا</span><span>•</span><span>يحفظ تلقائيًا</span></>}
              </div>
              <button className={styles.button} onClick={() => void handlePrimaryAction()} disabled={primaryDisabled} data-testid="student-primary-action">
                {starting && <span className="spinner w-5 h-5" />}{primaryLabel}
              </button>
              {error && <div className={styles.error} role="alert">{error}</div>}
            </div>
            <div className={styles.heroVisual}><Image src={character} alt="شخصية هِمّة" width={250} height={300} priority /></div>
          </section>

          <aside className={styles.side}>
            <div className={styles.tipCard}>
              <div className={styles.tipIcon}><Headphones size={21} /></div>
              <h3>قبل أن تبدأ</h3>
              <p>{waitingForAudioReview ? "تم حفظ تسجيلاتك. يمكنك العودة لاحقًا، وستتحدث النتيجة تلقائيًا بعد المراجعة." : "اختر مكانًا هادئًا، وارفع صوت الجهاز بدرجة مريحة، ثم اتبع تعليمات كل مهمة كما تظهر لك."}</p>
            </div>
            <div className={styles.progressCard}>
              <div className={styles.tipIcon}><Map size={21} /></div>
              <h3>تقدم المستوى</h3>
              <div className={styles.progressRing} style={{ "--progress": `${waitingForAudioReview ? 100 : isLearning ? learningProgress : phaseIndex >= 2 ? 100 : 0}%` } as React.CSSProperties}>
                <strong>{waitingForAudioReview ? "100%" : isLearning ? `${learningProgress}%` : phaseIndex >= 2 ? "100%" : "جاهز"}</strong>
              </div>
              <p>{waitingForAudioReview ? "اكتملت الأسئلة، والمتبقي مراجعة التسجيلات فقط." : isLearning ? "كل نشاط مكتمل يقربك من هدفك." : "سنبدأ بخطوة قصيرة لتحديد مسارك."}</p>
            </div>
          </aside>
        </div>

        {audioReviews.length > 0 && (
          <section className={styles.levelJourney} aria-label="حالة مراجعة التسجيلات" data-testid="audio-review-status">
            <div className={styles.journeyHeader}>
              <div>
                <h3>{rerecordTasks.length > 0 ? "يوجد تسجيل يحتاج إعادة" : "تسجيلك تحت المراجعة"}</h3>
                <p>
                  {rerecordTasks.length > 0
                    ? "المشرف طلب إعادة تسجيل محدد. افتحه من هنا، وبعد الإرسال ارجع وكمل من مكانك."
                    : "كمل أنشطتك بشكل طبيعي. المراجعة تعمل في الخلفية، ولن تنتقل إلى المستوى التالي حتى يعتمد المشرف التسجيل."}
                </p>
              </div>
              <span>{rerecordTasks.length > 0 ? `${rerecordTasks.length} إعادة مطلوبة` : `${pendingReviewTasks.length} تحت المراجعة`}</span>
            </div>
            <div className={styles.levelCards}>
              {rerecordTasks.length > 0 ? rerecordTasks.map((task) => (
                <article key={task.id} className={styles.levelCard}>
                  <div className={styles.levelTopline}>
                    <div className={styles.levelNumber}><Headphones size={20} /></div>
                    <span>إعادة التسجيل</span>
                  </div>
                  <h4>{task.item_title || "مهمة القراءة"}</h4>
                  <p>{task.expected_reading_text ? `النص: ${task.expected_reading_text}` : "أعد التسجيل المطلوب من المشرف فقط."}</p>
                  <button className={styles.button} disabled={starting} onClick={() => void handleRerecord(task)}>
                    {starting && <span className="spinner w-5 h-5" />} إعادة التسجيل الآن
                  </button>
                </article>
              )) : (
                <article className={styles.levelCard}>
                  <div className={styles.levelTopline}>
                    <div className={styles.levelNumber}><Headphones size={20} /></div>
                    <span>لا يوقفك</span>
                  </div>
                  <h4>المراجعة جارية في الخلفية</h4>
                  <p>تابع أنشطتك الحالية؛ هِمّة ستحجز الانتقال للمستوى التالي فقط إلى أن تنتهي المراجعة.</p>
                </article>
              )}
            </div>
          </section>
        )}

        {journey?.pretest_completed && (
          <section className={styles.levelJourney} aria-label="مستويات رحلة التعلم" data-testid="level-journey">
            <div className={styles.journeyHeader}>
              <div>
                <h3>مستويات رحلتك</h3>
                <p>تتقدم للأعلى بعد إكمال المستوى، والتقوية تساعدك داخل مسارك دون إعادته من البداية.</p>
              </div>
              <span>{journey.starting_level ? `بدأت من المستوى ${journey.starting_level}` : "مسارك التعليمي"}</span>
            </div>
            <div className={styles.levelCards}>
              {journey.levels.map((level) => {
                const levelPercent = Math.min(100, Math.round((level.completed_items / Math.max(1, level.total_items)) * 100));
                return (
                  <article key={level.level_id} className={`${styles.levelCard} ${styles[`levelState${level.state.charAt(0).toUpperCase()}${level.state.slice(1)}`]}`} data-level-state={level.state}>
                    <div className={styles.levelTopline}>
                      <div className={styles.levelNumber}>{level.state === "completed" ? <Check size={20} /> : level.level_id}</div>
                      <span>{LEVEL_STATE_LABELS[level.state]}</span>
                    </div>
                    <h4>{level.name}</h4>
                    {level.state === "skipped" ? (
                      <p>نتيجة الاختبار القبلي وضعتك في مستوى أعلى، لذلك لا تحتاج لإعادة هذا المستوى.</p>
                    ) : (
                      <>
                        <div className={styles.levelProgressTrack} aria-label={`تقدم المستوى ${level.level_id}: ${level.completed_items} من ${level.total_items}`}>
                          <span style={{ width: `${level.state === "completed" ? 100 : levelPercent}%` }} />
                        </div>
                        <p>{level.state === "locked" ? "يفتح بعد إكمال المستوى السابق." : `${level.completed_items} من ${level.total_items} أنشطة أساسية`}</p>
                      </>
                    )}
                  </article>
                );
              })}
            </div>
          </section>
        )}

        <section className={styles.journey} aria-label="رحلة الطالب">
          <div className={styles.journeyHeader}><h3>رحلتك في هِمّة</h3><span>نبني على مستواك الحقيقي</span></div>
          <div className={styles.steps}>
            {[{label:"نكتشف بدايتك",sub:"الاختبار القبلي"},{label:"نتعلم ونتطور",sub:"من مستوى البداية حتى الثالث"},{label:"نقيس تقدمك",sub:"الاختبار البعدي"}].map((entry,index) => {
              const done = phaseIndex > index || student.next_action === "completed";
              const current = phaseIndex === index;
              return (
                <div key={entry.label} className={`${styles.step} ${done ? styles.stepDone : ""} ${current ? styles.stepCurrent : ""}`} aria-current={current ? "step" : undefined}>
                  <div className={styles.stepIcon}>{done ? <Check size={20} /> : index + 1}</div>
                  <strong>{entry.label}</strong><span>{entry.sub}</span>
                </div>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}