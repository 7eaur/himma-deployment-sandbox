"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { SkipForward } from "lucide-react";
import { useParams } from "next/navigation";

type Mode = "assessment" | "activity";

type CurrentRecordingTask = {
  itemId: number;
  stepId: number;
};

const RECORDING_INTERACTIONS = new Set(["read_aloud", "timed_read_aloud"]);

export default function TemporaryAudioSkipControl({ mode }: { mode: Mode }) {
  const params = useParams();
  const sessionId = String(params.id ?? "");
  const [enabled, setEnabled] = useState(false);
  const [portalTarget, setPortalTarget] = useState<HTMLElement | null>(null);
  const [task, setTask] = useState<CurrentRecordingTask | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/runtime-flags", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) return null;
        return response.json();
      })
      .then((data) => {
        if (!cancelled) setEnabled(Boolean(data?.temporary_audio_skip));
      })
      .catch(() => {
        if (!cancelled) setEnabled(false);
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const selector = mode === "assessment"
      ? '[data-testid="reading-text"]'
      : '[data-testid="activity-reading-text"]';

    const syncTarget = () => {
      const reading = document.querySelector(selector);
      const candidate = reading?.nextElementSibling;
      setPortalTarget(candidate instanceof HTMLElement ? candidate : null);
      if (!candidate) setTask(null);
    };

    const kickoff = window.setTimeout(syncTarget, 0);
    const observer = new MutationObserver(syncTarget);
    observer.observe(document.body, { childList: true, subtree: true });
    return () => {
      window.clearTimeout(kickoff);
      observer.disconnect();
    };
  }, [enabled, mode]);

  useEffect(() => {
    if (!enabled || !portalTarget || !sessionId) return;
    let cancelled = false;
    const endpoint = mode === "assessment"
      ? `/api/assessment/session/${sessionId}/next`
      : `/api/activities/session/${sessionId}/next`;

    // The page has already opened the pending attempt before the recording DOM
    // exists, so this read only resolves the IDs for the temporary skip action.
    void fetch(endpoint, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) return null;
        return response.json();
      })
      .then((data) => {
        if (cancelled || !data) return;
        if (mode === "assessment") {
          if (!RECORDING_INTERACTIONS.has(String(data.interaction_type))) return;
          const step = data.steps?.[0];
          if (data.id && step?.id) setTask({ itemId: Number(data.id), stepId: Number(step.id) });
          return;
        }
        if (!RECORDING_INTERACTIONS.has(String(data.item?.interaction_type))) return;
        if (data.item?.id && data.step?.id) {
          setTask({ itemId: Number(data.item.id), stepId: Number(data.step.id) });
        }
      })
      .catch(() => {
        if (!cancelled) setTask(null);
      });

    return () => { cancelled = true; };
  }, [enabled, mode, portalTarget, sessionId]);

  const skip = async () => {
    if (!task || submitting) return;
    if (document.querySelector('button[aria-label="إيقاف التسجيل"]')) {
      setMessage("أوقف التسجيل الحالي أولًا، ثم استخدم التخطي المؤقت.");
      return;
    }

    setSubmitting(true);
    setMessage("");
    try {
      const response = await fetch(
        `/api/temporary-audio/session/${sessionId}/attempt/${task.itemId}/skip`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": crypto.randomUUID(),
          },
          body: JSON.stringify({ step_id: task.stepId, elapsed_seconds: 0 }),
        },
      );
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تخطي مهمة التسجيل");

      // TEMPORARY — reload lets the existing accepted runner resume from the
      // next pending step without modifying the real MediaRecorder path.
      window.location.reload();
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "تعذر تخطي مهمة التسجيل");
      setSubmitting(false);
    }
  };

  if (!enabled || !portalTarget || !task) return null;

  return createPortal(
    <div
      data-testid="temporary-audio-skip"
      style={{
        width: "100%",
        marginTop: "14px",
        paddingTop: "14px",
        borderTop: "1px solid #DCE8F2",
        textAlign: "center",
      }}
    >
      <button
        type="button"
        onClick={() => void skip()}
        disabled={submitting}
        style={{
          minHeight: "44px",
          borderRadius: "14px",
          border: "1px solid #347FD9",
          background: "#F7FBFF",
          color: "#20364D",
          padding: "10px 18px",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          fontWeight: 700,
          cursor: submitting ? "wait" : "pointer",
          opacity: submitting ? 0.65 : 1,
        }}
      >
        <SkipForward size={18} aria-hidden="true" />
        {submitting ? "جاري التخطي..." : "تخطي مؤقتًا"}
      </button>
      <p style={{ margin: "8px auto 0", maxWidth: "520px", color: "#60758A", fontSize: "13px", lineHeight: 1.7 }}>
        التسجيل الصوتي قيد التجهيز، ويمكنك تخطي هذه المهمة أثناء تجربة المنصة.
      </p>
      {message && (
        <p role="status" aria-live="polite" style={{ margin: "6px auto 0", color: "#20364D", fontSize: "13px" }}>
          {message}
        </p>
      )}
    </div>,
    portalTarget,
  );
}
