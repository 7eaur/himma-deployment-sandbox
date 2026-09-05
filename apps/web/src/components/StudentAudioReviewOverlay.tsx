"use client";

import Image from "next/image";
import { useParams } from "next/navigation";
import { Clock3, Mic2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import styles from "./student-adaptive-hold.module.css";

type LearningReviewState = {
  audio_review_status?: string | null;
  awaiting_audio_review?: boolean;
};

const WAITING = new Set(["uploaded", "pending"]);

export default function StudentAudioReviewOverlay() {
  const params = useParams<{ id: string }>();
  const sessionId = String(params?.id || "");
  const [held, setHeld] = useState(false);
  const [checking, setChecking] = useState(false);
  const checkingRef = useRef(false);
  const wasHeldRef = useRef(false);

  const poll = useCallback(async () => {
    if (!sessionId || checkingRef.current) return;
    checkingRef.current = true;
    try {
      const response = await fetch(`/api/learning-experience/session/${sessionId}`, { cache: "no-store" });
      if (!response.ok) return;
      const data: LearningReviewState | null = await response.json();
      const waiting = Boolean(
        data?.awaiting_audio_review || (data?.audio_review_status && WAITING.has(data.audio_review_status)),
      );
      setHeld(waiting);
      if (wasHeldRef.current && !waiting) {
        window.location.reload();
        return;
      }
      wasHeldRef.current = waiting;
    } catch {
      // The activity screen keeps its own recoverable network handling.
    } finally {
      checkingRef.current = false;
    }
  }, [sessionId]);

  const manualCheck = async () => {
    setChecking(true);
    try {
      await poll();
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    const first = window.setTimeout(() => void poll(), 0);
    const timer = window.setInterval(() => void poll(), 1800);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(timer);
    };
  }, [poll]);

  if (!held) return null;

  return (
    <div
      className={styles.overlay}
      dir="rtl"
      data-testid="student-audio-review-hold"
      role="dialog"
      aria-modal="true"
      aria-labelledby="audio-review-hold-title"
    >
      <div className={styles.viewport}>
        <section className={styles.card}>
          <div className={styles.grid}>
            <div className={styles.copy}>
              <span className={styles.badge}>
                <Mic2 size={17} aria-hidden="true" /> تم حفظ تسجيلك
              </span>
              <h1 id="audio-review-hold-title" className={styles.title}>تسجيلك الآن عند المشرف للمراجعة</h1>
              <p className={styles.description}>
                لن تُحتسب الجولة صحيحة أو مكتملة قبل المراجعة. بعد اعتماد التسجيل ستتابع تلقائيًا، وإذا احتاج إلى إعادة تسجيل ستظهر لك الجولة من جديد.
              </p>
              <div className={styles.notice}>
                <Clock3 size={20} aria-hidden="true" />
                <p><strong>لا تحتاج إلى إرسال التسجيل مرة أخرى الآن.</strong><br />انتظر قرار المشرف، فالتسجيل المحفوظ هو الدليل المعتمد لهذه الجولة.</p>
              </div>
              <div className={styles.actions}>
                <button className={styles.secondary} disabled={checking} onClick={() => void manualCheck()}>
                  <RefreshCw size={17} aria-hidden="true" /> {checking ? "جاري التحقق..." : "تحقق من المراجعة"}
                </button>
              </div>
            </div>
            <div className={styles.visual}>
              <div className={styles.visualLabel}>مراجعة التسجيل</div>
              <Image
                src="/characters/girl/encourage.png"
                alt="شخصية هِمّة تشجع الطالب أثناء انتظار مراجعة التسجيل"
                width={310}
                height={330}
                className={styles.character}
                priority
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
