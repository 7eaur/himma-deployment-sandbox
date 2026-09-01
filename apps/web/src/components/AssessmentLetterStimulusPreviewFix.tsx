"use client";

import { useEffect } from "react";

/**
 * Sandbox-only presentation guard for the assessment letter-form question.
 *
 * The approved content separates the visible stimulus (a single letter) from
 * the instruction and answer options. The current assessment page still
 * renders the legacy prose prompt in the stimulus box, so this guard narrows
 * only that exact legacy sentence to the displayed letter without touching
 * answer options, scoring, skill mapping, or API data.
 */
export function extractAssessmentLetterStimulus(rawText: string) {
  const normalized = rawText.replace(/\s+/gu, " ").trim();
  const match = normalized.match(
    /^يظهر الحرف\s*[«"“]?([\u0621-\u064A])[»"”]?\s*[.،]?\s*اختر الشكل الآخر للحرف نفسه\s*[:：]/u,
  );
  return match?.[1] ?? null;
}

export default function AssessmentLetterStimulusPreviewFix() {
  useEffect(() => {
    const applyFix = () => {
      const root = document.querySelector<HTMLElement>(
        '[data-testid="assessment-session"][data-phase="question"]',
      );
      if (!root) return;

      root.querySelectorAll<HTMLElement>("div").forEach((element) => {
        if (element.children.length > 0) return;
        const stimulus = extractAssessmentLetterStimulus(element.textContent ?? "");
        if (!stimulus) return;

        if (element.textContent?.trim() !== stimulus) {
          element.textContent = stimulus;
        }
        element.dataset.assessmentStimulus = "letter-form";
        element.setAttribute("aria-label", `الحرف ${stimulus}`);
        element.style.fontSize = "clamp(3.5rem, 12vw, 5.5rem)";
        element.style.lineHeight = "1.15";
        element.style.minWidth = "6.5rem";
        element.style.padding = "0.7rem 1.5rem";
      });
    };

    const frame = window.requestAnimationFrame(applyFix);
    const observer = new MutationObserver(applyFix);
    observer.observe(document.body, { childList: true, characterData: true, subtree: true });

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, []);

  return null;
}
