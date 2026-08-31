"use client";

import { useEffect, useState } from "react";
import { BarChart3, Download, RefreshCw } from "lucide-react";

interface SkillEvidenceRow {
  level: number;
  skill_code: string;
  skill_name: string;
  graded_responses: number;
  correct_responses: number;
  incorrect_responses: number;
  observed_accuracy_percent: number | null;
  evidence_scope: string;
  is_mastery_score: false;
}

interface SkillEvidencePayload {
  cohort_skills: SkillEvidenceRow[];
  students: Array<{ student_id: number; student_name: string; skills: SkillEvidenceRow[] }>;
  methodology: {
    source: string;
    retry_policy: string;
    academic_effect: string;
    speech: string;
  };
}

async function fetchSkillEvidence(): Promise<SkillEvidencePayload> {
  const response = await fetch("/api/researcher/reports/skills", { cache: "no-store" });
  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload) throw new Error(payload?.detail || "تعذر تحميل ملخص المهارات");
  return payload as SkillEvidencePayload;
}

export default function SkillReportsPage() {
  const [data, setData] = useState<SkillEvidencePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      setData(await fetchSkillEvidence());
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "تعذر تحميل ملخص المهارات");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    fetchSkillEvidence()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل ملخص المهارات");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const totalObservations = data?.cohort_skills.reduce((sum, row) => sum + row.graded_responses, 0) ?? 0;
  const observedSkills = data?.cohort_skills.length ?? 0;

  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto" dir="rtl">
      <div className="mb-7 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="text-sm text-primary font-semibold mb-1">دليل بحثي وصفي</p>
          <h1 className="text-3xl font-bold text-navy mb-2">ملخص المهارات</h1>
          <p className="text-muted max-w-3xl">
            يلخص الاستجابات المصححة والمخزنة حسب المهارة. هذه النسب وصفية للتقرير فقط، وليست درجة إتقان ولا تغير التصنيف أو مسار الطالب.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <a className="btn-secondary min-h-11" href="/api/researcher/reports/exports/skills.xlsx">
            <Download size={17} aria-hidden="true" /> تصدير المهارات Excel
          </a>
          <button className="btn-secondary min-h-11" onClick={() => void refresh()} disabled={loading}>
            <RefreshCw size={17} aria-hidden="true" /> تحديث
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-error mb-5 flex items-center justify-between gap-3 flex-wrap">
          <span>{error}</span>
          <button className="btn-secondary" onClick={() => void refresh()}>إعادة المحاولة</button>
        </div>
      )}

      {loading ? (
        <div aria-label="جاري تجهيز ملخص المهارات" className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="card min-h-28 animate-pulse bg-slate-50" />
            <div className="card min-h-28 animate-pulse bg-slate-50" />
          </div>
          <div className="card min-h-72 animate-pulse bg-slate-50" />
        </div>
      ) : data ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <div className="stat-card">
              <div className="stat-card-icon blue"><BarChart3 size={23} /></div>
              <div><p className="stat-card-value">{observedSkills}</p><p className="stat-card-label">مهارات لها دليل مخزن</p></div>
            </div>
            <div className="stat-card">
              <div className="stat-card-icon green"><BarChart3 size={23} /></div>
              <div><p className="stat-card-value">{totalObservations}</p><p className="stat-card-label">استجابات مقيمة</p></div>
            </div>
          </div>

          <section className="card">
            <div className="mb-5">
              <h2 className="font-bold text-navy text-lg">الدليل حسب المهارة</h2>
              <p className="text-sm text-muted mt-1">تُحسب الدقة المرصودة من الاستجابات التي تحمل حكمًا صحيح/غير صحيح فقط.</p>
            </div>

            {data.cohort_skills.length === 0 ? (
              <div className="empty-state py-10">
                <h3>لا توجد استجابات مقيمة بعد</h3>
                <p>ستظهر المهارات هنا بعد حفظ إجابات مصححة للطلاب.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr><th>المستوى</th><th>المهارة</th><th>الاستجابات</th><th>صحيح</th><th>غير صحيح</th><th>الدقة المرصودة</th></tr>
                  </thead>
                  <tbody>
                    {data.cohort_skills.map((row) => (
                      <tr key={`${row.level}-${row.skill_code}`}>
                        <td>L{row.level}</td>
                        <td><div className="font-semibold text-navy">{row.skill_name}</div><div className="text-xs text-muted mt-1">{row.skill_code}</div></td>
                        <td>{row.graded_responses}</td>
                        <td>{row.correct_responses}</td>
                        <td>{row.incorrect_responses}</td>
                        <td>{row.observed_accuracy_percent == null ? "—" : `${row.observed_accuracy_percent}%`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-muted leading-7">
            <strong className="text-navy">حدود التقرير:</strong> المحاولات المعادة تبقى ملاحظات مستقلة كما حُفظت، ولا يطبق هذا التقرير أوزان 50/30/20 أو أي قاعدة ترقية. ولا يعرض أخطاء نطق آلية قبل اعتماد الدليل الصوتي المُعاير.
          </div>
        </>
      ) : null}
    </div>
  );
}
