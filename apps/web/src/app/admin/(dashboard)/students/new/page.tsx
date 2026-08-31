"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Copy, CheckCircle, RefreshCw, KeyRound } from "lucide-react";

const generatePreviewCode = () => String(Math.floor(100000 + Math.random() * 900000));

export default function NewStudentPage() {
  const [fullName, setFullName] = useState("");
  const [codeMode, setCodeMode] = useState<"auto" | "manual">("auto");
  const [manualCode, setManualCode] = useState("");
  const [previewCode, setPreviewCode] = useState(generatePreviewCode());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [successCode, setSuccessCode] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    if (codeMode === "manual" && !/^\d{6}$/.test(manualCode)) {
      setError("رمز الدخول اليدوي يجب أن يتكون من 6 أرقام.");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/researcher/students", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          grade_level: 3,
          access_code: codeMode === "manual" ? manualCode : undefined,
        }),
      });
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        setError(data?.detail || "تعذر إضافة الطالب. تحقق من البيانات وحاول مرة أخرى.");
        return;
      }
      setSuccessCode(data.access_code);
    } catch {
      setError("تعذر الاتصال بالخادم الآن. حاول مرة أخرى بعد قليل.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(successCode);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  if (successCode) {
    return (
      <div className="flex-1 font-plex max-w-2xl mx-auto w-full" dir="rtl">
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-green/10 text-green rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle size={32} />
          </div>
          <h2 className="text-2xl font-bold text-navy mb-2">تمت إضافة الطالب بنجاح</h2>
          <p className="text-muted mb-8">أعطِ الطالب رمز الدخول الرقمي التالي. يمكن تغييره لاحقًا من صفحة الطالب.</p>

          <div className="bg-bg p-6 rounded-xl border border-border mb-8 max-w-sm mx-auto">
            <p className="text-sm text-muted mb-2">رمز دخول الطالب</p>
            <div className="flex items-center justify-center gap-4" dir="ltr">
              <span className="text-4xl font-mono font-bold text-primary tracking-widest" data-testid="student-access-code">
                {successCode}
              </span>
              <button onClick={() => void copyToClipboard()} className="p-2 text-muted hover:text-primary hover:bg-white rounded-md transition-colors" title="نسخ الرمز" aria-label="نسخ رمز الدخول">
                {copied ? <CheckCircle size={20} className="text-green" /> : <Copy size={20} />}
              </button>
            </div>
          </div>

          <div className="flex justify-center gap-4 flex-wrap">
            <button
              onClick={() => {
                setSuccessCode("");
                setFullName("");
                setManualCode("");
                setCodeMode("auto");
                setPreviewCode(generatePreviewCode());
              }}
              className="btn-secondary"
            >
              إضافة طالب آخر
            </button>
            <Link href="/admin/students" className="btn-primary">العودة إلى الطلاب</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 font-plex max-w-2xl mx-auto w-full" dir="rtl">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/admin/students" className="p-2 text-muted hover:text-navy hover:bg-bg rounded-full transition-colors" aria-label="العودة إلى الطلاب">
          <ArrowRight size={24} />
        </Link>
        <div>
          <p className="text-sm text-primary font-semibold">إدارة الطلاب</p>
          <h1 className="text-2xl font-bold text-navy">إضافة طالب جديد</h1>
        </div>
      </div>

      <div className="card">
        {error && <div className="alert-error mb-6" role="alert">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-navy font-medium mb-2" htmlFor="student-name">اسم الطالب</label>
            <input
              id="student-name"
              type="text"
              className="input-field"
              data-testid="input-student-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="مثال: سالم"
              required
              minLength={2}
            />
            <p className="text-sm text-muted mt-2">استخدم الاسم أو الاسم المستعار المعتمد في الدراسة.</p>
          </div>

          <div>
            <label className="block text-navy font-medium mb-2">الصف الدراسي</label>
            <div className="input-field bg-bg text-muted">الصف الثالث الابتدائي</div>
            <p className="text-sm text-muted mt-2">عينة الدراسة معتمدة لطلاب الصف الثالث فقط.</p>
          </div>

          <div className="border border-border rounded-xl p-5 bg-bg/60">
            <div className="flex items-center gap-3 mb-4">
              <div className="rounded-full bg-white p-2 text-primary"><KeyRound size={20} /></div>
              <div>
                <h2 className="font-bold text-navy">رمز دخول الطالب</h2>
                <p className="text-sm text-muted">رمز رقمي سهل مكوّن من 6 أرقام.</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <button type="button" onClick={() => setCodeMode("auto")} className={`border rounded-lg px-4 py-3 font-semibold transition-colors ${codeMode === "auto" ? "border-primary bg-white text-primary" : "border-border text-muted"}`}>
                توليد تلقائي
              </button>
              <button type="button" onClick={() => setCodeMode("manual")} className={`border rounded-lg px-4 py-3 font-semibold transition-colors ${codeMode === "manual" ? "border-primary bg-white text-primary" : "border-border text-muted"}`}>
                إدخال يدوي
              </button>
            </div>

            {codeMode === "auto" ? (
              <div className="flex items-center justify-between gap-4 bg-white rounded-lg border border-border p-4">
                <div>
                  <p className="text-xs text-muted mb-1">مثال للرمز الذي سيُنشأ</p>
                  <p className="text-2xl font-mono font-bold text-navy tracking-widest" dir="ltr">{previewCode}</p>
                </div>
                <button type="button" onClick={() => setPreviewCode(generatePreviewCode())} className="btn-secondary" aria-label="تغيير مثال الرمز">
                  <RefreshCw size={17} /> مثال آخر
                </button>
              </div>
            ) : (
              <div>
                <label className="block text-sm text-navy font-medium mb-2" htmlFor="manual-code">اكتب 6 أرقام</label>
                <input
                  id="manual-code"
                  className="input-field text-center text-2xl font-mono tracking-widest"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="123456"
                  dir="ltr"
                />
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-border flex justify-end gap-4">
            <Link href="/admin/students" className="btn-ghost">إلغاء</Link>
            <button type="submit" className="btn-primary" data-testid="submit-create-student" disabled={isLoading}>
              {isLoading ? <span className="spinner" /> : "إضافة الطالب"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
