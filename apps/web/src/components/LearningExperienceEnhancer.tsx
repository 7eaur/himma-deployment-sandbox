"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

type Asset = { asset_id: string; asset_type: string; url: string; semantic_text?: string | null; option_id?: number | null };
type Round = {
  round_number: number;
  round_total: number;
  skill: string;
  encouragement: string;
  hint: string;
  question_text: string;
  instruction_text: string;
  stimulus_text?: string;
};
type Projection = { version: string; item_id: number; stable_key: string; kind: string; interaction_type: string; round: Round; retry: boolean; assets: Asset[]; step_assets: Asset[] };

function setText(node: Element | null, value: string) {
  if (node && node.textContent !== value) node.textContent = value;
}

function createMemoryPanel(projection: Projection, stage: HTMLElement, onReady: () => void) {
  const panel = document.createElement("div");
  panel.dataset.manualMemoryPreview = `${projection.item_id}:${projection.round.round_number}`;
  panel.className = "learningMemoryPreview";

  const lead = document.createElement("p");
  lead.className = "learningMemoryLead";
  lead.textContent = "شاهد الصور جيدًا وركّز في ترتيبها";
  panel.appendChild(lead);

  const images = projection.step_assets.filter((asset) => asset.asset_type === "image" && asset.option_id);
  const grid = document.createElement("div");
  grid.className = "learningMemoryGrid";
  images.forEach((asset, index) => {
    const card = document.createElement("div");
    card.className = "learningMemoryCard";
    const num = document.createElement("b");
    num.textContent = String(index + 1);
    const img = document.createElement("img");
    img.src = asset.url;
    img.alt = asset.semantic_text || `الصورة ${index + 1}`;
    const label = document.createElement("span");
    label.textContent = asset.semantic_text || "";
    card.append(num, img, label);
    grid.appendChild(card);
  });
  panel.appendChild(grid);

  const note = document.createElement("p");
  note.className = "learningMemoryNote";
  note.textContent = "عندما تنتهي من التركيز، اضغط «التالي» ثم أعد ترتيب الصور كما ظهرت.";
  panel.appendChild(note);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "learningMemoryNext";
  button.textContent = "التالي";
  button.onclick = () => {
    const reveal = () => {
      if (stage.dataset.memoryPhase === "recall") {
        panel.remove();
        stage.style.display = "";
        onReady();
        return true;
      }
      return false;
    };
    if (!reveal()) {
      button.disabled = true;
      button.textContent = "جاري التجهيز…";
      const timer = window.setInterval(() => {
        if (reveal()) window.clearInterval(timer);
      }, 80);
    }
  };
  panel.appendChild(button);
  stage.insertAdjacentElement("afterend", panel);
  return panel;
}

export default function LearningExperienceEnhancer() {
  const pathname = usePathname();
  const match = pathname.match(/\/student\/activity\/([^/]+)/);
  const sessionId = match?.[1];
  const [projection, setProjection] = useState<Projection | null>(null);
  const memoryReady = useRef<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    let timer: number | null = null;
    const load = async () => {
      try {
        const response = await fetch(`/api/learning-experience/session/${sessionId}`, { cache: "no-store" });
        if (!response.ok) return;
        const data = (await response.json()) as Projection | null;
        if (!cancelled && data) setProjection(data);
      } catch {
        // Presentation enhancement must never break the learning route.
      }
    };
    void load();
    timer = window.setInterval(() => void load(), 900);
    return () => {
      cancelled = true;
      if (timer) window.clearInterval(timer);
    };
  }, [sessionId]);

  useEffect(() => {
    if (!projection) return;
    const key = `${projection.item_id}:${projection.round.round_number}`;
    if (memoryReady.current && memoryReady.current !== key) memoryReady.current = null;

    const apply = () => {
      const root = document.querySelector<HTMLElement>('[data-testid="activity-session"][data-phase="active"]');
      if (!root) return;

      const title = root.querySelector<HTMLElement>('[data-testid="student-task-instruction"]');
      setText(title, projection.round.question_text);

      let instruction = root.querySelector<HTMLElement>('[data-learning-instruction="true"]');
      if (!instruction && title) {
        instruction = document.createElement("p");
        instruction.dataset.learningInstruction = "true";
        title.insertAdjacentElement("afterend", instruction);
      }
      if (instruction) setText(instruction, projection.round.instruction_text);

      const prompt = root.querySelector<HTMLElement>('[data-testid="student-task-prompt"]');
      const stimulus = String(projection.round.stimulus_text || "").trim();
      if (prompt) {
        if (stimulus) {
          setText(prompt, stimulus);
          prompt.style.display = "";
        } else {
          prompt.style.display = "none";
        }
      }

      const helpers = root.querySelectorAll<HTMLElement>('[data-testid="contextual-hint"], [data-testid="motivational-helper"]');
      helpers.forEach((helper, index) => {
        if (index > 0) {
          helper.style.display = "none";
          return;
        }
        helper.style.display = "";
        const helperText = helper.querySelector("p");
        if (helperText) setText(helperText, projection.retry ? projection.round.hint : projection.round.encouragement);
        helper.dataset.helperState = projection.retry ? "retry" : "normal";
      });

      const levelPill = root.querySelector<HTMLElement>("[data-learning-skill]");
      if (levelPill) setText(levelPill, projection.round.skill);

      const roundPill = root.querySelector<HTMLElement>("[data-learning-round]")
        || Array.from(root.querySelectorAll<HTMLElement>("span")).find((node) => /الجولة\s+\d+/u.test(node.textContent || ""));
      if (roundPill) {
        setText(roundPill, `الجولة ${projection.round.round_number} من ${projection.round.round_total}`);
        roundPill.dataset.roundPosition = "top-left";
      }

      if (projection.interaction_type === "memory_sequence" && memoryReady.current !== key) {
        const stage = root.querySelector<HTMLElement>('[data-testid="memory-stage"]');
        if (stage) {
          stage.style.display = "none";
          const existing = root.querySelector<HTMLElement>(`[data-manual-memory-preview="${key}"]`);
          if (!existing) createMemoryPanel(projection, stage, () => { memoryReady.current = key; });
        }
      }
    };

    const frame = window.requestAnimationFrame(apply);
    const observer = new MutationObserver(apply);
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [projection]);

  return null;
}
