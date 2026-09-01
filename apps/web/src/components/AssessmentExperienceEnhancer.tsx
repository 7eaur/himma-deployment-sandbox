"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

type Experience = {
  version: string;
  question_number: number;
  section: string;
  skill: string;
  encouragement: string;
  question_text: string;
  instruction_text: string;
  interaction_type: string;
  stimulus?: { kind?: string; text?: string; audio_target?: string };
};
type Payload = {
  kind: string;
  template_data?: { posttest_experience?: Experience } | null;
  steps: Array<{ instruction_text?: string | null; prompt_text: string; expected_reading_text?: string | null }>;
};

function setText(node: Element | null, value?: string) {
  if (node && value && node.textContent !== value) node.textContent = value;
}

export default function AssessmentExperienceEnhancer() {
  const pathname = usePathname();
  const match = pathname.match(/\/student\/session\/([^/]+)/);
  const sessionId = match?.[1];
  const [payload, setPayload] = useState<Payload | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    const load = async () => {
      const root = document.querySelector('[data-testid="assessment-session"][data-phase="question"]');
      if (!root) return;
      try {
        const response = await fetch(`/api/assessment/session/${sessionId}/next`, { cache: "no-store" });
        if (!response.ok) return;
        const data = (await response.json()) as Payload | null;
        if (!cancelled && data?.kind === "posttest_question" && data.template_data?.posttest_experience) setPayload(data);
      } catch { /* rendering enhancement must not break assessment */ }
    };
    void load();
    const timer = window.setInterval(() => void load(), 900);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [sessionId]);

  useEffect(() => {
    const experience = payload?.template_data?.posttest_experience;
    if (!experience) return;
    const apply = () => {
      const root = document.querySelector<HTMLElement>('[data-testid="assessment-session"][data-phase="question"]');
      if (!root) return;
      setText(root.querySelector('[data-testid="question-title"]'), experience.question_text);

      const stimulusKind = experience.stimulus?.kind || "none";
      const stimulusText = experience.stimulus?.text;
      if (stimulusKind === "text" && stimulusText) setText(root.querySelector('[data-testid="question-stimulus"]'), stimulusText);
      if (stimulusKind === "reading" && stimulusText) setText(root.querySelector('[data-testid="reading-text"]'), stimulusText);

      const oldInstruction = payload?.steps?.[0]?.instruction_text?.trim();
      if (oldInstruction) {
        const paragraph = Array.from(root.querySelectorAll("p")).find((node) => (node.textContent || "").trim() === oldInstruction);
        setText(paragraph || null, experience.instruction_text);
      }

      const coach = root.querySelector<HTMLElement>('aside[aria-label="نصيحة هِمّة"]');
      if (coach) {
        const target = coach.querySelector("span:last-child") || coach.querySelector("span");
        setText(target, experience.encouragement);
      }
    };
    const frame = window.requestAnimationFrame(apply);
    const observer = new MutationObserver(apply);
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    return () => { window.cancelAnimationFrame(frame); observer.disconnect(); };
  }, [payload]);

  return null;
}
