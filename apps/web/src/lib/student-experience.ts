export type StudentRecoveryAction = "retry" | "dashboard" | "login";
export type FeedbackSound = "correct" | "incorrect" | "transition" | "complete";

/**
 * Classify student-runtime failures into a useful recovery route instead of
 * trapping the child on a dead session screen.
 */
export function classifyStudentRecovery(status: number, detail = ""): StudentRecoveryAction {
  if (status === 401) return "login";
  const normalized = detail.toLowerCase();
  const terminalDetail = /(غير موجود|غير متاح|انتهت|انتهى|مكتمل|مكتملة|مغلق|مغلقة|not found|expired|finished|closed|unavailable)/i.test(normalized);
  if (status === 403 || status === 404 || status === 410) return "dashboard";
  if (status >= 400 && status < 500 && terminalDetail) return "dashboard";
  return "retry";
}

/**
 * Fisher-Yates shuffle. Call once when a question/round payload changes so
 * choices stay visually stable while the child is selecting an answer, but
 * receive a fresh order on the next presentation/reload.
 */
export function shuffleForPresentation<T>(values: readonly T[]): T[] {
  const result = [...values];
  for (let index = result.length - 1; index > 0; index -= 1) {
    let random = Math.random();
    if (typeof globalThis.crypto?.getRandomValues === "function") {
      const sample = new Uint32Array(1);
      globalThis.crypto.getRandomValues(sample);
      random = sample[0] / 0x1_0000_0000;
    }
    const swapIndex = Math.floor(random * (index + 1));
    [result[index], result[swapIndex]] = [result[swapIndex], result[index]];
  }
  return result;
}

let feedbackContext: AudioContext | null = null;
let promptContext: AudioContext | null = null;

type WindowWithWebkitAudio = Window & typeof globalThis & {
  webkitAudioContext?: typeof AudioContext;
};

function audioContextConstructor() {
  if (typeof window === "undefined") return null;
  return window.AudioContext || (window as WindowWithWebkitAudio).webkitAudioContext || null;
}

/**
 * Give quiet same-origin educational prompts a modest loudness lift while a
 * compressor protects against harsh peaks. Cross-origin media remains on the
 * browser's normal full-volume path so a missing CORS header can never mute it.
 */
export function enhancePromptLoudness(audio: HTMLAudioElement, gainValue = 1.35) {
  audio.volume = 1;
  const AudioContextCtor = audioContextConstructor();
  if (!AudioContextCtor || typeof window === "undefined") return;

  try {
    const sourceUrl = new URL(audio.src, window.location.href);
    if (sourceUrl.origin !== window.location.origin) return;

    promptContext ??= new AudioContextCtor();
    const context = promptContext;
    if (context.state === "suspended") void context.resume();

    const source = context.createMediaElementSource(audio);
    const gain = context.createGain();
    const compressor = context.createDynamicsCompressor();
    gain.gain.value = Math.max(1, Math.min(1.6, gainValue));
    compressor.threshold.value = -14;
    compressor.knee.value = 18;
    compressor.ratio.value = 4;
    compressor.attack.value = 0.004;
    compressor.release.value = 0.2;
    source.connect(gain);
    gain.connect(compressor);
    compressor.connect(context.destination);
  } catch {
    // Full HTML-media volume is already set above; enhancement is optional.
  }
}

/**
 * Lightweight UI feedback tones generated locally. They do not depend on a
 * network asset and intentionally stay short/subtle so educational speech
 * remains the dominant audio channel.
 */
export function playFeedbackSound(kind: FeedbackSound) {
  const AudioContextCtor = audioContextConstructor();
  if (!AudioContextCtor) return;

  try {
    feedbackContext ??= new AudioContextCtor();
    const context = feedbackContext;
    if (context.state === "suspended") void context.resume();

    const patterns: Record<FeedbackSound, Array<[number, number, number]>> = {
      correct: [[660, 0, 0.09], [880, 0.09, 0.11]],
      incorrect: [[310, 0, 0.08], [250, 0.08, 0.1]],
      transition: [[520, 0, 0.07], [660, 0.07, 0.08]],
      complete: [[523, 0, 0.09], [659, 0.09, 0.09], [784, 0.18, 0.14]],
    };

    const now = context.currentTime;
    for (const [frequency, offset, duration] of patterns[kind]) {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(frequency, now + offset);
      gain.gain.setValueAtTime(0.0001, now + offset);
      gain.gain.exponentialRampToValueAtTime(kind === "incorrect" ? 0.07 : 0.11, now + offset + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + duration);
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start(now + offset);
      oscillator.stop(now + offset + duration + 0.01);
    }
  } catch {
    // Audio feedback is enhancement-only; never block the learning flow.
  }
}
