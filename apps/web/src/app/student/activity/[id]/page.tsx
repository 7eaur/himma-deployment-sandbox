"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { ArrowRight, Check, CheckCircle2, Mic, MicOff, RotateCcw, Volume2 } from "lucide-react";
import styles from "../activity.module.css";

type Interaction =
  | "choose_one"
  | "listen_choose_one"
  | "choose_image"
  | "listen_choose_image"
  | "choose_many"
  | "listen_choose_many"
  | "sequence"
  | "memory_sequence"
  | "path_sequence"
  | "build_word"
  | "read_aloud"
  | "timed_read_aloud";

type MemoryPhase = "preview" | "recall";

interface ActivityOption { id: number; text: string; order_index: number; }
interface ActivityAsset {
  asset_id: string;
  asset_type: "audio" | "image" | string;
  usage?: string | null;
  semantic_text?: string | null;
  url: string;
  option_id?: number | null;
}
interface MediaGap {
  asset_type: string;
  usage: string;
  semantic_text: string;
  status: string;
  reason?: string;
}
interface ActivityPayload {
  session_id: number;
  item: {
    id: number;
    stable_key: string;
    canonical_id: string;
    title: string;
    level_id: number;
    order_index: number;
    interaction_type: Interaction;
    source_method?: string | null;
    kind?: string;
    assets?: ActivityAsset[];
  };
  step: {
    id: number;
    order_index: number;
    prompt_text: string;
    instruction_text?: string | null;
    expected_reading_text?: string | null;
    options: ActivityOption[];
    assets: ActivityAsset[];
    media_gaps: MediaGap[];
  };
  attempts_used: number;
  max_attempts: number;
  retry: boolean;
  hint_available: boolean;
}
interface LearningProgress {
  session_id: number;
  status: "in_progress" | "completed";
  level_id: number;
  completed_items: number;
  total_items: number;
  elapsed_seconds: number;
}
interface SubmitResult {
  is_correct: boolean;
  attempts_used: number;
  step_complete: boolean;
  show_hint: boolean;
  activity_complete: boolean;
  learning_complete: boolean;
  detail?: string;
}

const LEVEL_NAMES: Record<number, string> = {
  1: "الاستعداد للقراءة",
  2: "بناء الكلمة",
  3: "الطلاقة والفهم",
};
const SINGLE = new Set<Interaction>(["choose_one", "listen_choose_one", "choose_image", "listen_choose_image"]);
const MULTI = new Set<Interaction>(["choose_many", "listen_choose_many"]);
const ORDER = new Set<Interaction>(["sequence", "memory_sequence", "build_word"]);
const AUDIO = new Set<Interaction>(["read_aloud", "timed_read_aloud"]);
const LISTEN = new Set<Interaction>(["listen_choose_one", "listen_choose_image", "listen_choose_many"]);

const INTERACTION_LABEL: Record<Interaction, string> = {
  choose_one: "اختيار إجابة",
  listen_choose_one: "استمع ثم اختر",
  choose_image: "اختيار صورة",
  listen_choose_image: "استمع ثم اختر صورة",
  choose_many: "اختيار أكثر من عنصر",
  listen_choose_many: "استمع ثم اختر العناصر",
  sequence: "ترتيب",
  memory_sequence: "ذاكرة بصرية",
  path_sequence: "نشاط مستبدل",
  build_word: "بناء كلمة",
  read_aloud: "قراءة بصوت واضح",
  timed_read_aloud: "قراءة وطلاقة",
};

function stableOptionOrder(values: ActivityOption[]) {
  return [...values].sort((a, b) => ((a.id * 19) % 101) - ((b.id * 19) % 101));
}

function conciseTitle(title?: string) {
  if (!title) return "مهارة تعليمية";
  const value = title.includes(":") ? title.split(":").slice(1).join(":").trim() : title;
  return value || "مهارة تعليمية";
}

function cleanPrompt(value: string, interaction: Interaction) {
  if (AUDIO.has(interaction) || interaction === "memory_sequence") return "";
  if (interaction === "sequence" || interaction === "build_word") return "";
  let prompt = value.replace(/^التعليمات:\s*/u, "");
  prompt = prompt.split(/الخيارات:|الصور:/u)[0].trim();
  return prompt;
}

function contextualHint(instruction: string, interaction: Interaction) {
  if (/آخرها|الأخير|تنتهي/u.test(instruction)) return "أعد الاستماع، وركّز على آخر صوت تسمعه في الكلمة.";
  if (/أول حرف|بداية الكلمة|قارن/u.test(instruction) && /متشابهان|مختلفان|يطابق/u.test(instruction)) return "استمع إلى الصوت، ثم انظر إلى أول حرف في الكلمة وقارن بينهما فقط.";
  if (/بدايتها|يبدأ اسمها|أول صوت|تبدأ/u.test(instruction)) return "استمع مرة أخرى، وركّز على أول صوت تسمعه.";
  if (/الشكل الآخر|الحرف نفسه|شكله/u.test(instruction)) return "قارن شكل الحرف ونقاطه بالخيارات، ثم اختر الشكل المطابق.";
  if (/الصورة/u.test(instruction) && LISTEN.has(interaction)) return "قل اسم كل صورة في ذهنك، ثم ركّز على الصوت المطلوب.";
  if (interaction === "memory_sequence") return "تذكّر الصورة التي ظهرت أولًا، ثم أكمل باقي الترتيب.";
  if (interaction === "build_word") return "قل الكلمة في ذهنك، ثم ابدأ بالحرف الأول وأكمل بالترتيب.";
  if (interaction === "sequence") return "فكّر: ماذا حدث أولًا؟ ثم أكمل الأحداث خطوةً خطوة.";
  if (/النص|السؤال|الإجابة/u.test(instruction)) return "ارجع إلى الجزء من النص الذي يساعدك على الإجابة.";
  return "اقرأ التعليمة مرة أخرى بهدوء، ثم جرّب من جديد.";
}

function helperMessage(instruction: string, interaction: Interaction, isReinforcement: boolean) {
  if (isReinforcement) return "هذا تدريب قصير يساعدك على إتقان المهارة. جرّب بهدوء.";
  if (interaction === "memory_sequence") return "شاهد الصور جيدًا؛ بعد قليل ستختفي وستعيد ترتيبها.";
  if (LISTEN.has(interaction)) return "يمكنك الاستماع مرة أخرى قبل أن تختار.";
  if (AUDIO.has(interaction)) return "خذ وقتك، واقرأ بصوت هادئ وواضح.";
  if (interaction === "sequence") return "ابدأ بما حدث أولًا، ثم أكمل الترتيب.";
  if (interaction === "build_word") return "ابدأ بالحرف الأول، ثم أكمل الكلمة خطوة خطوة.";
  if (/حرف|شكل/u.test(instruction)) return "ركّز في شكل الحرف ونقاطه قبل أن تختار.";
  return "خذ وقتك، اقرأ المطلوب بهدوء ثم اختر إجابتك.";
}

function successMessage(instruction: string, interaction: Interaction) {
  if (/آخرها|الأخير/u.test(instruction)) return "أحسنت! عرفت الصوت الأخير في الكلمة.";
  if (/بداية|أول حرف/u.test(instruction)) return "رائع! ركّزت على بداية الكلمة بشكل صحيح.";
  if (/الشكل الآخر|الحرف نفسه|شكله/u.test(instruction)) return "ممتاز! عرفت شكل الحرف الصحيح.";
  if (interaction === "memory_sequence") return "رائع! تذكّرت ترتيب الصور بشكل صحيح.";
  if (interaction === "sequence") return "أحسنت! رتّبت الأحداث بشكل صحيح.";
  if (interaction === "build_word") return "رائع! كوّنت الكلمة بالترتيب الصحيح.";
  return "أحسنت! إجابتك صحيحة.";
}

export default function StudentActivityPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = String(params.id);
  const [activity, setActivity] = useState<ActivityPayload | null>(null);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [memoryPhase, setMemoryPhase] = useState<MemoryPhase>("recall");
  const startedAtRef = useRef(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playbackRef = useRef<HTMLAudioElement | null>(null);

  const interaction = activity?.item.interaction_type;
  const isReinforcement = activity?.item.kind === "reinforcement_activity";
  const options = useMemo(() => stableOptionOrder(activity?.step.options ?? []), [activity]);
  const audioAssets = useMemo(() => activity?.step.assets.filter((asset) => asset.asset_type === "audio") ?? [], [activity]);
  const imageAssets = useMemo(() => activity?.step.assets.filter((asset) => asset.asset_type === "image") ?? [], [activity]);
  const contextAssets = useMemo(() => activity?.item.assets?.filter((asset) => asset.asset_type === "image") ?? [], [activity]);
  const percent = progress ? Math.min(100, Math.round((progress.completed_items / Math.max(1, progress.total_items)) * 100)) : 0;

  const fetchProgress = useCallback(async () => {
    const response = await fetch(`/api/activities/session/${sessionId}/progress`, { cache: "no-store" });
    if (response.ok) setProgress(await response.json());
  }, [sessionId]);

  const resetQuestionState = () => {
    setSelected([]);
    setAudioBlob(null);
    setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return null; });
    setRecordingSeconds(0);
    setFeedback(null);
  };

  const fetchNext = useCallback(async () => {
    setError("");
    try {
      const response = await fetch(`/api/activities/session/${sessionId}/next`, { cache: "no-store" });
      const data: ActivityPayload | null = await response.json().catch(() => null);
      if (!response.ok) throw new Error((data as unknown as { detail?: string })?.detail || "تعذر تحميل النشاط");
      if (!data) {
        setDone(true);
        setActivity(null);
        await fetchProgress();
        return;
      }
      setActivity(data);
      setSelected([]);
      setAudioBlob(null);
      setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return null; });
      setFeedback(null);
      setRecordingSeconds(0);
      setMemoryPhase(data.item.interaction_type === "memory_sequence" ? "preview" : "recall");
      startedAtRef.current = Date.now();
      await fetchProgress();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل النشاط");
    }
  }, [fetchProgress, sessionId]);

  useEffect(() => {
    const kickoff = window.setTimeout(() => void fetchNext(), 0);
    return () => {
      window.clearTimeout(kickoff);
      if (timerRef.current) clearInterval(timerRef.current);
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      playbackRef.current?.pause();
    };
  }, [fetchNext]);

  useEffect(() => {
    if (!activity || activity.item.interaction_type !== "memory_sequence" || memoryPhase !== "preview") return;
    const preview = window.setTimeout(() => setMemoryPhase("recall"), 2800);
    return () => window.clearTimeout(preview);
  }, [activity, memoryPhase]);

  const makeIdempotencyKey = (kind: "answer" | "upload") => {
    const stepId = activity?.step.id ?? 0;
    const attempt = (activity?.attempts_used ?? 0) + 1;
    const storageKey = `himma:activity:${sessionId}:${stepId}:${attempt}:${kind}`;
    const existing = window.sessionStorage.getItem(storageKey);
    if (existing) return existing;
    const created = crypto.randomUUID();
    window.sessionStorage.setItem(storageKey, created);
    return created;
  };

  const clearIdempotency = () => {
    if (!activity) return;
    const attempt = activity.attempts_used + 1;
    for (const kind of ["answer", "upload"] as const) window.sessionStorage.removeItem(`himma:activity:${sessionId}:${activity.step.id}:${attempt}:${kind}`);
  };

  const playPrompt = async () => {
    if (!audioAssets.length || isListening) return;
    setIsListening(true);
    setError("");
    try {
      for (const asset of audioAssets) {
        await new Promise<void>((resolve, reject) => {
          const audio = new Audio(asset.url);
          playbackRef.current = audio;
          audio.onended = () => resolve();
          audio.onerror = () => reject(new Error("تعذر تشغيل الصوت"));
          void audio.play().catch(reject);
        });
      }
    } catch {
      setError("تعذر تشغيل الصوت. تحقق من مستوى الصوت في الجهاز ثم حاول مرة أخرى.");
    } finally {
      setIsListening(false);
      playbackRef.current = null;
    }
  };

  const submitStructured = async (mediaGapSkip = false) => {
    if (!activity || !interaction) return;
    setSubmitting(true);
    setError("");
    const elapsedSeconds = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
    try {
      const response = await fetch(`/api/activities/session/${sessionId}/attempt/${activity.item.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": makeIdempotencyKey("answer") },
        body: JSON.stringify({ step_id: activity.step.id, selected_option_ids: selected, hint_used: activity.retry, elapsed_seconds: elapsedSeconds, declared_media_gap_skip: mediaGapSkip }),
      });
      const result: SubmitResult = await response.json().catch(() => ({} as SubmitResult));
      if (!response.ok) throw new Error(result.detail || "تعذر حفظ الإجابة");
      clearIdempotency();
      const instruction = activity.step.instruction_text || "";
      if (result.learning_complete) {
        setDone(true);
        setFeedback({ ok: true, text: "أحسنت، أكملت أنشطة مستواك." });
        await fetchProgress();
        return;
      }
      if (result.is_correct || result.step_complete) {
        setFeedback({ ok: result.is_correct, text: result.is_correct ? successMessage(instruction, interaction) : "أكملت المحاولة، وسننتقل إلى الخطوة التالية." });
        window.setTimeout(() => void fetchNext(), 720);
      } else {
        setFeedback({ ok: false, text: contextualHint(instruction, interaction) });
        await fetchNext();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ الإجابة");
    } finally {
      setSubmitting(false);
    }
  };

  const startRecording = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const preferred = "audio/webm;codecs=opus";
      const recorder = MediaRecorder.isTypeSupported(preferred) ? new MediaRecorder(stream, { mimeType: preferred }) : new MediaRecorder(stream);
      recorder.ondataavailable = (event) => { if (event.data.size > 0) chunksRef.current.push(event.data); };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return URL.createObjectURL(blob); });
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      recorderRef.current = recorder;
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => setRecordingSeconds((value) => value + 1), 1000);
    } catch {
      setError("لم نتمكن من تشغيل الميكروفون. اسمح للمتصفح باستخدامه ثم حاول مرة أخرى.");
    }
  };

  const stopRecording = () => {
    if (!recorderRef.current || recorderRef.current.state !== "recording") return;
    recorderRef.current.stop();
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const uploadReading = async () => {
    if (!activity || !audioBlob) return;
    setSubmitting(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", audioBlob, "activity-reading.webm");
      const upload = await fetch(`/api/assessment/session/${sessionId}/upload-audio`, { method: "POST", headers: { "Idempotency-Key": makeIdempotencyKey("upload") }, body: form });
      const uploaded = await upload.json().catch(() => null);
      if (!upload.ok) throw new Error(uploaded?.detail || "تعذر رفع التسجيل");
      const elapsedSeconds = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
      const submit = await fetch(`/api/activities/session/${sessionId}/attempt/${activity.item.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": makeIdempotencyKey("answer") },
        body: JSON.stringify({ step_id: activity.step.id, audio_storage_key: uploaded.audio_storage_key, audio_file_size: uploaded.audio_file_size, audio_mime_type: uploaded.audio_mime_type, audio_duration_seconds: recordingSeconds, elapsed_seconds: elapsedSeconds }),
      });
      const result = await submit.json().catch(() => null);
      if (!submit.ok) throw new Error(result?.detail || "تعذر حفظ القراءة");
      clearIdempotency();
      setFeedback({ ok: true, text: "تم حفظ قراءتك. أحسنت!" });
      window.setTimeout(() => void fetchNext(), 720);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ القراءة");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleOption = (optionId: number) => {
    if (!interaction || submitting || (interaction === "memory_sequence" && memoryPhase === "preview")) return;
    setFeedback(null);
    if (SINGLE.has(interaction)) { setSelected([optionId]); return; }
    if (MULTI.has(interaction)) {
      setSelected((current) => current.includes(optionId) ? current.filter((id) => id !== optionId) : [...current, optionId]);
      return;
    }
    if (ORDER.has(interaction)) setSelected((current) => current.includes(optionId) ? current : [...current, optionId]);
  };

  const readyToSubmit = Boolean(interaction && (
    (SINGLE.has(interaction) && selected.length === 1)
    || (MULTI.has(interaction) && selected.length >= 2)
    || (ORDER.has(interaction) && selected.length === options.length)
  ));

  if (done) {
    const completedLevel = progress?.level_id ?? 1;
    const hasNextLevel = completedLevel < 3;
    const nextLevelName = LEVEL_NAMES[completedLevel + 1];
    return (
      <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="done">
        <main className={styles.main}><section className={`${styles.card} ${styles.done}`}>
          <CheckCircle2 size={50} color="#51B985" aria-hidden="true" />
          <h1>{hasNextLevel ? `أحسنت، أكملت ${LEVEL_NAMES[completedLevel]}` : "أحسنت، أكملت المستوى الثالث"}</h1>
          <p>{hasNextLevel ? `أنهيت أنشطة هذا المستوى بنجاح. خطوتك التالية هي ${nextLevelName}.` : "أنهيت رحلة التعلم حتى المستوى الثالث. سيظهر الاختبار البعدي عندما يفتحه المشرف."}</p>
          <Image className={styles.character} src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل بالإنجاز" width={180} height={220} />
          <button className={styles.primary} onClick={() => router.push("/student")}>{hasNextLevel ? "الانتقال إلى خطوتي التالية" : "العودة إلى مساري"}</button>
        </section></main>
      </div>
    );
  }

  if (error && !activity) {
    return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="error"><main className={styles.main}><section className={`${styles.card} ${styles.error}`}><h1>تعذر فتح النشاط</h1><p className={styles.errorMessage}>{error}</p><button className={styles.primary} onClick={() => void fetchNext()}>حاول مرة أخرى</button></section></main></div>;
  }

  if (!activity || !interaction) {
    return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="loading"><main className={styles.main}><section className={`${styles.card} ${styles.loading}`}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={112} height={38} /><div className="spinner w-12 h-12 border-4" /><p>جاري تجهيز النشاط...</p></section></main></div>;
  }

  const hasMediaGap = activity.step.media_gaps.length > 0;
  const imageChoice = interaction === "choose_image" || interaction === "listen_choose_image";
  const multiImageChoice = interaction === "choose_many" || interaction === "listen_choose_many";
  const displayPrompt = cleanPrompt(activity.step.prompt_text, interaction);
  const imageOptions = imageAssets.filter((asset) => asset.option_id);
  const imageOptionIds = new Set(imageOptions.map((asset) => Number(asset.option_id)));
  const sequenceHasCompleteImageCoverage = options.length > 0 && options.every((option) => imageOptionIds.has(option.id));
  const instruction = activity.step.instruction_text || "اقرأ المطلوب، ثم أكمل النشاط.";
  const retryHint = contextualHint(instruction, interaction);
  const helper = activity.retry ? retryHint : helperMessage(instruction, interaction, isReinforcement);
  const skillLabel = conciseTitle(activity.item.title);
  const memoryImagesComplete = interaction === "memory_sequence" && sequenceHasCompleteImageCoverage;

  if (interaction === "path_sequence") {
    return (
      <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="error">
        <main className={styles.main}><section className={`${styles.card} ${styles.error}`}>
          <h1>هذا النشاط استُبدل في النسخة الجديدة</h1>
          <p className={styles.errorMessage}>حدّث بيانات المحتوى ثم أعد فتح النشاط. لا نعرض نشاط المسار القديم للطالب.</p>
          <button className={styles.primary} onClick={() => void fetchNext()}>تحديث النشاط</button>
        </section></main>
      </div>
    );
  }

  return (
    <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="active" data-activity-kind={isReinforcement ? "reinforcement" : "core"}>
      <header className={styles.header}>
        <button className={styles.back} onClick={() => router.push("/student")} aria-label="العودة إلى مسار الطالب"><ArrowRight size={18} aria-hidden="true" /><span>رجوع</span></button>
        <div className={styles.progress} aria-label={`أكملت ${progress?.completed_items ?? 0} من ${progress?.total_items ?? 10} أنشطة`}><span style={{ width: `${percent}%` }} /></div>
        <span className={styles.counter} data-testid="activity-progress">{progress?.completed_items ?? 0} من {progress?.total_items ?? 10}</span>
      </header>

      <main className={styles.main}>
        <section className={styles.card}>
          <div className={styles.activityMeta}>
            <span className={styles.levelPill}>{skillLabel}</span>
            <span className={styles.roundPill}>{INTERACTION_LABEL[interaction]} · الجولة {activity.step.order_index}</span>
          </div>

          <div className={styles.helperRow} data-testid={activity.retry ? "contextual-hint" : "motivational-helper"} data-helper-state={activity.retry ? "retry" : "normal"}>
            <Image src={activity.retry ? "/characters/girl/encourage.png" : "/characters/girl/idle.png"} alt="شخصية هِمّة ترافق الطالب" width={95} height={120} />
            <p>{activity.retry ? <>جرّب مرة أخرى.<br />{helper}</> : helper}</p>
          </div>

          <h1 className={styles.title} data-testid="student-task-instruction">{instruction}</h1>
          {isReinforcement && <p className={styles.reinforcementIntro} data-testid="reinforcement-intro">تقوية موجهة لهذه المهارة، وبعد إتقانها تعود إلى نشاطك الأساسي.</p>}
          {displayPrompt && <div className={styles.prompt} data-testid="student-task-prompt">{displayPrompt}</div>}

          {contextAssets[0] && interaction !== "memory_sequence" && <div className={styles.contextImage}><Image src={contextAssets[0].url} alt={contextAssets[0].semantic_text || "صورة توضيحية للنشاط"} width={460} height={260} unoptimized /></div>}

          {LISTEN.has(interaction) && (
            <button className={`${styles.listenButton} ${isListening ? styles.listening : ""}`} onClick={() => void playPrompt()} disabled={isListening || !audioAssets.length} data-testid="activity-listen">
              <Volume2 size={27} aria-hidden="true" /><span>{isListening ? "يتم التشغيل" : "استمع"}</span>
            </button>
          )}

          {hasMediaGap && <div className={styles.gapNotice}><p>هذا الملف الصوتي غير متوفر ضمن الملفات المعتمدة حاليًا، لذلك لن تُحسب هذه الجولة عليك.</p><button className={styles.secondary} disabled={submitting} onClick={() => void submitStructured(true)}>متابعة دون احتساب الجولة</button></div>}

          {!hasMediaGap && interaction === "memory_sequence" && (
            <div data-testid="memory-stage" data-memory-phase={memoryPhase} className={styles.memoryStage}>
              {memoryPhase === "preview" ? (
                <>
                  <p className={styles.memoryLead}>شاهد الصور واحفظ ترتيبها</p>
                  <div className={styles.memoryPreview} data-testid="memory-preview">
                    {imageOptions.map((asset, index) => <div className={styles.memoryPreviewCard} key={`${asset.asset_id}-${index}`}><b>{index + 1}</b><Image src={asset.url} alt={asset.semantic_text || `الصورة ${index + 1}`} width={210} height={145} unoptimized /><span>{asset.semantic_text}</span></div>)}
                  </div>
                  <div className={styles.memoryCountdown} aria-live="polite">بعد لحظات ستختفي الصور…</div>
                </>
              ) : (
                <>
                  <p className={styles.memoryLead}>الآن أعد الصور بنفس ترتيب ظهورها</p>
                  <div className={styles.memorySlots} aria-label="ترتيبك الحالي">
                    {options.map((_, index) => {
                      const chosenId = selected[index];
                      const chosenAsset = imageOptions.find((asset) => Number(asset.option_id) === chosenId);
                      return <div className={`${styles.memorySlot} ${chosenAsset ? styles.memorySlotFilled : ""}`} key={index}><b>{index + 1}</b>{chosenAsset ? <Image src={chosenAsset.url} alt={chosenAsset.semantic_text || `اختيار ${index + 1}`} width={120} height={78} unoptimized /> : <span>اختر الصورة</span>}</div>;
                    })}
                  </div>
                  {memoryImagesComplete ? <div className={styles.memoryChoices} data-testid="memory-recall-options">{imageOptions.filter((asset) => !selected.includes(Number(asset.option_id))).map((asset) => <button key={asset.asset_id} className={styles.memoryChoice} onClick={() => toggleOption(Number(asset.option_id))}><Image src={asset.url} alt={asset.semantic_text || "صورة للتذكر"} width={180} height={120} unoptimized /><span>{asset.semantic_text}</span></button>)}</div> : <div className={styles.gapNotice}>صور هذا النشاط غير مكتملة، لذلك لن نعرض له قالب ترتيب نصي بديل.</div>}
                </>
              )}
            </div>
          )}

          {!hasMediaGap && interaction !== "memory_sequence" && (imageChoice || (multiImageChoice && imageOptions.length > 0)) && (
            <div className={styles.imageOptions} data-testid="activity-image-options">
              {imageOptions.map((asset) => {
                const optionId = Number(asset.option_id);
                const isSelected = selected.includes(optionId);
                return <button key={`${asset.asset_id}-${optionId}`} className={`${styles.imageOption} ${isSelected ? styles.imageOptionSelected : ""}`} onClick={() => toggleOption(optionId)} aria-pressed={isSelected}>{isSelected && <span className={styles.selectedMark}><Check size={16} /></span>}<Image src={asset.url} alt={asset.semantic_text || "خيار مصور"} width={220} height={150} unoptimized /><span>{asset.semantic_text || activity.step.options.find((option) => option.id === optionId)?.text}</span></button>;
              })}
            </div>
          )}

          {!hasMediaGap && interaction !== "memory_sequence" && (interaction === "sequence" || interaction === "build_word") && (
            <>
              <div className={styles.sequenceChosen} aria-label="ترتيبك الحالي">
                {selected.length === 0 && <span className={styles.sequenceHint}>{interaction === "build_word" ? "ابدأ بالحرف الأول، ثم أكمل الكلمة." : "ابدأ بما يحدث أولًا، ثم أكمل الترتيب."}</span>}
                {selected.map((id, index) => { const option = activity.step.options.find((candidate) => candidate.id === id); return <span className={styles.sequenceChip} key={`${id}-${index}`}><b>{index + 1}</b>{option?.text}</span>; })}
              </div>
              {interaction === "build_word" && imageAssets[0] && <div className={styles.contextImage}><Image src={imageAssets[0].url} alt={imageAssets[0].semantic_text || "صورة الكلمة"} width={360} height={220} unoptimized /></div>}
              {sequenceHasCompleteImageCoverage && interaction !== "build_word" ? <div className={styles.imageOptions} data-testid="sequence-image-options">{imageOptions.filter((asset) => !selected.includes(Number(asset.option_id))).map((asset) => <button key={asset.asset_id} className={styles.imageOption} onClick={() => toggleOption(Number(asset.option_id))}><Image src={asset.url} alt={asset.semantic_text || "عنصر ترتيب"} width={220} height={150} unoptimized /><span>{asset.semantic_text}</span></button>)}</div> : <div className={styles.options}>{options.filter((option) => !selected.includes(option.id)).map((option) => <button key={option.id} className={styles.option} onClick={() => toggleOption(option.id)}>{option.text}</button>)}</div>}
            </>
          )}

          {!hasMediaGap && !AUDIO.has(interaction) && !ORDER.has(interaction) && !(imageChoice || (multiImageChoice && imageOptions.length > 0)) && (
            <div className={styles.options}>{options.map((option) => { const isSelected = selected.includes(option.id); return <button key={option.id} className={`${styles.option} ${isSelected ? styles.optionSelected : ""}`} onClick={() => toggleOption(option.id)} aria-pressed={isSelected}>{option.text}</button>; })}</div>
          )}

          {!hasMediaGap && AUDIO.has(interaction) && (
            <>
              <div className={`${styles.readingText} ${(activity.step.expected_reading_text?.length || 0) > 55 ? styles.readingTextLong : ""}`} data-testid="activity-reading-text">{activity.step.expected_reading_text || "اقرأ النص الظاهر بصوت واضح"}</div>
              <div className={styles.recordPanel}>
                {!audioBlob ? <><button className={`${styles.recordCircle} ${isRecording ? styles.recording : ""}`} onClick={isRecording ? stopRecording : () => void startRecording()} aria-label={isRecording ? "إيقاف التسجيل" : "بدء التسجيل"}>{isRecording ? <MicOff size={30} /> : <Mic size={30} />}</button><strong>{isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط لبدء التسجيل"}</strong>{isRecording && <span className={styles.timer}>{String(Math.floor(recordingSeconds / 60)).padStart(2, "0")}:{String(recordingSeconds % 60).padStart(2, "0")}</span>}</> : <>{audioUrl && <audio className={styles.audioPreview} src={audioUrl} controls />}<p>استمع إلى تسجيلك، ثم أرسله أو أعد المحاولة.</p><div className={styles.actions}><button className={styles.secondary} onClick={() => { resetQuestionState(); startedAtRef.current = Date.now(); }}><RotateCcw size={17} /> إعادة التسجيل</button><button className={styles.primary} disabled={submitting} onClick={() => void uploadReading()}>{submitting ? "جاري الحفظ..." : "إرسال التسجيل"}</button></div></>}
              </div>
            </>
          )}

          {feedback && <p className={`${styles.feedback} ${feedback.ok ? styles.success : styles.retry}`} role="status">{feedback.text}</p>}
          {error && <p className={`${styles.feedback} ${styles.errorMessage}`} role="alert">{error}</p>}

          {!hasMediaGap && !AUDIO.has(interaction) && interaction !== "memory_sequence" && (
            <div className={styles.actions}>{ORDER.has(interaction) && selected.length > 0 && <button className={styles.secondary} disabled={submitting} onClick={() => setSelected([])}><RotateCcw size={17} /> إعادة الترتيب</button>}<button className={styles.primary} disabled={submitting || !readyToSubmit} onClick={() => void submitStructured(false)}>{submitting ? "جاري الحفظ..." : "تأكيد والمتابعة"}</button></div>
          )}
          {!hasMediaGap && interaction === "memory_sequence" && memoryPhase === "recall" && memoryImagesComplete && (
            <div className={styles.actions}><button className={styles.secondary} disabled={submitting || selected.length === 0} onClick={() => setSelected([])}><RotateCcw size={17} /> ابدأ الترتيب من جديد</button><button className={styles.primary} disabled={submitting || !readyToSubmit} onClick={() => void submitStructured(false)}>{submitting ? "جاري الحفظ..." : "تأكيد الترتيب"}</button></div>
          )}
        </section>
      </main>
    </div>
  );
}
