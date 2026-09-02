"use client";

import { useEffect, useState } from "react";
import { BarChart3, Download, RefreshCw } from "lucide-react";
import {
  AdminAction,
  AdminEmptyState,
  AdminMobileCard,
  AdminPage,
  AdminPageHeader,
  AdminPanel,
  AdminResponsiveTable,
  AdminStat,
  AdminStatGrid,
} from "@/components/admin/AdminUI";

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
      .then((payload) => { if (!cancelled) setData(payload); })
      .catch((caught: unknown) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل ملخص المهارات"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const totalObservations = data?.cohort_skills.reduce((sum, row) => sum + row.graded_responses, 0) ?? 0;
  const observedSkills = data?.cohort_skills.length ?? 0;

  return (
    <AdminPage>
      <AdminPageHeader
        eyebrow="دليل بحثي وصفي"
        icon={BarChart3}
        title="ملخص المهارات"
        description="يلخص الاستجابات المصححة والمخزنة حسب المهارة. هذه النسب وصفية للتقرير فقط، وليست درجة إتقان ولا تغير التصنيف أو مسار الطالب."
        actions={<>
          <AdminAction href="/api/researcher/reports/exports/skills.xlsx" icon={Download}>تصدير Excel</AdminAction>
          <AdminAction icon={RefreshCw} disabled={loading} onClick={() => void refresh()}>تحديث</AdminAction>
        </>}
      />

      {error && <div className="alert-error flex items-center justify-between gap-3 flex-wrap"><span>{error}</span><AdminAction onClick={() => void refresh()}>إعادة المحاولة</AdminAction></div>}

      {loading ? (
        <div aria-label="جاري تجهيز ملخص المهارات" className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4"><div className="card min-h-28 animate-pulse bg-slate-50" /><div className="card min-h-28 animate-pulse bg-slate-50" /></div>
          <div className="card min-h-72 animate-pulse bg-slate-50" />
        </div>
      ) : data ? (
        <>
          <AdminStatGrid>
            <AdminStat icon={BarChart3} value={observedSkills} label="مهارات لها دليل مخزن" />
            <AdminStat icon={BarChart3} value={totalObservations} label="استجابات مقيمة" />
          </AdminStatGrid>

          <AdminPanel title="الدليل حسب المهارة" description="تُحسب الدقة المرصودة من الاستجابات التي تحمل حكمًا صحيح/غير صحيح فقط.">
            {data.cohort_skills.length === 0 ? (
              <AdminEmptyState title="لا توجد استجابات مقيمة بعد" description="ستظهر المهارات هنا بعد حفظ إجابات مصححة للطلاب." />
            ) : (
              <AdminResponsiveTable
                table={<table className="data-table"><thead><tr><th>المستوى</th><th>المهارة</th><th>الاستجابات</th><th>صحيح</th><th>غير صحيح</th><th>الدقة المرصودة</th></tr></thead><tbody>{data.cohort_skills.map((row) => <tr key={`${row.level}-${row.skill_code}`}><td>L{row.level}</td><td><div className="font-semibold text-navy">{row.skill_name}</div><div className="text-xs text-muted mt-1">{row.skill_code}</div></td><td>{row.graded_responses}</td><td>{row.correct_responses}</td><td>{row.incorrect_responses}</td><td>{row.observed_accuracy_percent == null ? "—" : `${row.observed_accuracy_percent}%`}</td></tr>)}</tbody></table>}
                cards={data.cohort_skills.map((row) => <AdminMobileCard key={`${row.level}-${row.skill_code}`} title={row.skill_name}><span><strong>المستوى:</strong> L{row.level}</span><span><strong>الاستجابات:</strong> {row.graded_responses}</span><span><strong>صحيح:</strong> {row.correct_responses}</span><span><strong>غير صحيح:</strong> {row.incorrect_responses}</span><span><strong>الدقة:</strong> {row.observed_accuracy_percent == null ? "—" : `${row.observed_accuracy_percent}%`}</span><span><strong>الرمز:</strong> {row.skill_code}</span></AdminMobileCard>)}
              />
            )}
          </AdminPanel>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-muted leading-7"><strong className="text-navy">حدود التقرير:</strong> المحاولات المعادة تبقى ملاحظات مستقلة كما حُفظت، ولا يطبق هذا التقرير أوزان 50/30/20 أو أي قاعدة ترقية. ولا يعرض أخطاء نطق آلية قبل اعتماد الدليل الصوتي المُعاير.</div>
        </>
      ) : null}
    </AdminPage>
  );
}
