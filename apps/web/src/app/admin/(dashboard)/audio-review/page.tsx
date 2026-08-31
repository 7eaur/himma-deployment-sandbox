"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Headphones, Play, RefreshCw, RotateCcw, UserRound, XCircle } from "lucide-react";

interface AudioSubmission {
  id: number;
  storage_key: string;
  status: string;
  submitted_at: string;
  student_id?: number | null;
  student_name?: string | null;
  session_type?: string | null;
  item_title?: string | null;
  expected_reading_text?: string | null;
}

function AudioPlayer({ storageKey }: { storageKey: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadRecording = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`/api/recordings/stream-by-key?key=${encodeURIComponent(storageKey)}`);
      const data = await response.json().catch(() => null);
      if (!response.ok || !data?.url) throw new Error(data?.detail || "تعذر تحميل التسجيل");
      setSrc(data.url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "تعذر تحميل التسجيل");
    } finally {
      setLoading(false);
    }
  };

  if (src) return <audio src={src} controls className="w-full max-w-xl" preload="metadata" />;

  return (
    <div className="space-y-2">
      <button type="button" className="btn-secondary" onClick={() => void loadRecording()} disabled={loading}>
        <Play size={16} /> {loading ? "جاري التحميل..." : "تشغيل التسجيل"}
      </button>
      {error && <p className="alert-error text-sm">{error}</p>}
    </div>
  );
}

function sessionLabel(value?: string | null) {
  if (value === "pretest") return "الاختبار القبلي";
  if (value === "posttest") return "الاختبار البعدي";
  if (value === "core") return "نشاط تعليمي";
  return "قراءة مسجلة";
}

export default function AudioReviewPage() {
  const [submissions, setSubmissions] = useState<AudioSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });
  const [gradingId, setGradingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const editingRef = useRef<number | null>(null);
  const [isValid, setIsValid] = useState(true);
  const [targetUnits, setTargetUnits] = useState(10);
  const [deletions, setDeletions] = useState(0);
  const [substitutions, setSubstitutions] = useState(0);
  const [insertions, setInsertions] = useState(0);
  const [pronunciationNotes, setPronunciationNotes] = useState("");
  const [fluencyNotes, setFluencyNotes] = useState("");

  useEffect(() => {
    editingRef.current = editingId;
  }, [editingId]);

  useEffect(() => {
    let cancelled = false;

    const fetchQueue = () => {
      // Do not replace the queue while a supervisor is actively grading a card.
      // Periodic refresh previously could detach the live form between pointer
      // down/up and also discard notes typed by the supervisor.
      if (editingRef.current !== null) return;
      void fetch("/api/review/pending-audio", { cache: "no-store" })
        .then(async (response) => {
          if (!response.ok) throw new Error("تعذر تحميل التسجيلات المنتظرة");
          const data: AudioSubmission[] = await response.json();
          if (!cancelled && editingRef.current === null) setSubmissions(data);
        })
        .catch((caught: unknown) => {
          if (!cancelled) setMessage({ kind: "error", text: caught instanceof Error ? caught.message : "تعذر تحميل التسجيلات" });
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    };

    fetchQueue();
    const interval = window.setInterval(fetchQueue, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const refreshQueue = async () => {
    if (editingId !== null) {
      setMessage({ kind: "error", text: "أكمل المراجعة الحالية أو ألغها قبل تحديث القائمة." });
      return;
    }
    setRefreshing(true);
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch("/api/review/pending-audio", { cache: "no-store" });
      if (!response.ok) throw new Error("تعذر تحديث قائمة التسجيلات");
      setSubmissions(await response.json());
    } catch (caught) {
      setMessage({ kind: "error", text: caught instanceof Error ? caught.message : "تعذر تحديث القائمة" });
    } finally {
      setRefreshing(false);
    }
  };

  const openReview = (id: number) => {
    editingRef.current = id;
    setEditingId(id);
    setIsValid(true);
    setTargetUnits(10);
    setDeletions(0);
    setSubstitutions(0);
    setInsertions(0);
    setPronunciationNotes("");
    setFluencyNotes("");
    setMessage({ kind: "success", text: "" });
  };

  const closeReview = () => {
    editingRef.current = null;
    setEditingId(null);
  };

  const handleGrade = async (id: number) => {
    setGradingId(id);
    setMessage({ kind: "success", text: "" });
    try {
      const payload = {
        is_valid: isValid,
        target_units: isValid ? targetUnits : undefined,
        deletions: isValid ? deletions : 0,
        substitutions: isValid ? substitutions : 0,
        insertions: isValid ? insertions : 0,
        pronunciation_notes: pronunciationNotes || undefined,
        fluency_notes: fluencyNotes || undefined,
      };
      const response = await fetch(`/api/review/audio/${id}/grade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر حفظ التقييم");
      setSubmissions((current) => current.filter((submission) => submission.id !== id));
      editingRef.current = null;
      setEditingId(null);
      setMessage({ kind: "success", text: isValid ? "تم حفظ تقييم التسجيل." : "تم طلب إعادة التسجيل من الطالب." });
    } catch (caught) {
      setMessage({ kind: "error", text: caught instanceof Error ? caught.message : "تعذر حفظ التقييم" });
    } finally {
      setGradingId(null);
    }
  };

  return (
    <div className="flex-1 font-plex max-w-5xl w-full mx-auto" dir="rtl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-7">
        <div>
          <p className="text-sm text-primary font-semibold mb-1">المراجعة اليدوية</p>
          <h1 className="text-3xl font-bold text-navy mb-2">التسجيلات الصوتية</h1>
          <p className="text-muted">استمع إلى قراءة الطالب مع النص المرجعي، ثم سجّل الأخطاء أو اطلب إعادة التسجيل.</p>
        </div>
        <button className="btn-secondary w-fit" onClick={() => void refreshQueue()} disabled={refreshing || editingId !== null}><RefreshCw size={17} /> {refreshing ? "جاري التحديث..." : "تحديث القائمة"}</button>
      </div>

      {message.text && <div className={`${message.kind === "success" ? "alert-success" : "alert-error"} mb-5`}>{message.text}</div>}

      {loading ? (
        <div className="card min-h-64 flex flex-col items-center justify-center gap-3"><div className="spinner w-10 h-10" /><p className="text-muted">جاري تحميل التسجيلات...</p></div>
      ) : submissions.length === 0 ? (
        <div className="card min-h-80 flex flex-col items-center justify-center text-center gap-3">
          <CheckCircle2 size={54} className="text-green" />
          <h2 className="text-xl font-bold text-navy">لا توجد تسجيلات بانتظار المراجعة</h2>
          <p className="text-muted">كل التسجيلات المرفوعة تمت معالجتها حاليًا.</p>
        </div>
      ) : (
        <div className="space-y-5">
          {submissions.map((submission, index) => (
            <article key={submission.id} className="card">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-border pb-4 mb-5">
                <div className="flex items-start gap-3">
                  <div className="w-11 h-11 rounded-xl bg-primary/10 text-primary flex items-center justify-center"><Headphones size={22} /></div>
                  <div>
                    <p className="text-xs text-muted mb-1">التسجيل {index + 1} من {submissions.length}</p>
                    <h2 className="font-bold text-navy text-lg">{submission.student_name || "طالب"}</h2>
                    <p className="text-sm text-muted">{sessionLabel(submission.session_type)}{submission.item_title ? ` · ${submission.item_title}` : ""}</p>
                  </div>
                </div>
                <div className="text-sm text-muted">{new Date(submission.submitted_at).toLocaleString("ar-SA")}</div>
              </div>

              {submission.student_id && <Link href={`/admin/students/${submission.student_id}`} className="inline-flex items-center gap-2 text-primary text-sm font-semibold mb-4"><UserRound size={16} /> فتح ملف الطالب</Link>}

              {submission.expected_reading_text && (
                <div className="rounded-2xl bg-bg border border-border p-5 mb-5">
                  <p className="text-xs text-muted mb-2">النص المرجعي الذي طُلب من الطالب قراءته</p>
                  <p className="text-2xl font-bold text-navy leading-loose">{submission.expected_reading_text}</p>
                </div>
              )}

              <div className="rounded-2xl border border-border bg-white p-4 mb-5"><AudioPlayer storageKey={submission.storage_key} /></div>

              {editingId !== submission.id ? (
                <button className="btn-primary" onClick={() => openReview(submission.id)} disabled={editingId !== null}>بدء المراجعة</button>
              ) : (
                <div className="rounded-2xl bg-bg border border-border p-5 space-y-5" data-testid={`audio-review-editor-${submission.id}`}>
                  <div>
                    <p className="font-bold text-navy mb-3">صلاحية التسجيل</p>
                    <div className="flex gap-3 flex-wrap">
                      <button className={`btn-secondary ${isValid ? "border-green text-green" : ""}`} onClick={() => setIsValid(true)}><CheckCircle2 size={17} /> تسجيل صالح</button>
                      <button className={`btn-secondary ${!isValid ? "border-red-300 text-red-600" : ""}`} onClick={() => setIsValid(false)}><XCircle size={17} /> يحتاج إعادة تسجيل</button>
                    </div>
                  </div>

                  {isValid ? (
                    <>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <label className="text-sm text-navy">الوحدات المستهدفة<input type="number" min={1} className="input-field mt-2" value={targetUnits} onChange={(event) => setTargetUnits(Number(event.target.value))} /></label>
                        <label className="text-sm text-navy">الحذف<input type="number" min={0} className="input-field mt-2" value={deletions} onChange={(event) => setDeletions(Number(event.target.value))} /></label>
                        <label className="text-sm text-navy">الاستبدال<input type="number" min={0} className="input-field mt-2" value={substitutions} onChange={(event) => setSubstitutions(Number(event.target.value))} /></label>
                        <label className="text-sm text-navy">الإضافة<input type="number" min={0} className="input-field mt-2" value={insertions} onChange={(event) => setInsertions(Number(event.target.value))} /></label>
                      </div>
                      <div className="grid md:grid-cols-2 gap-3">
                        <label className="text-sm text-navy">ملاحظات النطق<textarea className="input-field mt-2 min-h-24" value={pronunciationNotes} onChange={(event) => setPronunciationNotes(event.target.value)} placeholder="ملاحظة اختيارية" /></label>
                        <label className="text-sm text-navy">ملاحظات الطلاقة<textarea className="input-field mt-2 min-h-24" value={fluencyNotes} onChange={(event) => setFluencyNotes(event.target.value)} placeholder="ملاحظة اختيارية" /></label>
                      </div>
                    </>
                  ) : (
                    <div className="rounded-xl bg-white border border-border p-4 flex items-start gap-3 text-sm text-muted"><RotateCcw size={18} className="text-primary mt-0.5" /><p>عند الحفظ سيُعاد فتح محاولة الطالب ليتمكن من تسجيل القراءة مرة أخرى، ولن تُحتسب القراءة غير الصالحة.</p></div>
                  )}

                  <div className="flex justify-end gap-3 flex-wrap">
                    <button className="btn-ghost" onClick={closeReview} disabled={gradingId === submission.id}>إلغاء</button>
                    <button className="btn-primary" onClick={() => void handleGrade(submission.id)} disabled={gradingId === submission.id}>{gradingId === submission.id ? "جاري الحفظ..." : isValid ? "حفظ التقييم" : "طلب إعادة التسجيل"}</button>
                  </div>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
