"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Activity, ArrowLeft, BarChart3, BookOpenCheck, Headphones, Plus, ShieldCheck, Users } from "lucide-react";
import styles from "./admin.module.css";

interface Supervisor {
  id: number;
  full_name?: string;
  username?: string;
  role: string;
}

interface Student {
  id: number;
  full_name: string;
  grade_level: number;
  access_code: string;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible: boolean;
  core_completed_items: number;
  core_total_items: number;
  created_at: string;
}

export default function AdminDashboard() {
  const [supervisor, setSupervisor] = useState<Supervisor | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      fetch("/api/me", { cache: "no-store" }),
      fetch("/api/researcher/students", { cache: "no-store" }),
    ])
      .then(async ([meResponse, studentsResponse]) => {
        if (!meResponse.ok || !studentsResponse.ok) throw new Error("تعذر تحميل لوحة المشرف");
        const meData: Supervisor = await meResponse.json();
        const studentsData: Student[] = await studentsResponse.json();
        if (cancelled) return;
        setSupervisor(meData);
        setStudents(studentsData);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل لوحة المشرف");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeStudents = useMemo(() => students.filter((student) => student.status === "active").length, [students]);
  const learningStudents = useMemo(() => students.filter((student) => student.core_completed_items > 0 && student.core_completed_items < student.core_total_items).length, [students]);
  const readyForPosttest = useMemo(() => students.filter((student) => student.posttest_eligible || student.posttest_enabled).length, [students]);
  const inactiveStudents = useMemo(() => students.filter((student) => student.status !== "active").length, [students]);
  const recentStudents = useMemo(() => [...students].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)).slice(0, 6), [students]);
  const supervisorName = supervisor?.full_name || supervisor?.username || "المشرف";

  if (loading) {
    return (
      <div className={styles.loading} dir="rtl" data-testid="admin-dashboard-loading">
        <div className={styles.loadingHeader} />
        <div className={styles.loadingStats}>
          <span /><span /><span /><span />
        </div>
        <div className={styles.loadingPanel} />
      </div>
    );
  }

  return (
    <div className={styles.dashboard} dir="rtl">
      <header className={styles.hero}>
        <div>
          <div className={styles.eyebrow}><ShieldCheck size={17} /> مركز متابعة المنصة</div>
          <h1>مرحبًا، {supervisorName}</h1>
          <p>ابدأ بما يحتاج انتباهك، ثم تابع تقدم الطلاب والاختبارات والتسجيلات من مكان واحد.</p>
        </div>
        <Link href="/admin/students/new" className={styles.primaryAction}><Plus size={19} /> إضافة طالب</Link>
      </header>

      {error && <div className="alert-error">{error}</div>}

      <section className={styles.actionCenter} aria-labelledby="attention-title">
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionKicker}>الأولوية الآن</span>
            <h2 id="attention-title">ما الذي يحتاج انتباهك؟</h2>
          </div>
          <p>إجراءات مباشرة بدل البحث بين الصفحات.</p>
        </div>

        <div className={styles.actionGrid}>
          <Link href="/admin/audio-review" className={styles.actionCard}>
            <span className={`${styles.actionIcon} ${styles.blue}`}><Headphones size={22} /></span>
            <span className={styles.actionBody}><strong>مراجعة التسجيلات</strong><small>افتح قائمة تسجيلات القراءة وراجع ما ينتظر القرار.</small></span>
            <ArrowLeft size={18} className={styles.actionArrow} />
          </Link>
          <Link href="/admin/students" className={styles.actionCard}>
            <span className={`${styles.actionIcon} ${styles.green}`}><BookOpenCheck size={22} /></span>
            <span className={styles.actionBody}><strong>{learningStudents} في المسار التعليمي</strong><small>تابع مستوى كل طالب وتقدمه والتقوية عند الحاجة.</small></span>
            <ArrowLeft size={18} className={styles.actionArrow} />
          </Link>
          <Link href="/admin/students" className={styles.actionCard}>
            <span className={`${styles.actionIcon} ${styles.yellow}`}><ShieldCheck size={22} /></span>
            <span className={styles.actionBody}><strong>{readyForPosttest} جاهزون للبعدي</strong><small>تحقق من اكتمال رحلة L3 قبل فتح الاختبار البعدي.</small></span>
            <ArrowLeft size={18} className={styles.actionArrow} />
          </Link>
          <Link href="/admin/reports" className={styles.actionCard}>
            <span className={`${styles.actionIcon} ${styles.slate}`}><BarChart3 size={22} /></span>
            <span className={styles.actionBody}><strong>عرض التقارير</strong><small>راجع الصورة العامة للمستويات والتقدم والنتائج الحالية.</small></span>
            <ArrowLeft size={18} className={styles.actionArrow} />
          </Link>
        </div>
      </section>

      <section className={styles.statsGrid} aria-label="ملخص المنصة">
        <div className={styles.statCard}><span className={`${styles.statIcon} ${styles.blue}`}><Users size={22} /></span><div><strong>{students.length}</strong><span>إجمالي الطلاب</span></div></div>
        <div className={styles.statCard}><span className={`${styles.statIcon} ${styles.green}`}><Activity size={22} /></span><div><strong>{activeStudents}</strong><span>حسابات نشطة</span></div></div>
        <div className={styles.statCard}><span className={`${styles.statIcon} ${styles.yellow}`}><BookOpenCheck size={22} /></span><div><strong>{learningStudents}</strong><span>يتعلمون الآن</span></div></div>
        <div className={styles.statCard}><span className={`${styles.statIcon} ${styles.slate}`}><ShieldCheck size={22} /></span><div><strong>{inactiveStudents}</strong><span>حسابات موقوفة</span></div></div>
      </section>

      <section className={styles.studentsPanel}>
        <div className={styles.panelHeading}>
          <div><h2>أحدث الطلاب</h2><p>آخر الحسابات المضافة مع مستوى الطالب وتقدمه الحالي.</p></div>
          <Link href="/admin/students" className={styles.textLink}>عرض جميع الطلاب <ArrowLeft size={16} /></Link>
        </div>

        {recentStudents.length === 0 ? (
          <div className={styles.emptyState}>
            <Image src="/characters/girl/welcome.png" alt="شخصية هِمّة" width={112} height={145} />
            <div><h3>لا يوجد طلاب حتى الآن</h3><p>أضف أول طالب ليبدأ مساره في هِمّة.</p></div>
            <Link href="/admin/students/new" className={styles.primaryAction}><Plus size={18} /> إضافة أول طالب</Link>
          </div>
        ) : (
          <div className={styles.tableWrap}>
            <table className="data-table">
              <thead><tr><th>الطالب</th><th>رمز الدخول</th><th>المستوى</th><th>تقدم الأنشطة</th><th>الحالة</th></tr></thead>
              <tbody>
                {recentStudents.map((student) => {
                  const progress = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);
                  return (
                    <tr key={student.id}>
                      <td><Link href={`/admin/students/${student.id}`} className={styles.studentLink}>{student.full_name}</Link></td>
                      <td><span className="badge badge-gray border border-border tracking-widest px-3 py-1 font-mono" dir="ltr">{student.access_code}</span></td>
                      <td>المستوى {student.current_level}</td>
                      <td><div className={styles.progressCell}><div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div><span>{student.core_completed_items}/{student.core_total_items}</span></div></td>
                      <td><span className={`badge ${student.status === "active" ? "badge-green" : "badge-gray"}`}>{student.status === "active" ? "نشط" : "موقوف"}</span></td>
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
