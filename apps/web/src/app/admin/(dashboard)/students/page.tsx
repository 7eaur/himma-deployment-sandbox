"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Eye, Search, UserPlus } from "lucide-react";

interface Student {
  id: number;
  full_name: string;
  grade_level: number;
  access_code: string;
  created_at: string;
  current_level: number;
  status: "active" | "inactive";
  core_completed_items: number;
  core_total_items: number;
  posttest_enabled: boolean;
}

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | "active" | "inactive">("all");

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/researcher/students", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("تعذر تحميل قائمة الطلاب");
        const data: Student[] = await response.json();
        if (!cancelled) setStudents(data);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل الطلاب");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ar");
    return students.filter((student) => {
      const matchesStatus = status === "all" || student.status === status;
      const matchesQuery = !needle
        || student.full_name.toLocaleLowerCase("ar").includes(needle)
        || student.access_code.includes(needle);
      return matchesStatus && matchesQuery;
    });
  }, [query, status, students]);

  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto" dir="rtl">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 mb-7">
        <div>
          <p className="text-sm text-primary font-semibold mb-1">إدارة العينة</p>
          <h1 className="text-3xl font-bold text-navy mb-2">الطلاب</h1>
          <p className="text-muted">عرض الحسابات، الرموز، المستوى الحالي وتقدم الأنشطة.</p>
        </div>
        <Link href="/admin/students/new" className="btn-primary flex items-center gap-2 w-fit"><UserPlus size={18} /><span>إضافة طالب</span></Link>
      </div>

      {error && <div className="alert-error mb-5">{error}</div>}

      <section className="card">
        <div className="grid md:grid-cols-[1fr_180px_auto] gap-3 mb-6">
          <label className="relative">
            <span className="sr-only">البحث عن طالب</span>
            <input className="input-field pr-11" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ابحث بالاسم أو رمز الدخول" />
            <Search size={18} className="absolute right-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
          </label>
          <select className="input-field" value={status} onChange={(event) => setStatus(event.target.value as typeof status)} aria-label="تصفية حسب حالة الحساب">
            <option value="all">كل الحالات</option>
            <option value="active">نشط</option>
            <option value="inactive">موقوف</option>
          </select>
          <div className="rounded-xl bg-bg border border-border px-4 flex items-center justify-center text-sm text-muted">{filtered.length} من {students.length}</div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-14"><div className="spinner w-9 h-9" /><p className="text-muted">جاري تحميل الطلاب...</p></div>
        ) : students.length === 0 ? (
          <div className="empty-state">
            <Image src="/characters/girl/welcome.png" alt="شخصية هِمّة" width={115} height={150} />
            <h3>لا يوجد طلاب حتى الآن</h3>
            <p className="mb-6">أضف أول طالب ليبدأ استخدام المنصة.</p>
            <Link href="/admin/students/new" className="btn-primary">إضافة طالب جديد</Link>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state py-12"><Search size={36} className="mb-3" /><h3>لا توجد نتائج مطابقة</h3><p>جرّب اسمًا آخر أو غيّر التصفية.</p></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>الطالب</th><th>رمز الدخول</th><th>المستوى</th><th>تقدم الأنشطة</th><th>الحالة</th><th>التفاصيل</th></tr></thead>
              <tbody>
                {filtered.map((student) => {
                  const progress = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);
                  return (
                    <tr key={student.id}>
                      <td><div><Link href={`/admin/students/${student.id}`} className="font-semibold text-navy hover:text-primary">{student.full_name}</Link><p className="text-xs text-muted mt-1">أضيف {new Date(student.created_at).toLocaleDateString("ar-SA")}</p></div></td>
                      <td><span className="badge badge-gray border border-border tracking-widest px-3 py-1 font-mono" dir="ltr">{student.access_code}</span></td>
                      <td><span className="font-semibold text-navy">{student.current_level}</span></td>
                      <td><div className="flex items-center gap-2 min-w-[150px]"><div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div><span className="text-xs text-muted whitespace-nowrap">{student.core_completed_items}/{student.core_total_items}</span></div></td>
                      <td><span className={`badge ${student.status === "active" ? "badge-green" : "badge-gray"}`}>{student.status === "active" ? "نشط" : "موقوف"}</span></td>
                      <td><Link href={`/admin/students/${student.id}`} className="inline-flex items-center gap-2 text-primary font-semibold text-sm p-2 rounded-md hover:bg-primary/10" aria-label={`فتح ملف ${student.full_name}`}><Eye size={18} /> فتح</Link></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
