"use client";

import { useEffect, useState } from "react";
import { enhancePromptLoudness } from "@/lib/student-experience";

type Tone = "select" | "listen";

const STORAGE_KEY = "himma:student-ui-sounds";

function initialSoundPreference() {
  if (typeof window === "undefined") return true;
  return window.localStorage.getItem(STORAGE_KEY) !== "off";
}

function tonePattern(kind: Tone) {
  if (kind === "listen") return [[440, 0.06, 0.035], [620, 0.07, 0.04]] as const;
  return [[560, 0.045, 0.045]] as const;
}

function playTone(kind: Tone, enabled: boolean) {
  if (!enabled || typeof window === "undefined") return;
  const AudioContextCtor = window.AudioContext
    || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextCtor) return;

  const context = new AudioContextCtor();
  const master = context.createGain();
  master.gain.value = 0.14;
  master.connect(context.destination);

  let cursor = context.currentTime;
  for (const [frequency, duration, gain] of tonePattern(kind)) {
    const oscillator = context.createOscillator();
    const envelope = context.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    envelope.gain.setValueAtTime(0, cursor);
    envelope.gain.linearRampToValueAtTime(gain, cursor + 0.012);
    envelope.gain.exponentialRampToValueAtTime(0.001, cursor + duration);
    oscillator.connect(envelope);
    envelope.connect(master);
    oscillator.start(cursor);
    oscillator.stop(cursor + duration + 0.015);
    cursor += duration + 0.025;
  }

  window.setTimeout(() => void context.close(), 450);
}

export default function StudentExperienceEffects() {
  const [enabled] = useState(initialSoundPreference);

  useEffect(() => {
    // Student prompt audio is created with `new Audio(...)` by the assessment
    // and learning runtimes. Wrap only that constructor while the student
    // subtree is mounted so same-origin educational speech receives the safe
    // gain/compressor boost; native recording previews remain untouched.
    const audioWindow = window as typeof window & { Audio: typeof Audio };
    const OriginalAudio = audioWindow.Audio;
    const EnhancedAudio = function EnhancedAudio(src?: string) {
      const audio = new OriginalAudio(src);
      enhancePromptLoudness(audio);
      return audio;
    } as unknown as typeof Audio;
    EnhancedAudio.prototype = OriginalAudio.prototype;

    try {
      audioWindow.Audio = EnhancedAudio;
    } catch {
      // Browsers that disallow constructor replacement still play at volume=1.
    }

    return () => {
      if (audioWindow.Audio === EnhancedAudio) audioWindow.Audio = OriginalAudio;
    };
  }, []);

  useEffect(() => {
    const rootSelector = '[data-testid="activity-session"], [data-testid="assessment-session"]';

    const onClick = (event: MouseEvent) => {
      const button = event.target instanceof Element ? event.target.closest("button") : null;
      if (!button || !button.closest(rootSelector) || button.hasAttribute("disabled")) return;

      const testId = button.getAttribute("data-testid") || "";
      if (testId === "listen-prompt" || testId === "activity-listen-prompt") {
        playTone("listen", enabled);
        return;
      }
      if (button.hasAttribute("aria-pressed")) {
        playTone("select", enabled);
      }
    };

    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, [enabled]);

  return null;
}
