"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import { Check, Info, LogOut, Mic, MicOff, RotateCcw, Target, Volume2 } from "lucide-react";
import styles from "../../session/[id]/session.module.css";

type Interaction = "choose_one" | "listen_choose_one" | "choose_image" | "listen_choose_image" | "choose_many" | "listen_choose_many" | "sequence" | "memory_sequence" | "build_word" | "read_aloud" | "timed_read_aloud";
type Asset = { asset_id: string; asset_type: string; usage?: string | null; semantic_text?: string | null; url: string; option_id?: number | null };
type Option = { id: number; text: string; order_index: number };
type ViewPayload = {
  session_id: number; level_id: number; item_id: number; stable_key: string; kind: string; interaction_type: Interaction;
  round: { round_number: number; round_total: number; skill: string; encouragement: string; hint: string; question_text: string; instruction_text: string; stimulus_text?: string };
  retry: boolean; attempts_used: number;
  step: { id: number; expected_reading_text?: string | null; required_selection_count: number; options: Option[]; assets: Asset[]; media_gaps: Array<{ status?: string; semantic_text?: string }> };
  assets: Asset[];
};
type Progress = { completed_items: number; total_items: number; level_id: number; status: string };
type SubmitResult = { is_correct: boolean; step_complete: boolean; activity_complete: boolean; learning_complete: boolean; detail?: string };

const SINGLE = new Set<Interaction>(["choose_one", "listen_choose_one", "choose_image", "listen_choose_image"]);
const MULTI = new Set<Interaction>(["choose_many", "listen_choose_many"]);
const ORDER = new Set<Interaction>(["sequence", "memory_sequence", "build_word"]);
const LISTEN = new Set<Interaction>(["listen_choose_one", "listen_choose_image", "listen_choose_many"]);
const READ = new Set<Interaction>(["read_aloud", "timed_read_aloud"]);
const LEVEL_NAMES: Record<number, string> = { 1: "الاستعداد للقراءة", 2: "بناء الكلمة", 3: "الطلاقة والفهم" };

function completionCopy(levelId: number) {
  if (levelId === 1) return { title: "أحسنت، أكملت الاستعداد للقراءة", text: "خطوتك التالية هي بناء الكلمة. استمر بنفس التركيز.", cta: "الانتقال إلى خطوتي التالية" };
  if (levelId === 2) return { title: "أحسنت، أكملت بناء الكلمة", text: "خطوتك التالية هي الطلاقة والفهم. استمر، أنت تتقدم بشكل ممتاز.", cta: "الانتقال إلى خطوتي التالية" };
  return { title: "أحسنت، أكملت المستوى الثالث", text: "أكملت أنشطة الطلاقة والفهم. أصبح مسارك جاهزًا للاختبار البعدي عندما يفتحه المشرف.", cta: "العودة إلى مساري" };
}

export default function StudentActivityPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = String(params.id);
  const [view, setView] = useState<ViewPayload | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [memoryPreview, setMemoryPreview] = useState(true);
  const startedAtRef = useRef(0);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playbackRef = useRef<HTMLAudioElement | null>(null);

  const interaction = view?.interaction_type;
  const step = view?.step;
  const options = step?.options ?? [];
  const targetCount = step?.required_selection_count ?? 0;
  const audioAssets = useMemo(() => step?.assets?.filter((a) => a.asset_type === "audio") ?? [], [step]);
  const imageAssets = useMemo(() => step?.assets?.filter((a) => a.asset_type === "image") ?? [], [step]);
  const contextImages = useMemo(() => view?.assets?.filter((a) => a.asset_type === "image") ?? [], [view]);
  const imageOptions = imageAssets.filter((a) => a.option_id);
  const imageOptionIds = new Set(imageOptions.map((a) => Number(a.option_id)));
  const sequenceImagesComplete = options.length > 0 && options.every((o) => imageOptionIds.has(o.id));
  const percent = progress ? Math.min(100, Math.round((progress.completed_items / Math.max(1, progress.total_items)) * 100)) : 0;

  const fetchProgress = useCallback(async () => {
    const response = await fetch(`/api/activities/session/${sessionId}/progress`, { cache: "no-store" });
    if (response.ok) setProgress(await response.json());
  }, [sessionId]);

  const resetRoundState = () => {
    setSelected([]); setAudioBlob(null); setRecordingSeconds(0); setMemoryPreview(true); startedAtRef.current = Date.now();
    setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return null; });
  };

  const loadCurrent = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const advance = await fetch(`/api/activities/session/${sessionId}/next`, { cache: "no-store" });
      const advanceData = await advance.json().catch(() => null);
      if (!advance.ok) throw new Error(advanceData?.detail || "تعذر تجهيز النشاط");
      if (!advanceData) { setDone(true); setView(null); await fetchProgress(); return; }
      const response = await fetch(`/api/learning-experience/session/${sessionId}`, { cache: "no-store" });
      const data = await response.json().catch(() => null) as ViewPayload | null;
      if (!response.ok) throw new Error((data as unknown as { detail?: string })?.detail || "تعذر تحميل بيانات النشاط");
      if (!data?.step) { setDone(true); setView(null); await fetchProgress(); return; }
      setDone(false); setView(data); resetRoundState(); await fetchProgress();
    } catch (err) { setError(err instanceof Error ? err.message : "تعذر تحميل النشاط"); }
    finally { setLoading(false); }
  }, [fetchProgress, sessionId]);

  useEffect(() => {
    const kickoff = window.setTimeout(() => void loadCurrent(), 0);
    return () => { window.clearTimeout(kickoff); if (timerRef.current) clearInterval(timerRef.current); if (recorderRef.current?.state === "recording") recorderRef.current.stop(); playbackRef.current?.pause(); };
  }, [loadCurrent]);

  const operationKey = (kind: "answer" | "upload") => `himma:activity:${sessionId}:${step?.id ?? 0}:${(view?.attempts_used ?? 0) + 1}:${kind}`;
  const idempotencyKey = (kind: "answer" | "upload") => { const key = operationKey(kind); const existing = window.sessionStorage.getItem(key); if (existing) return existing; const created = crypto.randomUUID(); window.sessionStorage.setItem(key, created); return created; };
  const clearKeys = () => { for (const kind of ["answer", "upload"] as const) window.sessionStorage.removeItem(operationKey(kind)); };

  const playPrompt = async () => {
    if (!audioAssets.length || isListening) return;
    setIsListening(true); setError("");
    try { for (const asset of audioAssets) await new Promise<void>((resolve, reject) => { const audio = new Audio(asset.url); playbackRef.current = audio; audio.onended = () => resolve(); audio.onerror = () => reject(new Error("تعذر تشغيل الصوت")); void audio.play().catch(reject); }); }
    catch { setError("تعذر تشغيل الصوت. حاول مرة أخرى."); }
    finally { setIsListening(false); playbackRef.current = null; }
  };

  const toggleOption = (id: number) => {
    if (!interaction || submitting) return;
    if (SINGLE.has(interaction)) return setSelected([id]);
    if (MULTI.has(interaction)) return setSelected((current) => current.includes(id) ? current.filter((v) => v !== id) : targetCount > 0 && current.length >= targetCount ? current : [...current, id]);
    if (ORDER.has(interaction)) setSelected((current) => current.includes(id) || (targetCount > 0 && current.length >= targetCount) ? current : [...current, id]);
  };

  const canSubmit = Boolean(interaction && ((SINGLE.has(interaction) && selected.length === 1) || (MULTI.has(interaction) && targetCount > 0 && selected.length === targetCount) || (ORDER.has(interaction) && targetCount > 0 && selected.length === targetCount)));

  const submitStructured = async () => {
    if (!view || !step || !interaction || step.media_gaps.length) return;
    setSubmitting(true); setError("");
    try {
      const elapsed = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
      const response = await fetch(`/api/activities/session/${sessionId}/attempt/${view.item_id}/submit`, { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey("answer") }, body: JSON.stringify({ step_id: step.id, selected_option_ids: selected, hint_used: view.retry, elapsed_seconds: elapsed }) });
      const result = await response.json().catch(() => ({})) as SubmitResult;
      if (!response.ok) throw new Error(result.detail || "تعذر حفظ الإجابة");
      clearKeys();
      if (result.learning_complete) { setDone(true); await fetchProgress(); return; }
      if (!result.is_correct && !result.step_complete) { const refreshed = await fetch(`/api/learning-experience/session/${sessionId}`, { cache: "no-store" }); if (refreshed.ok) setView(await refreshed.json()); setSelected([]); startedAtRef.current = Date.now(); return; }
      await loadCurrent();
    } catch (err) { setError(err instanceof Error ? err.message : "تعذر حفظ الإجابة"); }
    finally { setSubmitting(false); }
  };

  const startRecording = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); chunksRef.current = [];
      const preferred = "audio/webm;codecs=opus"; const recorder = MediaRecorder.isTypeSupported(preferred) ? new MediaRecorder(stream, { mimeType: preferred }) : new MediaRecorder(stream);
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = () => { const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" }); setAudioBlob(blob); setAudioUrl((current) => { if (current) URL.revokeObjectURL(current); return URL.createObjectURL(blob); }); stream.getTracks().forEach((track) => track.stop()); };
      recorder.start(); recorderRef.current = recorder; setIsRecording(true); setRecordingSeconds(0); timerRef.current = setInterval(() => setRecordingSeconds((v) => v + 1), 1000);
    } catch { setError("لم نتمكن من تشغيل الميكروفون. اسمح للمتصفح باستخدامه ثم حاول مرة أخرى."); }
  };
  const stopRecording = () => { if (!recorderRef.current || recorderRef.current.state !== "recording") return; recorderRef.current.stop(); setIsRecording(false); if (timerRef.current) clearInterval(timerRef.current); };

  const uploadReading = async () => {
    if (!view || !step || !audioBlob || step.media_gaps.length) return;
    setSubmitting(true); setError("");
    try {
      const form = new FormData(); form.append("file", audioBlob, "activity-reading.webm");
      const upload = await fetch(`/api/assessment/session/${sessionId}/upload-audio`, { method: "POST", headers: { "Idempotency-Key": idempotencyKey("upload") }, body: form });
      const uploaded = await upload.json().catch(() => null); if (!upload.ok) throw new Error(uploaded?.detail || "تعذر رفع التسجيل");
      const elapsed = Math.min(3600, Math.max(0, Math.floor((Date.now() - startedAtRef.current) / 1000)));
      const submit = await fetch(`/api/activities/session/${sessionId}/attempt/${view.item_id}/submit`, { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey("answer") }, body: JSON.stringify({ step_id: step.id, audio_storage_key: uploaded.audio_storage_key, audio_file_size: uploaded.audio_file_size, audio_mime_type: uploaded.audio_mime_type, audio_duration_seconds: recordingSeconds, elapsed_seconds: elapsed }) });
      const result = await submit.json().catch(() => ({})) as SubmitResult; if (!submit.ok) throw new Error(result.detail || "تعذر حفظ القراءة");
      clearKeys(); await loadCurrent();
    } catch (err) { setError(err instanceof Error ? err.message : "تعذر حفظ القراءة"); }
    finally { setSubmitting(false); }
  };

  if (loading) return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="loading"><div className={styles.loadingState}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={128} height={46}/><div className={styles.spinner}/><p>جاري تجهيز النشاط...</p></div></div>;
  if (done) { const copy = completionCopy(progress?.level_id ?? 1); return <div className={styles.resultPage} dir="rtl" data-testid="activity-session" data-phase="done"><div className={styles.resultCard}><div className={styles.resultContent}><h1 className={styles.resultTitle}>{copy.title}</h1><p className={styles.resultText}>{copy.text}</p><button className={styles.primary} onClick={() => router.push("/student")}>{copy.cta}</button></div><div className={styles.resultVisual}><Image src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل" width={320} height={390}/></div></div></div>; }
  if (!view || !step || !interaction) return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase="error"><div className={styles.loadingState}><h1>تعذر فتح النشاط</h1><p>{error || "بيانات النشاط غير متاحة."}</p><button className={styles.primary} onClick={() => void loadCurrent()}>حاول مرة أخرى</button></div></div>;

  const hasMediaGap = step.media_gaps.length > 0;
  const message = view.retry ? view.round.hint : view.round.encouragement;
  const isImageChoice = interaction === "choose_image" || interaction === "listen_choose_image" || ((interaction === "choose_many" || interaction === "listen_choose_many") && imageOptions.length > 0);
  const stimulus = String(view.round.stimulus_text || "").trim();
  const visualAsset = contextImages[0];
  const isReinforcement = view.kind === "reinforcement_activity";
  const label = isReinforcement ? "تدريب تقوية" : `المستوى ${view.level_id} — ${LEVEL_NAMES[view.level_id] || "التعلم"}`;
  const selectionLimitReached = targetCount > 0 && selected.length >= targetCount;

  const optionButtons = (image: boolean) => image ? <div className={styles.imageOptions} data-testid="activity-image-options">{imageOptions.map((asset) => { const id = Number(asset.option_id); const chosen = selected.includes(id); return <button key={asset.asset_id} className={`${styles.imageOption} ${chosen ? styles.optionSelected : ""}`} type="button" onClick={() => toggleOption(id)} disabled={MULTI.has(interaction) && selectionLimitReached && !chosen} aria-pressed={chosen} data-testid="activity-option">{chosen && <span className={styles.selectedMark}><Check size={18}/></span>}<Image src={asset.url} alt={asset.semantic_text || "خيار مصور"} width={220} height={150} unoptimized/><span className={styles.imageLabel}>{asset.semantic_text || options.find((o) => o.id === id)?.text}</span></button>; })}</div> : <div className={styles.options} data-testid="activity-text-options">{options.map((option) => { const chosen = selected.includes(option.id); return <button key={option.id} className={`${styles.option} ${chosen ? styles.optionSelected : ""}`} type="button" onClick={() => toggleOption(option.id)} disabled={MULTI.has(interaction) && selectionLimitReached && !chosen} aria-pressed={chosen} data-testid="activity-option">{chosen && <span className={styles.selectedMark}><Check size={18}/></span>}{option.text}</button>; })}</div>;

  return <div className={styles.page} dir="rtl" data-testid="activity-session" data-phase={submitting ? "submitting" : "active"} data-activity-kind={isReinforcement ? "reinforcement" : "core"} data-item-id={view.item_id} data-step-id={step.id} data-interaction-type={interaction} data-media-gap-count={step.media_gaps.length}>
    <header className={styles.header}><div className={styles.headerInner}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={124} height={44} priority/><button className={styles.exit} type="button" onClick={() => router.push("/student")}><LogOut size={21}/><span>رجوع</span></button></div></header>
    <div className={styles.progressPanel}><div className={styles.progressTop}><span className={styles.assessmentBadge}>{label}</span><span className={styles.progressCount}>{progress?.completed_items ?? 0} من {progress?.total_items ?? 10}</span></div><div className={styles.progressTrack} aria-label={`التقدم ${percent}%`}><div className={styles.progressFill} style={{ width: `${Math.max(percent,2)}%` }}/></div></div>
    <main className={styles.shell}><section className={styles.card}>
      <div className={styles.taskMeta}><div className={styles.skillChip}><Target size={19}/>{view.round.skill}</div><span className={styles.assessmentBadge}>الجولة {view.round.round_number} من {view.round.round_total}</span></div>
      <div className={styles.contentColumn}>
        {isReinforcement && <div className={styles.notice} data-testid="reinforcement-intro">هذا تدريب قصير يساعدك على إتقان المهارة، وبعد إتقانها تعود إلى نشاطك الأساسي.</div>}
        <h1 className={styles.questionTitle}>{view.round.question_text}</h1>
        {stimulus && !LISTEN.has(interaction) && !READ.has(interaction) && <div className={`${styles.stimulusBox} ${stimulus.length <= 3 ? styles.letterStimulus : ""}`}>{stimulus}</div>}
        {visualAsset && interaction !== "memory_sequence" && <div className={styles.contextImage}><Image src={visualAsset.url} alt={visualAsset.semantic_text || "صورة النشاط"} width={420} height={260} unoptimized/></div>}
        {LISTEN.has(interaction) && <button type="button" className={`${styles.listenButton} ${isListening ? styles.listenPulse : ""}`} onClick={() => void playPrompt()} disabled={isListening || !audioAssets.length || hasMediaGap} data-testid="activity-listen-prompt"><Volume2 size={34}/><span>{isListening ? "استمع..." : "استمع"}</span></button>}
        {READ.has(interaction) && <div className={`${styles.readingBox} ${(step.expected_reading_text?.length || stimulus.length) > 55 ? styles.readingBoxLong : ""}`} data-testid="activity-reading-text">{step.expected_reading_text || stimulus || "اقرأ النص الظاهر"}</div>}
        <div className={styles.instructionRow} data-testid="student-task-instruction"><Info size={21}/><p>{view.round.instruction_text}</p></div>
        {hasMediaGap && <div className={styles.notice} role="alert" data-testid="declared-media-gap">هذا النشاط متوقف لأن أصلًا تعليميًا معتمدًا غير متوفر. لا يمكن تجاوز الجولة أو احتسابها. تواصل مع المشرف.</div>}
        {!hasMediaGap && interaction === "memory_sequence" && (memoryPreview ? <><div className={styles.imageOptions} data-testid="activity-memory-preview">{imageOptions.map((asset,index)=><div key={asset.asset_id} className={styles.imageOption}><span className={styles.selectedMark}>{index+1}</span><Image src={asset.url} alt={asset.semantic_text || `الصورة ${index+1}`} width={220} height={150} unoptimized/><span className={styles.imageLabel}>{asset.semantic_text}</span></div>)}</div><div className={styles.inlineActions}><button className={styles.primary} type="button" onClick={()=>setMemoryPreview(false)}>التالي</button></div></> : <><div className={styles.sequenceBoard}>{selected.length === 0 ? <span className={styles.sequenceHint}>رتّب الصور كما ظهرت.</span> : selected.map((id,index)=><span className={styles.sequenceChip} key={id}><span className={styles.number}>{index+1}</span>{imageOptions.find((a)=>Number(a.option_id)===id)?.semantic_text}</span>)}</div><div className={styles.imageOptions} data-testid="activity-sequence-image-options">{imageOptions.filter((a)=>!selected.includes(Number(a.option_id))).map((a)=><button key={a.asset_id} className={styles.imageOption} type="button" onClick={()=>toggleOption(Number(a.option_id))} disabled={selectionLimitReached}><Image src={a.url} alt={a.semantic_text || "خيار صورة"} width={220} height={150} unoptimized/><span className={styles.imageLabel}>{a.semantic_text}</span></button>)}</div></>)}
        {!hasMediaGap && interaction !== "memory_sequence" && (interaction === "sequence" || interaction === "build_word") && <><div className={styles.sequenceBoard}>{selected.length === 0 ? <span className={styles.sequenceHint}>ابدأ بالعنصر الأول ثم أكمل بالترتيب.</span> : selected.map((id,index)=><span className={styles.sequenceChip} key={id}><span className={styles.number}>{index+1}</span>{options.find((o)=>o.id===id)?.text}</span>)}</div>{sequenceImagesComplete && interaction !== "build_word" ? <div className={styles.imageOptions} data-testid="activity-sequence-image-options">{imageOptions.filter((a)=>!selected.includes(Number(a.option_id))).map((a)=><button key={a.asset_id} className={styles.imageOption} type="button" onClick={()=>toggleOption(Number(a.option_id))} disabled={selectionLimitReached}><Image src={a.url} alt={a.semantic_text || "عنصر ترتيب"} width={220} height={150} unoptimized/><span className={styles.imageLabel}>{a.semantic_text}</span></button>)}</div> : <div className={styles.options} data-testid="activity-sequence-options">{options.filter((o)=>!selected.includes(o.id)).map((o)=><button key={o.id} className={styles.option} type="button" onClick={()=>toggleOption(o.id)} disabled={selectionLimitReached}>{o.text}</button>)}</div>}</>}
        {!hasMediaGap && interaction !== "memory_sequence" && !ORDER.has(interaction) && !READ.has(interaction) && optionButtons(isImageChoice)}
        {!hasMediaGap && READ.has(interaction) && <div className={styles.recordPanel}>{!audioBlob ? <><button className={`${styles.recordButton} ${isRecording ? styles.recordButtonRecording : ""}`} type="button" onClick={isRecording ? stopRecording : () => void startRecording()} aria-label={isRecording ? "إيقاف التسجيل" : "بدء التسجيل"} data-testid="record-reading">{isRecording ? <MicOff size={30}/> : <Mic size={30}/>}</button><p className={styles.recordLabel}>{isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط لبدء التسجيل"}</p>{isRecording && <p className={styles.timer}>{String(Math.floor(recordingSeconds/60)).padStart(2,"0")}:{String(recordingSeconds%60).padStart(2,"0")}</p>}</> : <>{audioUrl && <audio className={styles.audioPreview} src={audioUrl} controls/>}<div className={styles.inlineActions}><button className={styles.secondary} type="button" onClick={resetRoundState}><RotateCcw size={17}/> إعادة التسجيل</button><button className={styles.primary} type="button" onClick={()=>void uploadReading()} disabled={submitting}>{submitting ? "جاري الحفظ..." : "إرسال التسجيل للمراجعة"}</button></div><p className={styles.recordLabel}>يراجع المشرف التسجيل ويعتمده أو يطلب إعادة التسجيل.</p></>}</div>}
      </div>
      <aside className={styles.coach} aria-label="نصيحة هِمّة"><div className={styles.tip}><span>{message}</span></div><Image className={styles.character} src={view.retry ? "/characters/girl/encourage.png" : "/characters/girl/explain.png"} alt="شخصية هِمّة" width={150} height={205}/></aside>
      {error && <div className={styles.error} role="alert">{error}</div>}
      {!hasMediaGap && !READ.has(interaction) && !(interaction === "memory_sequence" && memoryPreview) && <div className={styles.bottomActions}>{ORDER.has(interaction) && selected.length > 0 && <button className={styles.secondary} type="button" onClick={()=>setSelected([])} disabled={submitting}><RotateCcw size={17}/> إعادة الترتيب</button>}<button className={styles.primaryWide} type="button" onClick={()=>void submitStructured()} disabled={submitting || !canSubmit}>{submitting ? "جاري الحفظ..." : "تأكيد والمتابعة"}</button></div>}
    </section></main>
  </div>;
}
