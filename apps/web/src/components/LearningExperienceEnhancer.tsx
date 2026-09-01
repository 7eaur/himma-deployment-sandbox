"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

type Asset = { asset_id: string; asset_type: string; url: string; semantic_text?: string | null; option_id?: number | null };
type Round = { round_number: number; round_total: number; skill: string; encouragement: string; hint: string; question_text: string; instruction_text: string };
type Projection = { version: string; item_id: number; stable_key: string; kind: string; interaction_type: string; round: Round; retry: boolean; assets: Asset[]; step_assets: Asset[] };

function setText(node: Element | null, value: string) {
  if (node && node.textContent !== value) node.textContent = value;
}

function createMemoryPanel(projection: Projection, stage: HTMLElement, onReady: () => void) {
  const panel = document.createElement("div");
  panel.dataset.manualMemoryPreview = `${projection.item_id}:${projection.round.round_number}`;
  Object.assign(panel.style, {
    width: "min(100%, 820px)", margin: "4px auto 10px", display: "flex", flexDirection: "column",
    alignItems: "center", gap: "12px", position: "relative", zIndex: "3",
  });

  const lead = document.createElement("p");
  lead.textContent = "شاهد الصور جيدًا وركّز في ترتيبها";
  Object.assign(lead.style, { margin: "0", fontWeight: "900", color: "#405c72", fontSize: "clamp(.95rem, 1.5vw, 1.08rem)" });
  panel.appendChild(lead);

  const images = projection.step_assets.filter((asset) => asset.asset_type === "image" && asset.option_id);
  const grid = document.createElement("div");
  Object.assign(grid.style, { width: "100%", display: "grid", gridTemplateColumns: `repeat(${Math.max(1, images.length)}, minmax(0, 1fr))`, gap: "clamp(8px, 1.4vw, 14px)" });
  images.forEach((asset, index) => {
    const card = document.createElement("div");
    Object.assign(card.style, { minHeight: "135px", border: "2px solid #dce8f2", borderRadius: "20px", background: "#fff", padding: "9px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "5px", position: "relative" });
    const num = document.createElement("b");
    num.textContent = String(index + 1);
    Object.assign(num.style, { position: "absolute", top: "8px", right: "8px", width: "27px", height: "27px", borderRadius: "50%", display: "grid", placeItems: "center", background: "#edf5ff", color: "#2466b8", fontSize: ".75rem" });
    const img = document.createElement("img");
    img.src = asset.url; img.alt = asset.semantic_text || `الصورة ${index + 1}`;
    Object.assign(img.style, { width: "100%", height: "min(115px, 15vh)", objectFit: "contain" });
    const label = document.createElement("span"); label.textContent = asset.semantic_text || "";
    Object.assign(label.style, { fontWeight: "900", fontSize: ".82rem" });
    card.append(num, img, label); grid.appendChild(card);
  });
  panel.appendChild(grid);

  const note = document.createElement("p");
  note.textContent = "عندما تنتهي من التركيز، اضغط «التالي» ثم أعد ترتيب الصور كما ظهرت.";
  Object.assign(note.style, { margin: "0", textAlign: "center", color: "#657d91", fontWeight: "800", fontSize: "clamp(.78rem, 1.3vw, .92rem)" });
  panel.appendChild(note);

  const button = document.createElement("button");
  button.type = "button"; button.textContent = "التالي";
  Object.assign(button.style, { minWidth: "130px", minHeight: "44px", border: "0", borderRadius: "16px", padding: "8px 24px", background: "#347fd9", color: "white", fontWeight: "900", cursor: "pointer", fontFamily: "inherit", fontSize: ".95rem" });
  button.onclick = () => {
    const reveal = () => {
      if (stage.dataset.memoryPhase === "recall") {
        panel.remove(); stage.style.display = ""; onReady(); return true;
      }
      return false;
    };
    if (!reveal()) {
      button.disabled = true; button.textContent = "جاري التجهيز…";
      const timer = window.setInterval(() => { if (reveal()) window.clearInterval(timer); }, 80);
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
      } catch { /* presentation enhancement must not break the learning route */ }
    };
    void load();
    timer = window.setInterval(() => void load(), 900);
    return () => { cancelled = true; if (timer) window.clearInterval(timer); };
  }, [sessionId]);

  useEffect(() => {
    if (!projection) return;
    const key = `${projection.item_id}:${projection.round.round_number}`;
    if (memoryReady.current && memoryReady.current !== key) memoryReady.current = null;

    const apply = () => {
      const root = document.querySelector<HTMLElement>('[data-testid="activity-session"][data-phase="active"]');
      if (!root) return;

      setText(root.querySelector('[data-testid="student-task-instruction"]'), projection.round.question_text);
      const title = root.querySelector<HTMLElement>('[data-testid="student-task-instruction"]');
      if (title) {
        title.style.fontSize = "clamp(1.28rem, 2.15vw, 2rem)";
        title.style.lineHeight = "1.35";
      }

      let instruction = root.querySelector<HTMLElement>('[data-learning-instruction="true"]');
      if (!instruction && title) {
        instruction = document.createElement("p");
        instruction.dataset.learningInstruction = "true";
        title.insertAdjacentElement("afterend", instruction);
      }
      if (instruction) {
        setText(instruction, projection.round.instruction_text);
        Object.assign(instruction.style, { margin: "0 auto 8px", color: "#657d91", fontSize: "clamp(.78rem, 1.25vw, .92rem)", lineHeight: "1.5", textAlign: "center", fontWeight: "750", maxWidth: "760px", zIndex: "2" });
      }

      const helper = root.querySelector<HTMLElement>('[data-testid="contextual-hint"], [data-testid="motivational-helper"]');
      const helperText = helper?.querySelector("p");
      if (helperText) setText(helperText, projection.retry ? projection.round.hint : projection.round.encouragement);

      const roundPill = Array.from(root.querySelectorAll<HTMLElement>("span")).find((node) => /الجولة\s+\d+/u.test(node.textContent || ""));
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
    return () => { window.cancelAnimationFrame(frame); observer.disconnect(); };
  }, [projection]);

  return null;
}
