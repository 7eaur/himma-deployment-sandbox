"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { CheckCircle2, Clock3, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import styles from "./student-adaptive-hold.module.css";

interface AdaptationStatus {
  ready?: boolean;
  explanation?: Record<string, unknown>;
}

export default function StudentAdaptiveHoldOverlay() {
  const router = useRouter();
  const [held, setHeld] = useState(false);
  const [checking, setChecking] = useState(false);
  const checkingRef = useRef(false);

  const poll = useCallback(async () => {
    if (checkingRef.current) return;
    checkingRef.current = true;
    try {
      const response = await fetch("/api/adaptation/status", { cache: "no-store" });
      if (!response.ok) return;
      const data: AdaptationStatus = await response.json();
      setHeld(Boolean(data.explanation?.mapping_gap));
    } catch {
      // The activity page keeps its own recoverable network handling.
    } finally {
      checkingRef.current = false;
    }
  }, []);

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
    <div className={styles.overlay} dir="rtl" data-testid="student-adaptive-hold" role="dialog" aria-modal="true" aria-labelledby="adaptive-hold-title">
      <div className={styles.viewport}>
        <section className={styles.card}>
          <div className={styles.grid}>
            <div className={styles.copy}>
              <span className={styles.badge}>
                <CheckCircle2 size={17} aria-hidden="true" /> أنهيت خطوتك بنجاح
              </span>
              <h1 id="adaptive-hold-title" className={styles.title}>أحسنت! نجهّز لك الخطوة الأنسب.</h1>
              <p className={styles.description}>لاحظت هِمّة أن اختيار نشاط التقوية التالي يحتاج مراجعة المشرف حتى تحصل على تدريب مناسب فعلًا، وليس نشاطًا عشوائيًا.</p>
              <div className={styles.notice}>
                <Clock3 size={20} aria-hidden="true" />
                <p><strong>لا يوجد خطأ في إجابتك.</strong><br />يمكنك العودة إلى مسارك الآن، وبعد أن يحدد المشرف نشاط التقوية سيظهر لك عند المتابعة.</p>
              </div>
              <div className={styles.actions}>
                <button className={styles.primary} onClick={() => router.push("/student")}>العودة إلى مساري</button>
                <button className={styles.secondary} disabled={checking} onClick={() => void manualCheck()}>
                  <RefreshCw size={17} aria-hidden="true" /> {checking ? "جاري الفحص..." : "تحقق من الخطوة"}
                </button>
              </div>
            </div>
            <div className={styles.visual}>
              <div className={styles.visualLabel}>المشرف يراجع المسار</div>
              <Image src="/characters/girl/encourage.png" alt="شخصية هِمّة تشجع الطالب" width={310} height={330} className={styles.character} priority />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
