"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { LockKeyhole, UserRound } from "lucide-react";

export default function AdminLogin() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store" });
        const data = await response.json().catch(() => null);
        if (response.ok && data?.role === "researcher") {
          router.replace("/admin");
        }
      } catch {
        // Login remains available when there is no valid session.
      }
    };
    void checkSession();
  }, [router]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        setError(data?.detail || "تعذر تسجيل الدخول. تحقق من البيانات وحاول مرة أخرى.");
        return;
      }

      router.replace("/admin");
      router.refresh();
    } catch {
      setError("تعذر الاتصال بالخادم الآن. حاول مرة أخرى بعد قليل.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="admin-login-root" dir="rtl">
      <div className="admin-login-brand">
        <Image src="/brand/logo-white.svg" alt="هِمّة" width={140} height={48} priority />
        <h2 className="admin-brand-title">بوابة المشرف</h2>
        <p className="admin-brand-sub">إدارة الطلاب ومتابعة تقدمهم من مكان واحد</p>
        <Image src="/characters/girl/welcome.png" alt="شخصية هِمّة" width={160} height={200} className="admin-brand-char" priority />
        <p className="admin-brand-tagline">أتعلم، أتطور، أصل إلى القمة</p>
      </div>

      <div className="admin-login-form-wrap">
        <div className="admin-login-form-box">
          <div className="md:hidden flex justify-center mb-8">
            <Image src="/brand/logo-navy.svg" alt="هِمّة" width={140} height={48} />
          </div>
          <h1>مرحبًا بك</h1>
          <p>أدخل بيانات حساب المشرف للوصول إلى لوحة الإدارة.</p>

          {error && (
            <div data-testid="error-message" className="alert-error text-center mb-4" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-navy font-medium mb-2" htmlFor="supervisor-username">اسم المستخدم</label>
              <div className="relative">
                <input
                  id="supervisor-username"
                  type="text"
                  className="input-field"
                  data-testid="input-username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                  dir="rtl"
                  placeholder="اكتب اسم المستخدم"
                />
                <UserRound size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
              </div>
            </div>

            <div>
              <label className="block text-navy font-medium mb-2" htmlFor="supervisor-password">كلمة المرور</label>
              <div className="relative">
                <input
                  id="supervisor-password"
                  type="password"
                  className="input-field"
                  data-testid="input-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  dir="ltr"
                  placeholder="••••••••"
                />
                <LockKeyhole size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary w-full mt-6"
              data-testid="login-submit"
              disabled={isLoading}
            >
              {isLoading ? <span className="spinner" /> : "تسجيل الدخول"}
            </button>
          </form>
          <p className="admin-login-hint">الدخول مخصص للمشرفين المخولين بإدارة المنصة.</p>
        </div>
      </div>
    </div>
  );
}
