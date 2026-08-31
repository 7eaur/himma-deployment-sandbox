"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { Check, Mic, MicOff, RotateCcw, Volume2 } from "lucide-react";
import styles from "./session.module.css";

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

interface ContentOption { id: number; text: string; order_index: number; }
interface ContentAsset {
  asset_id: string;
  asset_type: string;
  usage?: string | null;
  semantic_text?: string | null;
  url: string;
  option_id?: number | null;
}
interface ContentStep {
  id: number;
  order_index: number;
  prompt_text: string;
  instruction_text?: string | null;
  expected_reading_text?: string | null;
  options: ContentOption[];
  assets: ContentAsset[];
  media_gaps: Array<{ semantic_text?: string; status?: string }>;
}
interface ContentItem {
  id: number;
  stable_key: string;
  canonical_id?: string | null;
  kind: string;
  interaction_type: Interaction;
  title?: string | null;
  source_method?: string | null;
  template_data?: { criterion?: string | null; [key: string]: unknown } | null;
  item_assets: ContentAsset[];
  steps: ContentStep[];
}
interface ProgressPayload {
  completed_items: number;
  total_items: number;
  completed_steps: number;
  total_steps: number;
  has_pending_item: boolean;
  elapsed_seconds: number;
}

type Phase = "loading" | "active" | "submitting" | "finishing" | "waiting" | "done" | "error";

const SINGLE = new Set<Interaction>(["choose_one", "listen_choose_one", "choose_image", "listen_choose_image"]);
const MULTI = new Set<Interaction>(["choose_many", "listen_choose_many"]);
const ORDER = new Set<Interaction>(["sequence", "memory_sequence", "path_sequence", "build_word"]);
const LISTEN = new Set<Interaction>(["listen_choose_one", "listen_choose_image", "listen_choose_many"]);
const READ = new Set<Interaction>(["read_aloud", "timed_read_aloud"]);
const LEVEL_LABELS = ["الاستعداد للقراءة", "بناء الكلمة", "الطلاقة والفهم"];

function conciseTitle(title?: string | null) {
  if (!title) return "مهمة قصيرة";
  const value = title.includes(":") ? title.split(":").slice(1).join(":").trim() : title;
  return value.replace(/^السؤال\s+\d+\s*/u, "").trim() || "مهمة قصيرة";
}

function cleanPrompt(raw: string, interaction: Interaction) {
  if (LISTEN.has(interaction) || READ.has(interaction) || ORDER.has(interaction)) return "";
  let value = raw.replace(/^التعليمات:\s*/u, "");
  value = value.split(/الخيارات:|الصور:/u)[0].trim();
  if (value.startsWith("العناصر:") && value.includes("التعليمات:")) {
    value = value.split("التعليمات:")[1]?.trim() || value;
  }
  return value;
}

function criterionCount(item: ContentItem, optionsLength: number) {
  const criterion = String(item.template_data?.criterion || "").trim();
  if (!criterion || criterion === "بالترتيب المذكور") return optionsLength;
  const parts = criterion.split(/\s+ثم\s+|[،,]/u).map((part) => part.trim()).filter(Boolean);
  return parts.length ? Math.min(parts.length, optionsLength) : optionsLength;
}

function stableOptionOrder(values: ContentOption[]) {
  return [...values].sort((a, b) => ((a.id * 17) % 97) - ((b.id * 17) % 97));
}

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = String(params.id);

  const [phase, setPhase] = useState<Phase>("loading");
  const [item, setItem] = useState<ContentItem | null>(null);
  const [progress, setProgress] = useState<ProgressPayload | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [error, setError] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [finalScore, setFinalScore] = useState<number | null>(null);
  const [assignedLevel, setAssignedLevel] = useState<number | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stepStartedAtRef = useRef(0);
  const playbackRef = useRef<HTMLAudioElement | null>(null);

  const step = item?.steps[0] ?? null;
  const interaction = item?.interaction_type;
  const options = useMemo(() => stableOptionOrder(step?.options ?? []), [step]);
  const audioAssets = useMemo(() => step?.assets.filter((asset) => asset.asset_type === "audio") ?? [], [step]);
  const imageAssets = useMemo(() => step?.assets.filter((asset) => asset.asset_type === "image") ?? [], [step]);
  const contextAssets = useMemo(() => item?.item_assets.filter((asset) => asset.asset_type === "image") ?? [], [item]);
  const answered = progress?.completed_items ?? 0;
  const total = progress?.total_items || 30;
  const percent = Math.min(100, Math.round((answered / Math.max(1, total)) * 100));
  const targetCount = item && step ? criterionCount(item, step.options.length) : 0;

  const operationKey = (kind: "answer" | "upload") => {
    if (!item || !step) return "";
    return `himma:assessment:${sessionId}:${item.id}:${step.id}:${kind}`;
  };

  const getIdempotencyKey = (kind: "answer" | "upload") => {
    const key = operationKey(kind);
    if (!key) return crypto.randomUUID();
    const existing = window.sessionStorage.getItem(key);
    if (existing) return existing;
    const created = crypto.randomUUID();
    window.sessionStorage.setItem(key, created);
    return created;
  };

  const clearOperationKeys = () => {
    for (const kind of ["answer", "upload"] as const) {
      const key = operationKey(kind);
      if (key) window.sessionStorage.removeItem(key);
    }
  };

  const clearQuestionState = () => {
    setSelectedIds([]);
    setAudioBlob(null);
    setAudioUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
    setRecordingSeconds(0);
    setError("");
  };

  const fetchProgress = useCallback(async () => {
    const response = await fetch(`/api/assessment/session/${sessionId}/progress`, { cache: "no-store" });
    if (response.ok) setProgress(await response.json());
  }, [sessionId]);

  const finishSession = useCallback(async () => {
    setPhase("finishing");
    setError("");
    try {
      const response = await fetch(`/api/assessment/session/${sessionId}/finish`, { method: "POST" });
      const data = await response.json().catch(() => null);
      const detail = typeof data?.detail === "string" ? data.detail : "";
      if (response.status === 409 && detail.includes("انتظار المراجعة")) {
        setPhase("waiting");
        return;
      }
      if (!response.ok) throw new Error(detail || "تعذر إنهاء الاختبار");
      setFinalScore(Number(data.final_score));
      setAssignedLevel(Number(data.assigned_level));
      setPhase("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر إنهاء الاختبار");
      setPhase("error");
    }
  }, [sessionId]);

  const fetchNext = useCallback(async () => {
    setPhase("loading");
    setError("");
    try {
      const response = await fetch(`/api/assessment/session/${sessionId}/next`, { cache: "no-store" });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تحميل السؤال");
      if (!data) {
        await finishSession();
        return;
      }
      setItem(data);
      setSelectedIds([]);
      setAudioBlob(null);
      setAudioUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return null;
      });
      setRecordingSeconds(0);
      stepStartedAtRef.current = Date.now();
      await fetchProgress();
      setPhase("active");
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل السؤال");
      setPhase("error");
    }
  }, [fetchProgress, finishSession, sessionId]);

  useEffect(() => {
    const kickoff = window.setTimeout(() => void fetchNext(), 0);
    return () => {
      window.clearTimeout(kickoff);
      if (timerRef.current) clearInterval(timerRef.current);
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      playbackRef.current?.pause();
    };
  }, [fetchNext]);

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

  const toggleOption = (optionId: number) => {
    if (!interaction || phase !== "active") return;
    setError("");
    if (SINGLE.has(interaction)) {
      setSelectedIds([optionId]);
      return;
    }
    if (MULTI.has(interaction)) {
      setSelectedIds((current) => current.includes(optionId) ? current.filter((id) => id !== optionId) : [...current, optionId]);
      return;
    }
    if (ORDER.has(interaction)) {
      setSelectedIds((current) => {
        if (current.includes(optionId)) return current;
        if (targetCount > 0 && current.length >= targetCount) return current;
        return [...current, optionId];
      });
    }
  };

  const submitAnswer = async () => {
    if (!item || !step || !interaction) return;
    setPhase("submitting");
    setError("");
    const elapsed = Math.min(3600, Math.max(0, Math.floor((Date.now() - stepStartedAtRef.current) / 1000)));
    try {
      const body: Record<string, unknown> = { step_id: step.id, elapsed_seconds: elapsed };
      if (SINGLE.has(interaction)) body.selected_option_id = selectedIds[0];
      if (MULTI.has(interaction) || ORDER.has(interaction)) body.selected_option_ids = selectedIds;
      const response = await fetch(`/api/assessment/session/${sessionId}/attempt/${item.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": getIdempotencyKey("answer") },
        body: JSON.stringify(body),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر حفظ الإجابة");
      clearOperationKeys();
      await fetchProgress();
      await fetchNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ الإجابة");
      setPhase("active");
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
        setAudioUrl((current) => {
          if (current) URL.revokeObjectURL(current);
          return URL.createObjectURL(blob);
        });
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
    if (!item || !step || !audioBlob) return;
    setPhase("submitting");
    setError("");
    try {
      const form = new FormData();
      form.append("file", audioBlob, "assessment-reading.webm");
      const upload = await fetch(`/api/assessment/session/${sessionId}/upload-audio`, {
        method: "POST",
        headers: { "Idempotency-Key": getIdempotencyKey("upload") },
        body: form,
      });
      const uploaded = await upload.json().catch(() => null);
      if (!upload.ok) throw new Error(uploaded?.detail || "تعذر رفع التسجيل");
      const elapsed = Math.min(3600, Math.max(0, Math.floor((Date.now() - stepStartedAtRef.current) / 1000)));
      const submit = await fetch(`/api/assessment/session/${sessionId}/attempt/${item.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": getIdempotencyKey("answer") },
        body: JSON.stringify({
          step_id: step.id,
          audio_storage_key: uploaded.audio_storage_key,
          audio_file_size: uploaded.audio_file_size,
          audio_mime_type: uploaded.audio_mime_type,
          audio_duration_seconds: recordingSeconds,
          elapsed_seconds: elapsed,
        }),
      });
      const data = await submit.json().catch(() => null);
      if (!submit.ok) throw new Error(data?.detail || "تعذر حفظ القراءة");
      clearOperationKeys();
      await fetchProgress();
      await fetchNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ القراءة");
      setPhase("active");
    }
  };

  if (phase === "done" && assignedLevel !== null) {
    return (
      <div className={styles.resultPage} dir="rtl" data-testid="assessment-session" data-phase="done">
        <div className={styles.resultCard}>
          <div className={styles.resultContent}>
            <span className={styles.badge}><Check size={16} /> اكتمل الاختبار</span>
            <h1 className={styles.title}>أحسنت، أكملت المهمة!</h1>
            <p className={styles.instruction}>تم حفظ إجاباتك وقراءتك. هِمّة ستقودك الآن إلى المسار الأنسب لك.</p>
            <div className={styles.score}>{Math.round(finalScore || 0)}%</div>
            <p className="font-bold text-navy mb-6">مستواك: {LEVEL_LABELS[Math.max(0, assignedLevel - 1)] || assignedLevel}</p>
            <button className={styles.primary} onClick={() => router.push("/student")}>متابعة رحلتي</button>
          </div>
          <div className={styles.resultVisual}><Image src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل بالإنجاز" width={340} height={410} priority /></div>
        </div>
      </div>
    );
  }

  if (phase === "waiting") {
    return (
      <div className={styles.resultPage} dir="rtl" data-testid="assessment-session" data-phase="waiting_audio_review">
        <div className={styles.resultCard}>
          <div className={styles.resultContent}>
            <span className={styles.badge}>تم حفظ إجاباتك</span>
            <h1 className={styles.title}>عمل رائع</h1>
            <p className={styles.instruction}>أنهيت الأسئلة. سيُراجع المشرف تسجيلات القراءة، وبعدها تظهر النتيجة بشكل صحيح.</p>
            <button className={styles.primary} onClick={() => router.push("/student")}>العودة إلى مساري</button>
          </div>
          <div className={styles.resultVisual}><Image src="/characters/girl/encourage.png" alt="شخصية هِمّة تشجع الطالب" width={330} height={400} /></div>
        </div>
      </div>
    );
  }

  if (phase === "finishing" || phase === "loading") {
    return (
      <div className={styles.page} dir="rtl" data-testid="assessment-session" data-phase={phase}>
        <div className="min-h-screen flex flex-col items-center justify-center gap-4">
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={120} height={42} />
          <div className="spinner w-12 h-12 border-4" />
          <p className="text-muted">{phase === "finishing" ? "جاري إنهاء الاختبار..." : "جاري تجهيز المهمة التالية..."}</p>
        </div>
      </div>
    );
  }

  if (phase === "error" || !item || !step || !interaction) {
    return (
      <div className={styles.page} dir="rtl" data-testid="assessment-session" data-phase="error">
        <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-6 text-center">
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={120} height={42} />
          <h1 className="text-2xl font-bold text-navy">تعذر فتح المهمة</h1>
          <p className="text-muted max-w-lg">{error || "حدث خطأ غير متوقع."}</p>
          <button className={styles.primary} onClick={() => void fetchNext()}>حاول مرة أخرى</button>
        </div>
      </div>
    );
  }

  const displayPrompt = cleanPrompt(step.prompt_text, interaction);
  const hasMediaGap = step.media_gaps.length > 0;
  const imageChoice = interaction === "choose_image" || interaction === "listen_choose_image";
  const sequenceWithImages = ORDER.has(interaction) && imageAssets.some((asset) => asset.option_id);
  const canSubmit = Boolean(
    (SINGLE.has(interaction) && selectedIds.length === 1)
    || (MULTI.has(interaction) && selectedIds.length >= 2)
    || (ORDER.has(interaction) && selectedIds.length === targetCount),
  );
  const sideCharacter = READ.has(interaction) ? "/characters/girl/encourage.png" : "/characters/girl/explain.png";

  return (
    <div className={styles.page} dir="rtl" data-testid="assessment-session" data-phase={phase === "submitting" ? "submitting" : "question"}>
      <header className={styles.topbar}>
        <div className={styles.logo}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={112} height={38} priority /></div>
        <div className={styles.progressWrap}>
          <div className={styles.progressMeta}><span>{conciseTitle(item.title)}</span><span>{Math.min(answered + 1, total)} من {total}</span></div>
          <div className={styles.progressTrack}><div className={styles.progressFill} style={{ width: `${percent}%` }} /></div>
        </div>
        <button className={styles.exit} onClick={() => router.push("/student")}>خروج</button>
      </header>

      <main className={styles.shell}>
        <section className={styles.card}>
          <h1 className={styles.title}>{step.instruction_text || conciseTitle(item.title)}</h1>
          <p className={styles.instruction}>{conciseTitle(item.title)}</p>
          {displayPrompt && <div className={styles.prompt}>{displayPrompt}</div>}

          {contextAssets[0] && (
            <div className={styles.contextImage}><Image src={contextAssets[0].url} alt={contextAssets[0].semantic_text || "صورة توضيحية"} width={460} height={250} unoptimized /></div>
          )}

          {LISTEN.has(interaction) && (
            <button className={`${styles.listenButton} ${isListening ? styles.listenPulse : ""}`} onClick={() => void playPrompt()} disabled={isListening || !audioAssets.length} data-testid="listen-prompt">
              <Volume2 size={26} aria-hidden="true" /><span>استمع</span>
            </button>
          )}

          {hasMediaGap && <div className={styles.notice}>هذا الصوت غير متوفر ضمن الملفات المعتمدة حاليًا، لذلك لن يُطلب منك الإجابة على هذه المهمة الآن.</div>}

          {!hasMediaGap && imageChoice && (
            <div className={styles.imageOptions} data-testid="image-options">
              {imageAssets.filter((asset) => asset.option_id).map((asset) => {
                const optionId = Number(asset.option_id);
                const selected = selectedIds.includes(optionId);
                return (
                  <button key={`${asset.asset_id}-${optionId}`} className={`${styles.imageOption} ${selected ? styles.imageOptionSelected : ""}`} onClick={() => toggleOption(optionId)} aria-pressed={selected}>
                    {selected && <span className={styles.selectedMark}><Check size={16} /></span>}
                    <Image src={asset.url} alt={asset.semantic_text || "خيار مصور"} width={220} height={150} unoptimized />
                    <span className={styles.imageLabel}>{asset.semantic_text || step.options.find((option) => option.id === optionId)?.text}</span>
                  </button>
                );
              })}
            </div>
          )}

          {!hasMediaGap && ORDER.has(interaction) && (
            <>
              <div className={styles.sequenceBoard} data-testid="sequence-board">
                {!selectedIds.length && <span className={styles.sequenceHint}>{interaction === "build_word" ? "اضغط الحروف بالترتيب لتكوين الكلمة" : "اضغط العناصر بالترتيب الصحيح"}</span>}
                {selectedIds.map((id, index) => {
                  const option = step.options.find((candidate) => candidate.id === id);
                  return <span className={styles.sequenceChip} key={`${id}-${index}`}><span className={styles.number}>{index + 1}</span>{option?.text}</span>;
                })}
              </div>

              {interaction === "build_word" && imageAssets[0] && (
                <div className={styles.contextImage}><Image src={imageAssets[0].url} alt={imageAssets[0].semantic_text || "صورة الكلمة"} width={340} height={200} unoptimized /></div>
              )}

              {sequenceWithImages && interaction !== "build_word" ? (
                <div className={styles.imageOptions} data-testid="sequence-image-options">
                  {imageAssets.filter((asset) => asset.option_id && !selectedIds.includes(Number(asset.option_id))).map((asset) => (
                    <button key={asset.asset_id} className={styles.imageOption} onClick={() => toggleOption(Number(asset.option_id))} disabled={targetCount > 0 && selectedIds.length >= targetCount}>
                      <Image src={asset.url} alt={asset.semantic_text || "عنصر ترتيب"} width={220} height={150} unoptimized />
                      <span className={styles.imageLabel}>{asset.semantic_text}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <div className={styles.options}>
                  {options.filter((option) => !selectedIds.includes(option.id)).map((option) => (
                    <button key={option.id} className={styles.option} onClick={() => toggleOption(option.id)} disabled={targetCount > 0 && selectedIds.length >= targetCount}>{option.text}</button>
                  ))}
                </div>
              )}
            </>
          )}

          {!hasMediaGap && !READ.has(interaction) && !ORDER.has(interaction) && !imageChoice && (
            <div className={styles.options}>
              {options.map((option) => {
                const selected = selectedIds.includes(option.id);
                return <button key={option.id} className={`${styles.option} ${selected ? styles.optionSelected : ""}`} onClick={() => toggleOption(option.id)} aria-pressed={selected}>{option.text}</button>;
              })}
            </div>
          )}

          {!hasMediaGap && READ.has(interaction) && (
            <>
              <div className={`${styles.readingBox} ${(step.expected_reading_text?.length || 0) > 55 ? styles.readingBoxLong : ""}`} data-testid="reading-text">{step.expected_reading_text || "اقرأ النص الظاهر"}</div>
              <div className={styles.recordPanel}>
                {!audioBlob ? (
                  <>
                    <button className={`${styles.recordButton} ${isRecording ? styles.recordButtonRecording : ""}`} onClick={isRecording ? stopRecording : () => void startRecording()} aria-label={isRecording ? "إيقاف التسجيل" : "بدء التسجيل"} data-testid="record-reading">
                      {isRecording ? <MicOff size={30} /> : <Mic size={30} />}
                    </button>
                    <p className="font-bold text-navy">{isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط لبدء التسجيل"}</p>
                    {isRecording && <p className={styles.timer}>{String(Math.floor(recordingSeconds / 60)).padStart(2, "0")}:{String(recordingSeconds % 60).padStart(2, "0")}</p>}
                  </>
                ) : (
                  <>
                    {audioUrl && <audio className={styles.audioPreview} src={audioUrl} controls />}
                    <p className="text-sm text-muted">استمع إلى تسجيلك، ثم أرسله أو أعد المحاولة.</p>
                    <div className={styles.actions}>
                      <button className={styles.secondary} onClick={() => { clearQuestionState(); stepStartedAtRef.current = Date.now(); }}><RotateCcw size={17} /> إعادة التسجيل</button>
                      <button className={styles.primary} onClick={() => void uploadReading()} disabled={phase === "submitting"}>إرسال التسجيل</button>
                    </div>
                  </>
                )}
              </div>
            </>
          )}

          {error && <div className={styles.error} role="alert">{error}</div>}

          {!hasMediaGap && !READ.has(interaction) && (
            <div className={styles.actions}>
              {ORDER.has(interaction) && selectedIds.length > 0 && <button className={styles.secondary} onClick={() => setSelectedIds([])}><RotateCcw size={17} /> إعادة الترتيب</button>}
              <button className={styles.primary} onClick={() => void submitAnswer()} disabled={!canSubmit || phase === "submitting"}>{phase === "submitting" ? "جاري الحفظ..." : "تأكيد والمتابعة"}</button>
            </div>
          )}
        </section>

        <aside className={styles.side} aria-label="نصيحة هِمّة">
          <div className={styles.tip}>{READ.has(interaction) ? "اقرأ بهدوء وبصوت طبيعي. لا تحتاج إلى السرعة؛ المهم أن تكون القراءة واضحة." : LISTEN.has(interaction) ? "يمكنك الاستماع مرة أخرى قبل اختيار الإجابة." : "خذ وقتك، ركّز في المهمة، ثم اختر ما تراه صحيحًا."}</div>
          <Image className={styles.character} src={sideCharacter} alt="شخصية هِمّة المساعدة" width={190} height={260} />
        </aside>
      </main>
    </div>
  );
}