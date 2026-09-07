"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { Check, ClipboardList, Info, LogOut, Mic, MicOff, Pause, Play, RotateCcw, Star, Target, Volume2 } from "lucide-react";
import { classifyStudentRecovery, playFeedbackSound, shuffleForPresentation, type StudentRecoveryAction } from "../../../../lib/student-experience";
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

type PlaybackState = "idle" | "playing" | "paused";

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
  expected_reading_text?: string | null;
  required_selection_count: number;
  options: ContentOption[];
  assets: ContentAsset[];
  media_gaps: Array<{ semantic_text?: string; status?: string }>;
}
interface AssessmentPresentation {
  version: string;
  question_number: number;
  section: string;
  skill: string;
  encouragement: string;
  question_text: string;
  instruction_text: string;
  interaction_type: Interaction;
  stimulus: {
    kind?: "text" | "reading" | "audio" | "image" | "reference" | "none" | string;
    text?: string | null;
    audio_target?: string | null;
  };
  media_semantics?: { option_kind?: string; stimulus?: string } | null;
}
interface ContentItem {
  id: number;
  stable_key: string;
  canonical_id?: string | null;
  kind: "pretest_question" | "posttest_question";
  interaction_type: Interaction;
  title?: string | null;
  presentation: AssessmentPresentation;
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

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = String(params.id);
  const [phase, setPhase] = useState<Phase>("loading");
  const [item, setItem] = useState<ContentItem | null>(null);
  const [progress, setProgress] = useState<ProgressPayload | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [error, setError] = useState("");
  const [errorAction, setErrorAction] = useState<StudentRecoveryAction>("retry");
  const [playbackState, setPlaybackState] = useState<PlaybackState>("idle");
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
  const recordingPreviewRef = useRef<HTMLAudioElement | null>(null);

  const step = item?.steps[0] ?? null;
  const interaction = item?.interaction_type;
  const presentation = item?.presentation;
  const options = useMemo(() => shuffleForPresentation(step?.options ?? []), [step]);
  const audioAssets = useMemo(() => step?.assets.filter((asset) => asset.asset_type === "audio") ?? [], [step]);
  const imageAssets = useMemo(() => step?.assets.filter((asset) => asset.asset_type === "image") ?? [], [step]);
  const contextAssets = useMemo(() => item?.item_assets.filter((asset) => asset.asset_type === "image") ?? [], [item]);
  const optionRank = useMemo(() => new Map(options.map((option, index) => [option.id, index])), [options]);
  const imageOptions = useMemo(
    () => imageAssets.filter((asset) => asset.option_id).sort((a, b) => (optionRank.get(Number(a.option_id)) ?? 999) - (optionRank.get(Number(b.option_id)) ?? 999)),
    [imageAssets, optionRank],
  );
  const answered = progress?.completed_items ?? 0;
  const total = progress?.total_items || 30;
  const currentNumber = presentation?.question_number ?? Math.min(answered + 1, total);
  const percent = Math.min(100, Math.round((answered / Math.max(1, total)) * 100));
  const targetCount = step?.required_selection_count ?? 0;

  const stopPrompt = useCallback(() => {
    const audio = playbackRef.current;
    if (audio) {
      audio.onended = null;
      audio.onerror = null;
      audio.pause();
      audio.currentTime = 0;
    }
    playbackRef.current = null;
    setPlaybackState("idle");
  }, []);

  const stopRecordedPreview = useCallback(() => {
    const preview = recordingPreviewRef.current;
    if (preview) {
      preview.pause();
      preview.currentTime = 0;
    }
  }, []);

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

  const clearQuestionState = useCallback(() => {
    stopPrompt();
    stopRecordedPreview();
    setSelectedIds([]);
    setAudioBlob(null);
    setAudioUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
    setRecordingSeconds(0);
    setError("");
  }, [stopPrompt, stopRecordedPreview]);

  const fetchProgress = useCallback(async () => {
    const response = await fetch(`/api/assessment/session/${sessionId}/progress`, { cache: "no-store" });
    if (response.ok) setProgress(await response.json());
  }, [sessionId]);

  const finishSession = useCallback(async () => {
    stopPrompt();
    stopRecordedPreview();
    setPhase("finishing");
    setError("");
    setErrorAction("retry");
    try {
      const response = await fetch(`/api/assessment/session/${sessionId}/finish`, { method: "POST" });
      const data = await response.json().catch(() => null);
      const detail = typeof data?.detail === "string" ? data.detail : "";
      if (response.status === 409 && detail.includes("انتظار المراجعة")) {
        setPhase("waiting");
        return;
      }
      if (!response.ok) {
        const recovery = classifyStudentRecovery(response.status, detail);
        if (recovery === "login") {
          router.replace(`/student/login?next=${encodeURIComponent(`/student/session/${sessionId}`)}`);
          return;
        }
        setError(detail || "تعذر إنهاء الاختبار");
        setErrorAction(recovery);
        setPhase("error");
        return;
      }
      setFinalScore(Number(data.final_score));
      setAssignedLevel(Number(data.assigned_level));
      playFeedbackSound("complete");
      setPhase("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر إنهاء الاختبار");
      setErrorAction("retry");
      setPhase("error");
    }
  }, [router, sessionId, stopPrompt, stopRecordedPreview]);

  const fetchNext = useCallback(async () => {
    stopPrompt();
    stopRecordedPreview();
    setPhase("loading");
    setError("");
    setErrorAction("retry");
    try {
      const response = await fetch(`/api/assessment-view/session/${sessionId}/next`, { cache: "no-store" });
      const data = await response.json().catch(() => null);
      const detail = typeof data?.detail === "string" ? data.detail : "";
      if (response.status === 409 && detail.includes("انتظار المراجعة")) {
        setPhase("waiting");
        return;
      }
      if (!response.ok) {
        const recovery = classifyStudentRecovery(response.status, detail);
        if (recovery === "login") {
          router.replace(`/student/login?next=${encodeURIComponent(`/student/session/${sessionId}`)}`);
          return;
        }
        setError(detail || "تعذر تحميل السؤال");
        setErrorAction(recovery);
        setPhase("error");
        setItem(null);
        return;
      }
      if (!data) {
        await finishSession();
        return;
      }
      setItem(data);
      clearQuestionState();
      stepStartedAtRef.current = Date.now();
      await fetchProgress();
      setPhase("active");
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل السؤال");
      setErrorAction("retry");
      setPhase("error");
      setItem(null);
    }
  }, [clearQuestionState, fetchProgress, finishSession, router, sessionId, stopPrompt, stopRecordedPreview]);

  useEffect(() => {
    const kickoff = window.setTimeout(() => void fetchNext(), 0);
    return () => {
      window.clearTimeout(kickoff);
      if (timerRef.current) clearInterval(timerRef.current);
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      const audio = playbackRef.current;
      if (audio) {
        audio.onended = null;
        audio.onerror = null;
        audio.pause();
      }
      const preview = recordingPreviewRef.current;
      if (preview) preview.pause();
    };
  }, [fetchNext]);

  const playAssetAt = useCallback((index: number) => {
    if (index >= audioAssets.length) {
      stopPrompt();
      return;
    }
    const audio = new Audio(audioAssets[index].url);
    audio.volume = 1;
    playbackRef.current = audio;
    audio.onended = () => playAssetAt(index + 1);
    audio.onerror = () => {
      stopPrompt();
      setError("تعذر تشغيل الصوت. تحقق من مستوى الصوت في الجهاز ثم حاول مرة أخرى.");
    };
    setPlaybackState("playing");
    void audio.play().catch(() => {
      stopPrompt();
      setError("تعذر تشغيل الصوت. تحقق من مستوى الصوت في الجهاز ثم حاول مرة أخرى.");
    });
  }, [audioAssets, stopPrompt]);

  const togglePromptPlayback = () => {
    const audio = playbackRef.current;
    if (playbackState === "playing" && audio) {
      audio.pause();
      setPlaybackState("paused");
      return;
    }
    if (playbackState === "paused" && audio) {
      void audio.play().then(() => setPlaybackState("playing")).catch(() => setError("تعذر استئناف الصوت. حاول مرة أخرى."));
      return;
    }
    setError("");
    playAssetAt(0);
  };

  const toggleOption = (optionId: number) => {
    if (!interaction || phase !== "active") return;
    setError("");
    if (SINGLE.has(interaction)) {
      setSelectedIds([optionId]);
      return;
    }
    if (MULTI.has(interaction)) {
      setSelectedIds((current) => {
        if (current.includes(optionId)) return current.filter((id) => id !== optionId);
        if (targetCount > 0 && current.length >= targetCount) return current;
        return [...current, optionId];
      });
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
    stopPrompt();
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
      playFeedbackSound("transition");
      await fetchProgress();
      await fetchNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ الإجابة");
      setPhase("active");
    }
  };

  const startRecording = async () => {
    stopPrompt();
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
    stopRecordedPreview();
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
      playFeedbackSound("transition");
      await fetchProgress();
      await fetchNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ القراءة");
      setPhase("active");
    }
  };

  const recoverFromError = () => {
    if (errorAction === "dashboard") {
      router.replace("/student");
      return;
    }
    if (errorAction === "login") {
      router.replace(`/student/login?next=${encodeURIComponent(`/student/session/${sessionId}`)}`);
      return;
    }
    void fetchNext();
  };

  if (phase === "done" && assignedLevel !== null) {
    return (
      <div className={styles.resultPage} dir="rtl" data-testid="assessment-session" data-phase="done">
        <div className={styles.resultCard}>
          <div className={styles.resultContent}>
            <span className={styles.resultBadge}><Check size={18} /> اكتمل الاختبار</span>
            <h1 className={styles.resultTitle}>أحسنت، أكملت المهمة!</h1>
            <p className={styles.resultText}>تم حفظ إجاباتك وقراءتك. هِمّة ستقودك الآن إلى المسار الأنسب لك.</p>
            <div className={styles.score}>{Math.round(finalScore || 0)}%</div>
            <p className={styles.resultLevel}>مستواك: {LEVEL_LABELS[Math.max(0, assignedLevel - 1)] || assignedLevel}</p>
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
            <span className={styles.resultBadge}>تم حفظ تسجيلك</span>
            <h1 className={styles.resultTitle}>عمل رائع</h1>
            <p className={styles.resultText}>تم حفظ تسجيلك. سيُراجع المشرف القراءة، وبعد اعتمادها يمكنك متابعة الاختبار من نفس المكان.</p>
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
        <div className={styles.loadingState}>
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={128} height={46} priority />
          <div className={styles.spinner} />
          <p>{phase === "finishing" ? "جاري إنهاء الاختبار..." : "جاري تجهيز السؤال التالي..."}</p>
        </div>
      </div>
    );
  }

  if (phase === "error" || !item || !step || !interaction || !presentation) {
    const label = errorAction === "retry" ? "حاول مرة أخرى" : errorAction === "login" ? "تسجيل الدخول" : "العودة إلى مساري";
    return (
      <div className={styles.page} dir="rtl" data-testid="assessment-session" data-phase="error">
        <div className={styles.loadingState}>
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={128} height={46} />
          <h1>تعذر فتح السؤال</h1>
          <p>{error || "هذا السؤال لم يعد متاحًا من هذا الرابط."}</p>
          <button className={styles.primary} onClick={recoverFromError}>{label}</button>
        </div>
      </div>
    );
  }

  const questionText = presentation.question_text;
  const skillText = presentation.skill;
  const instructionText = presentation.instruction_text;
  const encouragement = presentation.encouragement;
  const stimulusKind = presentation.stimulus?.kind || "none";
  const stimulusText = String(presentation.stimulus?.text || "");
  const hasMediaGap = step.media_gaps.length > 0;
  const imageChoice = interaction === "choose_image" || interaction === "listen_choose_image";
  const sequenceWithImages = ORDER.has(interaction) && imageOptions.length > 0;
  const canSubmit = Boolean(
    (SINGLE.has(interaction) && selectedIds.length === 1)
    || (MULTI.has(interaction) && targetCount > 0 && selectedIds.length === targetCount)
    || (ORDER.has(interaction) && targetCount > 0 && selectedIds.length === targetCount),
  );
  const visualAsset = contextAssets[0] || (stimulusKind === "image" ? imageAssets.find((asset) => !asset.option_id) || imageAssets[0] : undefined);
  const sideCharacter = READ.has(interaction) ? "/characters/girl/encourage.png" : "/characters/girl/explain.png";
  const assessmentLabel = item.kind === "pretest_question" ? "الاختبار القبلي" : "الاختبار البعدي";
  const listenLabel = playbackState === "playing" ? "إيقاف مؤقت" : playbackState === "paused" ? "متابعة" : "استمع";
  const listenIcon = playbackState === "playing" ? <Pause size={34} aria-hidden="true" /> : playbackState === "paused" ? <Play size={34} aria-hidden="true" /> : <Volume2 size={34} aria-hidden="true" />;

  return (
    <div className={styles.page} dir="rtl" data-testid="assessment-session" data-phase={phase === "submitting" ? "submitting" : "question"}>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.brandCluster}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={124} height={44} priority /></div>
          <button className={styles.exit} type="button" onClick={() => { stopPrompt(); stopRecordedPreview(); router.push("/student"); }}><LogOut size={21} /><span>خروج</span></button>
        </div>
      </header>

      <div className={styles.progressPanel}>
        <div className={styles.progressTop}>
          <span className={styles.assessmentBadge}><ClipboardList size={20} />{assessmentLabel}</span>
          <span className={styles.progressCount}>{currentNumber} من {total}</span>
        </div>
        <div className={styles.progressTrack} aria-label={`التقدم ${percent}%`}><div className={styles.progressFill} style={{ width: `${Math.max(percent, 2)}%` }} /></div>
      </div>

      <main className={styles.shell}>
        <section className={styles.card}>
          <div className={styles.skillChip}><Target size={19} />{skillText}</div>
          <div className={styles.contentColumn}>
            <h1 className={styles.questionTitle} data-testid="question-title">{questionText}</h1>

            {!LISTEN.has(interaction) && !READ.has(interaction) && stimulusKind === "text" && stimulusText && (
              <div className={`${styles.stimulusBox} ${stimulusText.length <= 3 ? styles.letterStimulus : ""}`} data-testid="question-stimulus">{stimulusText}</div>
            )}

            {visualAsset && (
              <div className={styles.contextImage} data-testid="question-image">
                <Image src={visualAsset.url} alt={visualAsset.semantic_text || presentation.media_semantics?.stimulus || "صورة مرتبطة بالسؤال"} width={420} height={260} unoptimized />
              </div>
            )}

            {LISTEN.has(interaction) && (
              <button className={`${styles.listenButton} ${playbackState === "playing" ? styles.listenPulse : ""}`} onClick={togglePromptPlayback} disabled={!audioAssets.length} data-testid="listen-prompt" type="button" aria-label={listenLabel}>
                {listenIcon}<span>{listenLabel}</span>
              </button>
            )}

            {READ.has(interaction) && (
              <div className={`${styles.readingBox} ${(step.expected_reading_text?.length || stimulusText.length) > 55 ? styles.readingBoxLong : ""}`} data-testid="reading-text">{step.expected_reading_text || stimulusText}</div>
            )}

            <div className={styles.instructionRow}><Info size={21} aria-hidden="true" /><p>{instructionText}</p></div>
            {hasMediaGap && <div className={styles.notice}>هذا الملف غير متوفر ضمن الوسائط المعتمدة حاليًا، لذلك لن يُطلب منك الإجابة على هذه المهمة الآن.</div>}

            {!hasMediaGap && imageChoice && (
              <div className={styles.imageOptions} data-testid="image-options">
                {imageOptions.map((asset) => {
                  const optionId = Number(asset.option_id);
                  const selected = selectedIds.includes(optionId);
                  return (
                    <button key={`${asset.asset_id}-${optionId}`} className={`${styles.imageOption} ${selected ? styles.optionSelected : ""}`} onClick={() => toggleOption(optionId)} aria-pressed={selected} type="button">
                      {selected && <span className={styles.selectedMark}><Check size={18} /></span>}
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
                {sequenceWithImages && interaction !== "build_word" ? (
                  <div className={styles.imageOptions} data-testid="sequence-image-options">
                    {imageOptions.filter((asset) => !selectedIds.includes(Number(asset.option_id))).map((asset) => (
                      <button key={`${asset.asset_id}-${asset.option_id}`} className={styles.imageOption} onClick={() => toggleOption(Number(asset.option_id))} disabled={targetCount > 0 && selectedIds.length >= targetCount} type="button">
                        <Image src={asset.url} alt={asset.semantic_text || "عنصر ترتيب"} width={220} height={150} unoptimized /><span className={styles.imageLabel}>{asset.semantic_text}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className={styles.options}>
                    {options.filter((option) => !selectedIds.includes(option.id)).map((option) => (
                      <button key={option.id} className={styles.option} onClick={() => toggleOption(option.id)} disabled={targetCount > 0 && selectedIds.length >= targetCount} type="button">{option.text}</button>
                    ))}
                  </div>
                )}
              </>
            )}

            {!hasMediaGap && !READ.has(interaction) && !ORDER.has(interaction) && !imageChoice && (
              <div className={styles.options} data-testid="text-options">
                {options.map((option) => {
                  const selected = selectedIds.includes(option.id);
                  return <button key={option.id} className={`${styles.option} ${selected ? styles.optionSelected : ""}`} onClick={() => toggleOption(option.id)} aria-pressed={selected} type="button">{selected && <span className={styles.selectedMark}><Check size={18} /></span>}{option.text}</button>;
                })}
              </div>
            )}

            {!hasMediaGap && READ.has(interaction) && (
              <div className={styles.recordPanel}>
                {!audioBlob ? (
                  <>
                    <button className={`${styles.recordButton} ${isRecording ? styles.recordButtonRecording : ""}`} onClick={isRecording ? stopRecording : () => void startRecording()} aria-label={isRecording ? "إيقاف التسجيل" : "بدء التسجيل"} data-testid="record-reading" type="button">{isRecording ? <MicOff size={31} /> : <Mic size={31} />}</button>
                    <p className={styles.recordLabel}>{isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط لبدء التسجيل"}</p>
                    {isRecording && <p className={styles.timer}>{String(Math.floor(recordingSeconds / 60)).padStart(2, "0")}:{String(recordingSeconds % 60).padStart(2, "0")}</p>}
                  </>
                ) : (
                  <>
                    {audioUrl && <audio ref={recordingPreviewRef} className={styles.audioPreview} src={audioUrl} controls onPlay={(event) => { event.currentTarget.volume = 1; }} />}
                    <p className={styles.previewText}>استمع إلى تسجيلك، ثم أرسله أو أعد المحاولة.</p>
                    <div className={styles.inlineActions}>
                      <button className={styles.secondary} type="button" onClick={() => { clearQuestionState(); stepStartedAtRef.current = Date.now(); }}><RotateCcw size={18} /> إعادة التسجيل</button>
                      <button className={styles.primary} type="button" onClick={() => void uploadReading()} disabled={phase === "submitting"}>إرسال التسجيل</button>
                    </div>
                  </>
                )}
              </div>
            )}
            {error && <div className={styles.error} role="alert">{error}</div>}
          </div>

          <aside className={styles.coach} aria-label="نصيحة هِمّة">
            <div className={styles.tip}><Star size={21} fill="currentColor" aria-hidden="true" /><span>{encouragement}</span></div>
            <Image className={styles.character} src={sideCharacter} alt="شخصية هِمّة المساعدة" width={180} height={245} priority />
          </aside>

          {!hasMediaGap && !READ.has(interaction) && (
            <div className={styles.bottomActions}>
              {ORDER.has(interaction) && selectedIds.length > 0 && <button className={styles.secondary} type="button" onClick={() => setSelectedIds([])}><RotateCcw size={18} /> إعادة الترتيب</button>}
              <button className={styles.primaryWide} type="button" onClick={() => void submitAnswer()} disabled={!canSubmit || phase === "submitting"}>
                <span>{phase === "submitting" ? "جاري الحفظ..." : "تأكيد والمتابعة"}</span>
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
