"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { KeyRound } from "lucide-react";

export default function StudentLogin() {
  const router = useRouter();
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/auth/me", { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json().catch(() => null);
        if (!cancelled && response.ok && data?.role === "student") {
          router.replace("/student");
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [router]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!/^\d{6}$/.test(accessCode)) {
      setError("اكتب رمز الدخول المكوّن من 6 أرقام.");
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await fetch("/api/auth/student-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_code: accessCode }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        setError(data?.detail || "رمز الدخول غير صحيح. تحقّق من الأرقام وحاول مرة أخرى.");
        return;
      }
      router.replace("/student");
      router.refresh();
    } catch {
      setError("تعذر الاتصال بالخادم الآن. حاول مرة أخرى بعد قليل.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="student-login-root" dir="rtl">
      <div className="student-login-amb-1" />
      <div className="student-login-amb-2" />

      <div className="student-login-card">
        <div className="flex justify-center student-login-logo">
          <Image src="/brand/logo-gradient.svg" alt="منصة هِمّة" width={180} height={60} priority />
        </div>

        <div className="flex justify-center mb-5">
          <Image
            src="/characters/boy/welcome.png"
            alt="شخصية هِمّة ترحب بالطالب"
            width={140}
            height={180}
            className="drop-shadow-md"
            priority
          />
        </div>

        <h1 className="student-login-title">مرحبًا يا بطل!</h1>
        <p className="student-login-sub">أدخل رمزك الرقمي المكوّن من 6 أرقام لنبدأ رحلتك.</p>

        {error && (
          <div data-testid="error-message" className="alert-error text-center mb-6 font-bold" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <label htmlFor="student-access-code" className="block text-sm text-navy font-semibold mb-2 text-right">
            رمز الدخول
          </label>
          <div className="relative mb-4">
            <input
              id="student-access-code"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              className="student-login-code-input"
              data-testid="input-access-code"
              value={accessCode}
              onChange={(event) => setAccessCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="123456"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              dir="ltr"
              aria-describedby="access-code-help"
            />
            <KeyRound size={19} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted pointer-events-none" aria-hidden="true" />
          </div>
          <p id="access-code-help" className="text-xs text-muted mb-5 text-right">ستجد الرمز عند المشرف المسؤول عن حسابك.</p>

          <button
            type="submit"
            className="student-login-btn"
            data-testid="student-login-submit"
            disabled={isLoading || accessCode.length !== 6}
          >
            {isLoading ? <span className="spinner mx-auto border-4" /> : "ابدأ الآن"}
          </button>
        </form>
      </div>
    </div>
  );
}
