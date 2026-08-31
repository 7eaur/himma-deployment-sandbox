"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpLeft, BarChart3, CheckCircle2, Clock3, FileSpreadsheet, FileText, RefreshCw, Sparkles, Users } from "lucide-react";

interface ResearchStudentReport {
  student_id: number;
  student_name: string;
  status: "active" | "inactive";
  starting_level: number | null;
  current_level: number;
  final_level: number | null;
  completed_core_levels: number[];
  pretest: { status: string; score: number | null; elapsed_seconds: number };
  posttest: { status: string; score: number | null; elapsed_seconds: number };
  improvement: {
    absolute_percentage_points: number | null;
    relative_percent: number | null;
    relative_percent_defined: boolean;
  };
  engagement: {
    assessment_seconds: number;
    learning_seconds: number;
    attempts: number;
    completed_attempts: number;
  };
  reinforcement: { total: number; verified: number; escalated: number; active: number };
  speech_evidence: { calibrated: boolean; error_categories: unknown | null; note: string };
}

interface ResearchSummary {
  cohort: {
    students: number;
    active_students: number;
    completed_pretests: number;
    completed_posttests: number;
    paired_pre_post: number;
    average_pretest_score: number | null;
    average_posttest_score: number | null;
    average_absolute_improvement_points: number | null;
    reinforcement_cycles: number;
    verified_reinforcement_cycles: number;
    escalated_reinforcement_cycles: number;
  };
  students: ResearchStudentReport[];
  reporting_notes: {
    score_source: string;
    relative_improvement: string;
    speech_metrics: string;
  };
}

function formatScore(value: number | null) {
  return value == null ? "—" : `${Math.round(value * 10) / 10}%`;
}

function formatSeconds(value: number) {
  if (value <= 0) return "—";
  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return minutes ? `${minutes} د ${seconds ? `${seconds} ث` : ""}`.trim() : `${seconds} ث`;
}

function improvementLabel(report: ResearchStudentReport) {
  const value = report.improvement.absolute_percentage_points;
  if (value == null) return { text: "بانتظار البعدي", className: "badge-gray" };
  if (value > 0) return { text: `+${Math.round(value * 10) / 10} نقطة`, className: "badge-green" };
  if (value < 0) return { text: `${Math.round(value * 10) / 10} نقطة`, className: "badge-yellow" };
  return { text: "دون تغير", className: "badge-gray" };
}

async function fetchResearchSummary(): Promise<ResearchSummary> {
  const response = await fetch("/api/researcher/reports/summary", { cache: "no-store" });
  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload) throw new Error(payload?.detail || "تعذر تحميل التقرير البحثي");
  return payload as ResearchSummary;
}

export default function ReportsPage() {
  const [data, setData] = useState<ResearchSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      setData(await fetchResearchSummary());
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "تعذر تحميل التقرير البحثي");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    fetchResearchSummary()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل التقرير البحثي");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto" dir="rtl">
      <div className="mb-7 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p className="text-sm text-primary font-semibold mb-1">بيانات البحث الفعلية</p>
          <h1 className="text-3xl font-bold text-navy mb-2">التقارير والإحصائيات</h1>
          <p className="text-muted max-w-3xl">مقارنة القبلي والبعدي والزمن والتقوية من القيم المحفوظة في قاعدة البيانات، دون إعادة احتساب التصنيف أو اختراع مؤشرات صوتية غير معايرة.</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <a className="btn-secondary min-h-11" href="/api/researcher/reports/exports/cohort.xlsx">
            <FileSpreadsheet size={17} aria-hidden="true" /> Excel
          </a>
          <a className="btn-secondary min-h-11" href="/api/researcher/reports/exports/cohort.pdf">
            <FileText size={17} aria-hidden="true" /> PDF إجمالي
          </a>
          <button className="btn-secondary min-h-11" onClick={() => void refresh()} disabled={loading}>
            <RefreshCw size={17} aria-hidden="true" /> تحديث البيانات
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
        <div aria-label="جاري تجهيز التقرير" className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {[0, 1, 2, 3].map((item) => <div key={item} className="card min-h-28 animate-pulse bg-slate-50" />)}
          </div>
          <div className="card min-h-72 animate-pulse bg-slate-50" />
        </div>
      ) : data ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
            <div className="stat-card"><div className="stat-card-icon blue"><Users size={23} /></div><div><p className="stat-card-value">{data.cohort.students}</p><p className="stat-card-label">إجمالي الطلاب</p></div></div>
            <div className="stat-card"><div className="stat-card-icon green"><CheckCircle2 size={23} /></div><div><p className="stat-card-value">{data.cohort.paired_pre_post}</p><p className="stat-card-label">مقارنات قبلي/بعدي مكتملة</p></div></div>
            <div className="stat-card"><div className="stat-card-icon yellow"><BarChart3 size={23} /></div><div><p className="stat-card-value">{formatScore(data.cohort.average_absolute_improvement_points)}</p><p className="stat-card-label">متوسط التحسن بالنقاط</p></div></div>
            <div className="stat-card"><div className="stat-card-icon blue"><Sparkles size={23} /></div><div><p className="stat-card-value">{data.cohort.verified_reinforcement_cycles}/{data.cohort.reinforcement_cycles}</p><p className="stat-card-label">دورات تقوية متحققة</p></div></div>
          </div>

          <section className="card mb-6">
            <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
              <div>
                <h2 className="font-bold text-navy text-lg">ملخص الاختبارات</h2>
                <p className="text-sm text-muted mt-1">القيم التالية مأخوذة من جلسات الاختبار المكتملة والمحفوظة.</p>
              </div>
              <div className="flex gap-2 flex-wrap">
                <span className="badge badge-gray">قبلي مكتمل: {data.cohort.completed_pretests}</span>
                <span className="badge badge-gray">بعدي مكتمل: {data.cohort.completed_posttests}</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-2xl border border-slate-200 p-4"><p className="text-sm text-muted">متوسط القبلي</p><strong className="text-2xl text-navy">{formatScore(data.cohort.average_pretest_score)}</strong></div>
              <div className="rounded-2xl border border-slate-200 p-4"><p className="text-sm text-muted">متوسط البعدي</p><strong className="text-2xl text-navy">{formatScore(data.cohort.average_posttest_score)}</strong></div>
              <div className="rounded-2xl border border-slate-200 p-4"><p className="text-sm text-muted">متوسط التحسن المطلق</p><strong className="text-2xl text-navy">{data.cohort.average_absolute_improvement_points == null ? "—" : `${data.cohort.average_absolute_improvement_points > 0 ? "+" : ""}${Math.round(data.cohort.average_absolute_improvement_points * 10) / 10} نقطة`}</strong></div>
            </div>
          </section>

          <section className="card">
            <div className="flex items-center justify-between gap-3 mb-5 flex-wrap">
              <div><h2 className="font-bold text-navy text-lg">نتائج الطلاب</h2><p className="text-sm text-muted mt-1">المستوى الابتدائي والنهائي والنتائج والزمن والتقوية لكل طالب.</p></div>
              <Link href="/admin/students" className="text-primary text-sm font-semibold inline-flex items-center gap-1">إدارة الطلاب <ArrowUpLeft size={15} /></Link>
            </div>

            {data.students.length === 0 ? (
              <div className="empty-state py-10"><h3>لا توجد بيانات بعد</h3><p>أضف الطلاب وابدأ الاختبار القبلي لتظهر بيانات البحث هنا.</p><Link className="btn-primary mt-4" href="/admin/students/new">إضافة أول طالب</Link></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead><tr><th>الطالب</th><th>المستوى</th><th>القبلي</th><th>البعدي</th><th>التحسن</th><th>الزمن</th><th>التقوية</th><th>تقرير</th></tr></thead>
                  <tbody>
                    {data.students.map((student) => {
                      const improvement = improvementLabel(student);
                      return (
                        <tr key={student.student_id}>
                          <td><Link href={`/admin/students/${student.student_id}`} className="font-semibold text-navy hover:text-primary">{student.student_name}</Link></td>
                          <td><span className="whitespace-nowrap">{student.starting_level ? `L${student.starting_level}` : "—"} ← {student.final_level ? `L${student.final_level}` : `L${student.current_level}`}</span></td>
                          <td>{formatScore(student.pretest.score)}</td>
                          <td>{formatScore(student.posttest.score)}</td>
                          <td><span className={`badge ${improvement.className}`}>{improvement.text}</span></td>
                          <td><span className="inline-flex items-center gap-1 whitespace-nowrap"><Clock3 size={14} className="text-muted" />{formatSeconds(student.engagement.assessment_seconds + student.engagement.learning_seconds)}</span></td>
                          <td>{student.reinforcement.verified}/{student.reinforcement.total}</td>
                          <td><a className="text-primary text-sm font-semibold whitespace-nowrap" href={`/api/researcher/reports/students/${student.student_id}/export.pdf`}>PDF فردي</a></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-muted leading-7">
            <strong className="text-navy">ملاحظة منهجية:</strong> التحسن النسبي لا يُحسب عندما تكون نتيجة القبلي صفرًا. كما تبقى مؤشرات أخطاء النطق الآلية غير معروضة حتى اعتماد دليل صوتي معاير. جميع عمليات تصدير Excel وPDF تُسجل في سجل العمليات.
          </div>
        </>
      ) : null}
    </div>
  );
}
