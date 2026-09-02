"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, ArrowLeft, BarChart3, BellRing, BookOpenCheck, Headphones, Plus, ShieldCheck, Users } from "lucide-react";
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
import styles from "./admin.module.css";

interface Supervisor { id: number; full_name?: string; username?: string; role: string; }
interface Student { id: number; full_name: string; grade_level: number; access_code: string; current_level: number; status: "active" | "inactive"; posttest_enabled: boolean; posttest_eligible: boolean; core_completed_items: number; core_total_items: number; created_at: string; }
interface NotificationSummary { unread_count: number; items: Array<{ id: number; type: string; title: string; message: string; href: string; is_read: boolean }>; }

export default function AdminDashboard() {
  const [supervisor, setSupervisor] = useState<Supervisor | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [notifications, setNotifications] = useState<NotificationSummary>({ unread_count: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      fetch("/api/me", { cache: "no-store" }),
      fetch("/api/researcher/students", { cache: "no-store" }),
      fetch("/api/researcher/notifications?limit=4", { cache: "no-store" }),
    ])
      .then(async ([meResponse, studentsResponse, notificationResponse]) => {
        if (!meResponse.ok || !studentsResponse.ok) throw new Error("تعذر تحميل لوحة المشرف");
        const meData: Supervisor = await meResponse.json();
        const studentsData: Student[] = await studentsResponse.json();
        const notificationData: NotificationSummary = notificationResponse.ok ? await notificationResponse.json() : { unread_count: 0, items: [] };
        if (cancelled) return;
        setSupervisor(meData);
        setStudents(studentsData);
        setNotifications(notificationData);
      })
      .catch((caught: unknown) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل لوحة المشرف"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const activeStudents = useMemo(() => students.filter((student) => student.status === "active").length, [students]);
  const learningStudents = useMemo(() => students.filter((student) => student.core_completed_items > 0 && student.core_completed_items < student.core_total_items).length, [students]);
  const readyForPosttest = useMemo(() => students.filter((student) => student.posttest_eligible || student.posttest_enabled).length, [students]);
  const recentStudents = useMemo(() => [...students].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)).slice(0, 6), [students]);
  const supervisorName = supervisor?.full_name || supervisor?.username || "المشرف";
  const unreadItems = notifications.items.filter((item) => !item.is_read).slice(0, 3);

  if (loading) return <div className={styles.loading} dir="rtl" data-testid="admin-dashboard-loading"><div className={styles.loadingHeader} /><div className={styles.loadingStats}><span /><span /><span /><span /></div><div className={styles.loadingPanel} /></div>;

  return (
    <AdminPage>
      <AdminPageHeader
        eyebrow="لوحة المشرف"
        icon={ShieldCheck}
        title={`مرحبًا، ${supervisorName}`}
        description="ابدأ بما يحتاج تدخلًا الآن، ثم تابع تقدم الطلاب والاختبارات والتقارير من مكان واحد."
        actions={<AdminAction href="/admin/students/new" tone="primary" icon={Plus}>إضافة طالب</AdminAction>}
      />

      {error && <div className="alert-error">{error}</div>}

      <AdminPanel
        title="ما الذي يحتاج انتباهك الآن؟"
        description="قائمة إجراءات حقيقية مبنية على حالات النظام الحالية، وليست تنبيهات شكلية."
        actions={notifications.unread_count > 0 ? <span className={styles.attentionBadge}><BellRing size={15} /> {notifications.unread_count} غير مقروء</span> : undefined}
      >
        <div className={styles.actionGrid}>
          {unreadItems.map((item) => <Link key={item.id} href={item.href} className={`${styles.actionCard} ${styles.priorityCard}`}><span className={`${styles.actionIcon} ${styles.blue}`}><BellRing size={22} /></span><span className={styles.actionBody}><strong>{item.title}</strong><small>{item.message}</small></span><ArrowLeft size={18} className={styles.actionArrow} /></Link>)}
          <Link href="/admin/audio-review" className={styles.actionCard}><span className={`${styles.actionIcon} ${styles.blue}`}><Headphones size={22} /></span><span className={styles.actionBody}><strong>مراجعة التسجيلات</strong><small>راجع تسجيلات القراءة التي وصلت وتحتاج قرارًا.</small></span><ArrowLeft size={18} className={styles.actionArrow} /></Link>
          <Link href="/admin/students" className={styles.actionCard}><span className={`${styles.actionIcon} ${styles.green}`}><BookOpenCheck size={22} /></span><span className={styles.actionBody}><strong>{learningStudents} في المسار التعليمي</strong><small>تابع التقدم والتقوية وحالة كل طالب.</small></span><ArrowLeft size={18} className={styles.actionArrow} /></Link>
          <Link href="/admin/students" className={styles.actionCard}><span className={`${styles.actionIcon} ${styles.yellow}`}><ShieldCheck size={22} /></span><span className={styles.actionBody}><strong>{readyForPosttest} جاهزون للبعدي</strong><small>تحقق من اكتمال رحلة المستوى الثالث قبل فتح الاختبار.</small></span><ArrowLeft size={18} className={styles.actionArrow} /></Link>
          <Link href="/admin/reports" className={styles.actionCard}><span className={`${styles.actionIcon} ${styles.slate}`}><BarChart3 size={22} /></span><span className={styles.actionBody}><strong>التقارير والنتائج</strong><small>راجع الصورة العامة والتحسن والبيانات البحثية.</small></span><ArrowLeft size={18} className={styles.actionArrow} /></Link>
        </div>
      </AdminPanel>

      <AdminStatGrid>
        <AdminStat icon={Users} value={students.length} label="إجمالي الطلاب" />
        <AdminStat icon={Activity} value={activeStudents} label="حسابات نشطة" />
        <AdminStat icon={BookOpenCheck} value={learningStudents} label="يتعلمون الآن" />
        <AdminStat icon={BellRing} value={notifications.unread_count} label="تحتاج انتباه المشرف" />
      </AdminStatGrid>

      <AdminPanel title="أحدث الطلاب" description="آخر الحسابات المضافة مع المستوى والتقدم الحالي." actions={<AdminAction href="/admin/students">عرض جميع الطلاب</AdminAction>}>
        {recentStudents.length === 0 ? (
          <AdminEmptyState title="لا يوجد طلاب حتى الآن" description="أضف أول طالب ليبدأ مساره في هِمّة." action={<AdminAction href="/admin/students/new" tone="primary" icon={Plus}>إضافة أول طالب</AdminAction>} />
        ) : (
          <AdminResponsiveTable
            table={<table className="data-table"><thead><tr><th>الطالب</th><th>رمز الدخول</th><th>المستوى</th><th>تقدم الأنشطة</th><th>الحالة</th></tr></thead><tbody>{recentStudents.map((student) => { const progress = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100); return <tr key={student.id}><td><Link href={`/admin/students/${student.id}`} className={styles.studentLink}>{student.full_name}</Link></td><td><span className="badge badge-gray border border-border tracking-widest px-3 py-1 font-mono" dir="ltr">{student.access_code}</span></td><td>المستوى {student.current_level}</td><td><div className={styles.progressCell}><div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div><span>{student.core_completed_items}/{student.core_total_items}</span></div></td><td><span className={`badge ${student.status === "active" ? "badge-green" : "badge-gray"}`}>{student.status === "active" ? "نشط" : "موقوف"}</span></td></tr>; })}</tbody></table>}
            cards={recentStudents.map((student) => { const progress = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100); return <AdminMobileCard key={student.id} title={<Link href={`/admin/students/${student.id}`}>{student.full_name}</Link>}><span><strong>المستوى:</strong> {student.current_level}</span><span><strong>التقدم:</strong> {student.core_completed_items}/{student.core_total_items} ({progress}%)</span><span><strong>رمز الدخول:</strong> <b dir="ltr">{student.access_code}</b></span><span><strong>الحالة:</strong> {student.status === "active" ? "نشط" : "موقوف"}</span><span><AdminAction href={`/admin/students/${student.id}`}>فتح الملف</AdminAction></span></AdminMobileCard>; })}
          />
        )}
      </AdminPanel>
    </AdminPage>
  );
}
