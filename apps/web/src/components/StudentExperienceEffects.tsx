"use client";

import { useEffect, useRef, useState } from "react";
import { Award } from "lucide-react";
import styles from "./StudentExperienceEffects.module.css";

type Tone = "select" | "listen" | "success" | "retry" | "transition" | "award";
type Reward = { kind: "award"; text: string } | null;

const STORAGE_KEY = "himma:student-ui-sounds";

function initialSoundPreference() {
  if (typeof window === "undefined") return true;
  return window.localStorage.getItem(STORAGE_KEY) !== "off";
}

function tonePattern(kind: Tone) {
  switch (kind) {
    case "select": return [[560, .045, .045]] as const;
    case "listen": return [[440, .06, .035], [620, .07, .04]] as const;
    case "success": return [[520, .06, .04], [660, .07, .04], [820, .09, .05]] as const;
    case "retry": return [[330, .08, .035], [280, .09, .03]] as const;
    case "award": return [[520, .06, .04], [690, .07, .045], [880, .11, .05]] as const;
    default: return [[460, .045, .03], [560, .055, .03]] as const;
  }
}

function playTone(kind: Tone, enabled: boolean) {
  if (!enabled || typeof window === "undefined") return;
  const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextCtor) return;
  const context = new AudioContextCtor();
  const master = context.createGain();
  master.gain.value = .11;
  master.connect(context.destination);
  let cursor = context.currentTime;
  for (const [frequency, duration, gain] of tonePattern(kind)) {
    const oscillator = context.createOscillator();
    const envelope = context.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    envelope.gain.setValueAtTime(0, cursor);
    envelope.gain.linearRampToValueAtTime(gain, cursor + .012);
    envelope.gain.exponentialRampToValueAtTime(.001, cursor + duration);
    oscillator.connect(envelope);
    envelope.connect(master);
    oscillator.start(cursor);
    oscillator.stop(cursor + duration + .015);
    cursor += duration + .025;
  }
  window.setTimeout(() => void context.close(), 650);
}

export default function StudentExperienceEffects() {
  const [enabled] = useState(initialSoundPreference);
  const [taskVisible, setTaskVisible] = useState(false);
  const [reward, setReward] = useState<Reward>(null);
  const lastSignalRef = useRef("");
  const rewardTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const rootSelector = '[data-testid="activity-session"], [data-testid="assessment-session"]';

    const updateTaskVisibility = () => {
      setTaskVisible(Boolean(document.querySelector(rootSelector)));
    };
    updateTaskVisibility();

    const showReward = (next: Reward, sound: Tone) => {
      if (!next) return;
      setReward(next);
      playTone(sound, enabled);
      if (rewardTimerRef.current) window.clearTimeout(rewardTimerRef.current);
      rewardTimerRef.current = window.setTimeout(() => setReward(null), 1500);
    };

    const inspect = () => {
      updateTaskVisibility();
      const root = document.querySelector<HTMLElement>(rootSelector);
      if (!root) return;
      const text = root.innerText || "";
      const phase = root.dataset.phase || "";

      if (phase === "waiting_audio_review") {
        lastSignalRef.current = "waiting_audio_review";
        setReward(null);
        return;
      }

      // Do not infer correctness from encouragement copy such as "أحسنت" or
      // "رائع". Those phrases are part of the approved round content and can be
      // present before the learner answers. Pop-up rewards are reserved for a
      // real terminal completion state only.
      let signal = "";
      if (phase === "done") signal = `done:${text.slice(0, 120)}`;
      else if (/قريب جدًا|حاول مرة أخرى|جرّب مرة أخرى/u.test(text)) signal = `retry:${text.slice(-180)}`;

      if (!signal || signal === lastSignalRef.current) return;
      lastSignalRef.current = signal;
      if (signal.startsWith("done:")) showReward({ kind: "award", text: "إنجاز جديد في رحلتك" }, "award");
      else if (signal.startsWith("retry:")) playTone("retry", enabled);
    };

    const onClick = (event: MouseEvent) => {
      const target = event.target instanceof Element ? event.target.closest("button") : null;
      if (!target || !target.closest(rootSelector) || target.hasAttribute("disabled")) return;
      const label = (target.textContent || target.getAttribute("aria-label") || "").trim();
      if (/استمع/u.test(label)) playTone("listen", enabled);
      else if (target.hasAttribute("aria-pressed")) playTone("select", enabled);
      else if (/تأكيد|متابعة|إرسال|التالي/u.test(label)) playTone("transition", enabled);
    };

    document.addEventListener("click", onClick, true);
    const observer = new MutationObserver(inspect);
    observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["data-phase"] });
    inspect();

    return () => {
      document.removeEventListener("click", onClick, true);
      observer.disconnect();
      if (rewardTimerRef.current) window.clearTimeout(rewardTimerRef.current);
    };
  }, [enabled]);

  if (!taskVisible || !reward) return null;

  return (
    <div className={styles.reward} role="status" aria-live="polite">
      <Award className={styles.award} size={30} aria-hidden="true" />
      <span>{reward.text}</span>
    </div>
  );
}
