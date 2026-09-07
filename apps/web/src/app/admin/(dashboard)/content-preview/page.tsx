"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Eye,
  Info,
  Mic,
  MicOff,
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Target,
  Volume2,
} from "lucide-react";
import { shuffleForPresentation } from "@/lib/student-experience";
import studentStyles from "@/app/student/session/[id]/session.module.css";
import styles from "./preview.module.css";

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

type Asset = {
  asset_id: string;
  asset_type: string;
  usage?: string | null;
  semantic_text?: string | null;
  url: string;
  option_id?: number | null;
};

type Option = { id: number; text: string; order_index: number };
type PreviewStep = {
  id: number;
  order_index: number;
  expected_reading_text?: string | null;
  required_selection_count: number;
  presentation: Record<string, unknown>;
  options: Option[];
  assets: Asset[];
  media_gaps: Array<{ status?: string; semantic_text?: string }>;
};
type PreviewItem = {
  id: number;
  stable_key: string;
  canonical_id: string;
  kind: "pretest_question" | "posttest_question" | "core_activity" | "reinforcement_activity";
  level_id: number;
  order_index: number;
  interaction_type: Interaction;
  skill?: string | null;
  item_assets: Asset[];
  steps: PreviewStep[];
};
type PreviewSection = {
  key: string;
  label: string;
  kind: PreviewItem["kind"];
  level_id: number | null;
  item_count: number;
  round_count: number;
  items: PreviewItem[];
};
type PreviewJourney = {
  version: string;
  read_only: boolean;
  adaptive_logic: boolean;
  results_persisted: boolean;
  item_count: number;
  round_count: number;
  sections: PreviewSection[];
};
type PlaybackState = "idle" | "playing" | "paused";

const SINGLE = new Set<Interaction>(["choose_one", "listen_choose_one", "choose_image", "listen_choose_image"]);
const MULTI = new Set<Interaction>(["choose_many", "listen_choose_many"]);
const ORDER = new Set<Interaction>(["sequence", "memory_sequence", "path_sequence", "build_word"]);
const LISTEN = new Set<Interaction>(["listen_choose_one", "listen_choose_image", "listen_choose_many"]);
const READ = new Set<Interaction>(["read_aloud", "timed_read_aloud"]);

function stringValue(value: unknown, fallback = "") {
  return typeof value === "string" ? value.trim() : fallback;
}

function stimulusValue(presentation: Record<string, unknown>) {
  const direct = stringValue(presentation.stimulus_text);
  if (direct) return direct;
  const stimulus = presentation.stimulus;
  if (stimulus && typeof stimulus === "object") {
    return stringValue((stimulus as { text?: unknown }).text);
  }
  return "";
}

function questionNumber(item: PreviewItem, step: PreviewStep) {
  const fromPresentation = Number(step.presentation.question_number || 0);
  return fromPresentation > 0 ? fromPresentation : item.order_index;
}

export default function AdminContentPreviewPage() {
  const [journey, setJourney] = useState<PreviewJourney | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sectionIndex, setSectionIndex] = useState(0);
  const [itemIndex, setItemIndex] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);
  const [selected, setSelected] = useState<number[]>([]);
  const [memoryPreview, setMemoryPreview] = useState(true);
  const [showCelebration, setShowCelebration] = useState(false);
  const [journeyDone, setJourneyDone] = useState(false);
  const [playbackState, setPlaybackState] = useState<PlaybackState>("idle");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const playbackRef = useRef<HTMLAudioElement | null>(null);
  const recordingPreviewRef = useRef<HTMLAudioElement | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const recordingStreamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const currentSection = journey?.sections[sectionIndex] ?? null;
  const currentItem = currentSection?.items[itemIndex] ?? null;
  const currentStep = currentItem?.steps[stepIndex] ?? null;
  const interaction: Interaction = currentItem?.interaction_type ?? "choose_one";

  const options = useMemo(() => shuffleForPresentation(currentStep?.options ?? []), [currentStep]);
  const audioAssets = useMemo(
    () => currentStep?.assets.filter((asset) => asset.asset_type === "audio") ?? [],
    [currentStep],
  );
  const imageAssets = useMemo(
    () => currentStep?.assets.filter((asset) => asset.asset_type === "image") ?? [],
    [currentStep],
  );
  const contextImages = useMemo(
    () => currentItem?.item_assets.filter((asset) => asset.asset_type === "image") ?? [],
    [currentItem],
  );
  const optionRank = useMemo(() => new Map(options.map((option, index) => [option.id, index])), [options]);
  const imageOptions = useMemo(
    () => imageAssets
      .filter((asset) => asset.option_id)
      .sort((a, b) => (optionRank.get(Number(a.option_id)) ?? 999) - (optionRank.get(Number(b.option_id)) ?? 999)),
    [imageAssets, optionRank],
  );
  const memoryPreviewImages = useMemo(() => {
    const canonical = [...(currentStep?.options ?? [])].sort((a, b) => a.order_index - b.order_index);
    const rank = new Map(canonical.map((option, index) => [option.id, index]));
    return imageAssets
      .filter((asset) => asset.option_id)
      .sort((a, b) => (rank.get(Number(a.option_id)) ?? 999) - (rank.get(Number(b.option_id)) ?? 999));
  }, [currentStep, imageAssets]);

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

  const stopRecordingPreview = useCallback(() => {
    const preview = recordingPreviewRef.current;
    if (preview) {
      preview.pause();
      preview.currentTime = 0;
    }
  }, []);

  const resetInteraction = useCallback(() => {
    stopPrompt();
    stopRecordingPreview();
    setSelected([]);
    setMemoryPreview(true);
    setIsRecording(false);
    setRecordingSeconds(0);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    const recorder = recorderRef.current;
    if (recorder?.state === "recording") recorder.stop();
    recordingStreamRef.current?.getTracks().forEach((track) => track.stop());
    recordingStreamRef.current = null;
    setAudioUrl((current) => {
      if (current) URL.revokeObjectURL(current);
      return null;
    });
  }, [stopPrompt, stopRecordingPreview]);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const response = await fetch("/api/researcher/content-preview/journey", { cache: "no-store" });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.detail || "تعذر تحميل محتوى المعاينة");
        if (alive) setJourney(data as PreviewJourney);
      } catch (err) {
        if (alive) setError(err instanceof Error ? err.message : "تعذر تحميل محتوى المعاينة");
      } finally {
        if (alive) setLoading(false);
      }
    };
    void load();
    return () => { alive = false; };
  }, []);

  useEffect(() => () => {
    const audio = playbackRef.current;
    if (audio) audio.pause();
    const preview = recordingPreviewRef.current;
    if (preview) preview.pause();
    const recorder = recorderRef.current;
    if (recorder?.state === "recording") recorder.stop();
    recordingStreamRef.current?.getTracks().forEach((track) => track.stop());
    if (timerRef.current) clearInterval(timerRef.current);
  }, []);

  function playAssetAt(index: number) {
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
      setError("تعذر تشغيل هذا الصوت في المعاينة.");
    };
    setPlaybackState("playing");
    void audio.play().catch(() => {
      stopPrompt();
      setError("تعذر تشغيل هذا الصوت في المعاينة.");
    });
  }

  const togglePrompt = () => {
    const audio = playbackRef.current;
    if (playbackState === "playing" && audio) {
      audio.pause();
      setPlaybackState("paused");
      return;
    }
    if (playbackState === "paused" && audio) {
      void audio.play().then(() => setPlaybackState("playing"));
      return;
    }
    setError("");
    playAssetAt(0);
  };

  const startRecording = async () => {
    stopPrompt();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordingStreamRef.current = stream;
      chunksRef.current = [];
      const preferred = "audio/webm;codecs=opus";
      const recorder = MediaRecorder.isTypeSupported(preferred)
        ? new MediaRecorder(stream, { mimeType: preferred })
        : new MediaRecorder(stream);
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioUrl((current) => {
          if (current) URL.revokeObjectURL(current);
          return URL.createObjectURL(blob);
        });
        stream.getTracks().forEach((track) => track.stop());
        recordingStreamRef.current = null;
      };
      recorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => setRecordingSeconds((value) => value + 1), 1000);
    } catch {
      setError("لم نتمكن من تشغيل الميكروفون. التسجيل في هذه الصفحة محلي للمعاينة فقط.");
    }
  };

  const stopRecording = () => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording") return;
    recorder.stop();
    setIsRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const toggleOption = (id: number) => {
    if (SINGLE.has(interaction)) {
      setSelected([id]);
      return;
    }
    if (MULTI.has(interaction)) {
      const target = currentStep?.required_selection_count || options.length;
      setSelected((current) => current.includes(id)
        ? current.filter((value) => value !== id)
        : current.length >= target ? current : [...current, id]);
      return;
    }
    if (ORDER.has(interaction)) {
      setSelected((current) => current.includes(id) ? current : [...current, id]);
    }
  };

  const moveTo = (nextSection: number, nextItem: number, nextStep: number) => {
    resetInteraction();
    setShowCelebration(false);
    setJourneyDone(false);
    setSectionIndex(nextSection);
    setItemIndex(nextItem);
    setStepIndex(nextStep);
  };

  const advancePastCurrentItem = () => {
    if (!journey || !currentSection) return;
    if (itemIndex < currentSection.items.length - 1) {
      moveTo(sectionIndex, itemIndex + 1, 0);
      return;
    }
    if (sectionIndex < journey.sections.length - 1) {
      moveTo(sectionIndex + 1, 0, 0);
      return;
    }
    resetInteraction();
    setShowCelebration(false);
    setJourneyDone(true);
  };

  const goNext = () => {
    if (!currentItem || !currentStep) return;
    resetInteraction();
    if (stepIndex < currentItem.steps.length - 1) {
      setStepIndex(stepIndex + 1);
      return;
    }
    if (currentItem.kind === "core_activity" || currentItem.kind === "reinforcement_activity") {
      setShowCelebration(true);
      return;
    }
    advancePastCurrentItem();
  };

  const goPrevious = () => {
    if (!journey || !currentSection) return;
    if (journeyDone) {
      setJourneyDone(false);
      return;
    }
    resetInteraction();
    if (showCelebration) {
      setShowCelebration(false);
      return;
    }
    if (stepIndex > 0) {
      setStepIndex(stepIndex - 1);
      return;
    }
    if (itemIndex > 0) {
      const previousItem = currentSection.items[itemIndex - 1];
      setItemIndex(itemIndex - 1);
      setStepIndex(Math.max(0, previousItem.steps.length - 1));
      return;
    }
    if (sectionIndex > 0) {
      const previousSection = journey.sections[sectionIndex - 1];
      const previousItemIndex = Math.max(0, previousSection.items.length - 1);
      const previousItem = previousSection.items[previousItemIndex];
      setSectionIndex(sectionIndex - 1);
      setItemIndex(previousItemIndex);
      setStepIndex(Math.max(0, (previousItem?.steps.length ?? 1) - 1));
    }
  };

  if (loading) return <div className={styles.page}><div className={styles.loading}><div><div className="spinner w-12 h-12 border-4" /><p>جاري تجهيز رحلة المعاينة...</p></div></div></div>;
  if (error && !journey) return <div className={styles.page}><div className={styles.error}><div><h1>تعذر فتح المعاينة</h1><p>{error}</p></div></div></div>;
  if (!journey || !currentSection || !currentItem || !currentStep) return <div className={styles.page}><div className={styles.empty}>لا يوجد محتوى متاح للمعاينة.</div></div>;

  const roundBeforeItem = currentSection.items.slice(0, itemIndex).reduce((sum, item) => sum + item.steps.length, 0);
  const roundInSection = roundBeforeItem + stepIndex + 1;
  const roundsBeforeSection = journey.sections.slice(0, sectionIndex).reduce((sum, section) => sum + section.round_count, 0);
  const globalRound = roundsBeforeSection + roundInSection;
  const progress = Math.min(100, Math.round((roundInSection / Math.max(1, currentSection.round_count)) * 100));
  const presentation = currentStep.presentation || {};
  const skill = stringValue(presentation.skill, currentItem.skill || "المهارة الحالية");
  const encouragement = stringValue(presentation.encouragement, "استمر، أنت تتقدم بشكل رائع.");
  const question = stringValue(presentation.question_text, currentItem.skill || "مهمة تعليمية");
  const instruction = stringValue(presentation.instruction_text, "نفّذ المطلوب كما يظهر أمامك.");
  const stimulus = stimulusValue(presentation);
  const visualAsset = contextImages[0];
  const hasMediaGap = currentStep.media_gaps.length > 0;
  const isImageChoice = interaction === "choose_image" || interaction === "listen_choose_image" || ((interaction === "choose_many" || interaction === "listen_choose_many") && imageOptions.length > 0);
  const selectionLimit = currentStep.required_selection_count > 0 && selected.length >= currentStep.required_selection_count;
  const isAssessment = currentItem.kind === "pretest_question" || currentItem.kind === "posttest_question";
  const itemLabel = isAssessment
    ? `السؤال ${questionNumber(currentItem, currentStep)} من ${currentSection.item_count}`
    : `النشاط ${currentItem.order_index} من ${currentSection.item_count} — الجولة ${currentStep.order_index} من ${currentItem.steps.length}`;
  const listenLabel = playbackState === "playing" ? "إيقاف مؤقت" : playbackState === "paused" ? "متابعة" : "استمع";
  const listenIcon = playbackState === "playing" ? <Pause size={34} /> : playbackState === "paused" ? <Play size={34} /> : <Volume2 size={34} />;
  const firstPosition = sectionIndex === 0 && itemIndex === 0 && stepIndex === 0 && !showCelebration && !journeyDone;
  const lastPosition = sectionIndex === journey.sections.length - 1 && itemIndex === currentSection.items.length - 1 && stepIndex === currentItem.steps.length - 1;

  const renderOptions = () => {
    if (isImageChoice) {
      return <div className={studentStyles.imageOptions} data-testid="preview-image-options">{imageOptions.map((asset) => {
        const id = Number(asset.option_id);
        const chosen = selected.includes(id);
        return <button key={asset.asset_id} type="button" className={`${studentStyles.imageOption} ${chosen ? studentStyles.optionSelected : ""}`} onClick={() => toggleOption(id)} disabled={MULTI.has(interaction) && selectionLimit && !chosen} aria-pressed={chosen}>{chosen && <span className={studentStyles.selectedMark}><Check size={18} /></span>}<Image src={asset.url} alt={asset.semantic_text || "خيار مصور"} width={220} height={150} unoptimized /><span className={studentStyles.imageLabel}>{asset.semantic_text || options.find((option) => option.id === id)?.text}</span></button>;
      })}</div>;
    }
    return <div className={studentStyles.options} data-testid="preview-text-options">{options.map((option) => {
      const chosen = selected.includes(option.id);
      return <button key={option.id} type="button" className={`${studentStyles.option} ${chosen ? studentStyles.optionSelected : ""}`} onClick={() => toggleOption(option.id)} disabled={MULTI.has(interaction) && selectionLimit && !chosen} aria-pressed={chosen}>{chosen && <span className={studentStyles.selectedMark}><Check size={18} /></span>}{option.text}</button>;
    })}</div>;
  };

  const celebrationNext = itemIndex < currentSection.items.length - 1
    ? `النشاط التالي: ${currentSection.items[itemIndex + 1].order_index} من ${currentSection.item_count}`
    : sectionIndex < journey.sections.length - 1
      ? `الخطوة التالية: ${journey.sections[sectionIndex + 1].label}`
      : "هذه آخر خطوة في رحلة المعاينة";

  return (
    <div className={styles.page} dir="rtl" data-testid="admin-content-preview">
      <div className={styles.heading}>
        <div>
          <h1>معاينة رحلة الطالب</h1>
          <p>مرور كامل على المحتوى كما يراه الطالب، بالترتيب من الاختبار القبلي حتى الاختبار البعدي، بدون تكيف وبدون إنشاء جلسة أو حفظ إجابة أو نتيجة.</p>
        </div>
        <span className={styles.readOnlyBadge}><ShieldCheck size={18} /> وضع مؤقت للمعاينة فقط</span>
      </div>

      <section className={styles.controlPanel} aria-label="أدوات المعاينة">
        <div className={styles.notice}><Info size={20} /><span>يمكنك التقدم والتراجع والقفز لأي قسم أو نشاط. كل الاختيارات والتسجيلات هنا محلية في المتصفح ولا تُحسب على أي طالب.</span></div>
        <div className={styles.sectionRail}>{journey.sections.map((section, index) => <button key={section.key} type="button" className={`${styles.sectionButton} ${index === sectionIndex ? styles.sectionButtonActive : ""}`} onClick={() => moveTo(index, 0, 0)}>{section.label} · {section.item_count}</button>)}</div>
        <div className={styles.controls}>
          <label className={styles.field}>القسم<select className={styles.select} value={sectionIndex} onChange={(event) => moveTo(Number(event.target.value), 0, 0)}>{journey.sections.map((section, index) => <option key={section.key} value={index}>{section.label} — {section.item_count} عنصر</option>)}</select></label>
          <label className={styles.field}>{isAssessment ? "السؤال" : "النشاط"}<select className={styles.select} value={itemIndex} onChange={(event) => moveTo(sectionIndex, Number(event.target.value), 0)}>{currentSection.items.map((item, index) => <option key={item.id} value={index}>{isAssessment ? `السؤال ${item.order_index}` : `النشاط ${item.order_index}`} · {item.skill || item.stable_key}</option>)}</select></label>
          <div className={styles.stats}><span className={styles.stat}>{journey.item_count} عنصر</span><span className={styles.stat}>{globalRound} / {journey.round_count} عرض</span></div>
        </div>
      </section>

      <section className={styles.viewport}>
        <div className={styles.viewportLabel}><span><Eye size={16} /> منظور الطالب</span><span>لا يتم الحفظ</span></div>
        <div className={styles.studentScreen}>
          {journeyDone ? (
            <div className={studentStyles.resultPage}>
              <div className={studentStyles.resultCard}>
                <div className={studentStyles.resultContent}>
                  <span className={studentStyles.resultBadge}><Sparkles size={18} /> اكتملت المعاينة</span>
                  <h1 className={studentStyles.resultTitle}>مررت على رحلة الطالب كاملة</h1>
                  <p className={studentStyles.resultText}>تمت معاينة الاختبار القبلي والمستويات والتقوية والاختبار البعدي بدون تسجيل أي نتيجة.</p>
                  <button className={studentStyles.primary} type="button" onClick={() => moveTo(0, 0, 0)}>ابدأ المعاينة من البداية</button>
                </div>
                <div className={studentStyles.resultVisual}><Image src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل" width={320} height={390} /></div>
              </div>
            </div>
          ) : showCelebration ? (
            <div className={studentStyles.resultPage}>
              <div className={studentStyles.resultCard}>
                <div className={studentStyles.resultContent}>
                  <span className={studentStyles.resultBadge}><Sparkles size={18} /> إنجاز جديد</span>
                  <h1 className={studentStyles.resultTitle}>{currentItem.kind === "reinforcement_activity" ? "أحسنت، أنجزت تدريب التقوية!" : `أحسنت، أكملت النشاط ${currentItem.order_index}!`}</h1>
                  <p className={studentStyles.resultText}>أنجزت جولات {skill} وعددها {currentItem.steps.length} بنجاح في هذه المعاينة.</p>
                  <div className={studentStyles.score}>{currentItem.order_index}/{currentSection.item_count}</div>
                  <p className={studentStyles.resultLevel}>{celebrationNext}</p>
                  <button className={studentStyles.primary} type="button" onClick={advancePastCurrentItem}>متابعة الرحلة</button>
                </div>
                <div className={studentStyles.resultVisual}><Image src="/characters/girl/success.png" alt="شخصية هِمّة تحتفل بالإنجاز" width={320} height={390} /></div>
              </div>
            </div>
          ) : (
            <>
              <header className={studentStyles.header}><div className={studentStyles.headerInner}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={124} height={44} priority /><span className={styles.previewOnly}><Eye size={16} /> معاينة المشرف</span></div></header>
              <div className={studentStyles.progressPanel}><div className={studentStyles.progressTop}><span className={studentStyles.assessmentBadge}>{currentSection.label}</span><span className={studentStyles.progressCount}>{itemLabel}</span></div><div className={studentStyles.progressTrack} aria-label={`التقدم ${progress}%`}><div className={studentStyles.progressFill} style={{ width: `${Math.max(progress, 2)}%` }} /></div></div>
              <main className={studentStyles.shell}><section className={studentStyles.card}>
                <div className={studentStyles.taskMeta}><div className={studentStyles.skillChip}><Target size={19} />{skill}</div>{!isAssessment && <span className={studentStyles.assessmentBadge}>الجولة {currentStep.order_index} من {currentItem.steps.length}</span>}</div>
                <div className={studentStyles.contentColumn}>
                  <h1 className={studentStyles.questionTitle}>{question}</h1>
                  {stimulus && !LISTEN.has(interaction) && !READ.has(interaction) && <div className={`${studentStyles.stimulusBox} ${stimulus.length <= 3 ? studentStyles.letterStimulus : ""}`}>{stimulus}</div>}
                  {visualAsset && interaction !== "memory_sequence" && <div className={studentStyles.contextImage}><Image src={visualAsset.url} alt={visualAsset.semantic_text || "صورة المحتوى"} width={420} height={260} unoptimized /></div>}
                  {LISTEN.has(interaction) && <button type="button" className={`${studentStyles.listenButton} ${playbackState === "playing" ? studentStyles.listenPulse : ""}`} onClick={togglePrompt} disabled={!audioAssets.length || hasMediaGap} aria-label={listenLabel}>{listenIcon}<span>{listenLabel}</span></button>}
                  {READ.has(interaction) && <div className={`${studentStyles.readingBox} ${(currentStep.expected_reading_text?.length || stimulus.length) > 55 ? studentStyles.readingBoxLong : ""}`}>{currentStep.expected_reading_text || stimulus || "اقرأ النص الظاهر"}</div>}
                  <div className={studentStyles.instructionRow}><Info size={21} /><p>{instruction}</p></div>
                  {hasMediaGap && <div className={studentStyles.notice} role="alert">يوجد أصل وسائط غير متوفر لهذه الجولة، لذلك يظهر هنا بوضوح أثناء فحص المحتوى.</div>}

                  {!hasMediaGap && interaction === "memory_sequence" && (memoryPreview
                    ? <><div className={studentStyles.imageOptions}>{memoryPreviewImages.map((asset, index) => <div key={asset.asset_id} className={studentStyles.imageOption}><span className={studentStyles.selectedMark}>{index + 1}</span><Image src={asset.url} alt={asset.semantic_text || `الصورة ${index + 1}`} width={220} height={150} unoptimized /><span className={studentStyles.imageLabel}>{asset.semantic_text}</span></div>)}</div><div className={studentStyles.inlineActions}><button className={studentStyles.primary} type="button" onClick={() => setMemoryPreview(false)}>التالي</button></div></>
                    : <><div className={studentStyles.sequenceBoard}>{selected.length === 0 ? <span className={studentStyles.sequenceHint}>رتّب الصور كما ظهرت.</span> : selected.map((id, index) => <span className={studentStyles.sequenceChip} key={id}><span className={studentStyles.number}>{index + 1}</span>{imageOptions.find((asset) => Number(asset.option_id) === id)?.semantic_text}</span>)}</div><div className={studentStyles.imageOptions}>{imageOptions.filter((asset) => !selected.includes(Number(asset.option_id))).map((asset) => <button key={asset.asset_id} className={studentStyles.imageOption} type="button" onClick={() => toggleOption(Number(asset.option_id))}><Image src={asset.url} alt={asset.semantic_text || "خيار صورة"} width={220} height={150} unoptimized /><span className={studentStyles.imageLabel}>{asset.semantic_text}</span></button>)}</div></>)}

                  {!hasMediaGap && interaction !== "memory_sequence" && ORDER.has(interaction) && <><div className={studentStyles.sequenceBoard}>{selected.length === 0 ? <span className={studentStyles.sequenceHint}>ابدأ بالعنصر الأول ثم أكمل بالترتيب.</span> : selected.map((id, index) => <span className={studentStyles.sequenceChip} key={id}><span className={studentStyles.number}>{index + 1}</span>{options.find((option) => option.id === id)?.text}</span>)}</div><div className={studentStyles.options}>{options.filter((option) => !selected.includes(option.id)).map((option) => <button key={option.id} className={studentStyles.option} type="button" onClick={() => toggleOption(option.id)}>{option.text}</button>)}</div></>}

                  {!hasMediaGap && !ORDER.has(interaction) && !READ.has(interaction) && renderOptions()}

                  {!hasMediaGap && READ.has(interaction) && <div className={studentStyles.recordPanel}>{!audioUrl ? <><button className={`${studentStyles.recordButton} ${isRecording ? studentStyles.recordButtonRecording : ""}`} type="button" onClick={isRecording ? stopRecording : () => void startRecording()} aria-label={isRecording ? "إيقاف التسجيل" : "بدء التسجيل"}>{isRecording ? <MicOff size={30} /> : <Mic size={30} />}</button><p className={studentStyles.recordLabel}>{isRecording ? "جاري التسجيل... اضغط للإيقاف" : "اضغط لبدء التسجيل"}</p>{isRecording && <p className={studentStyles.timer}>{String(Math.floor(recordingSeconds / 60)).padStart(2, "0")}:{String(recordingSeconds % 60).padStart(2, "0")}</p>}</> : <><audio ref={recordingPreviewRef} className={studentStyles.audioPreview} src={audioUrl} controls /><div className={studentStyles.inlineActions}><button className={studentStyles.secondary} type="button" onClick={resetInteraction}><RotateCcw size={17} /> إعادة التسجيل</button></div></>}<p className={styles.localRecordingNote}>التسجيل محلي داخل جهازك ولا يتم رفعه أو حفظه.</p></div>}
                </div>
                <aside className={studentStyles.coach} aria-label="تشجيع هِمّة"><div className={studentStyles.tip}><span>{encouragement}</span></div><Image className={studentStyles.character} src="/characters/girl/explain.png" alt="شخصية هِمّة" width={150} height={205} /></aside>
                {!READ.has(interaction) && !(interaction === "memory_sequence" && memoryPreview) && <div className={studentStyles.bottomActions}>{ORDER.has(interaction) && selected.length > 0 && <button className={studentStyles.secondary} type="button" onClick={() => setSelected([])}><RotateCcw size={17} /> إعادة الترتيب</button>}<button className={studentStyles.primaryWide} type="button" onClick={goNext}>تأكيد والمتابعة</button></div>}
                {READ.has(interaction) && <div className={studentStyles.bottomActions}><button className={studentStyles.primaryWide} type="button" onClick={goNext}>متابعة المعاينة</button></div>}
              </section></main>
            </>
          )}
        </div>
        <div className={styles.navBar}>
          <div className={styles.navGroup}><button type="button" className={styles.navButton} onClick={goPrevious} disabled={firstPosition}><ChevronRight size={18} /> السابق</button><button type="button" className={styles.navButtonPrimary} onClick={showCelebration ? advancePastCurrentItem : goNext} disabled={journeyDone}>{journeyDone ? "تم" : lastPosition && !showCelebration ? "إنهاء المعاينة" : "التالي"}<ChevronLeft size={18} /></button></div>
          <span className={styles.position}>{currentSection.label} · {itemLabel}</span>
        </div>
      </section>
    </div>
  );
}
