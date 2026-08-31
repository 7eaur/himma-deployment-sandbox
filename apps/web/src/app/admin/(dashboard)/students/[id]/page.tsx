"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Activity,
  ArrowRight,
  BookOpen,
  Calendar,
  Check,
  ClipboardList,
  Copy,
  Headphones,
  History,
  KeyRound,
  LockKeyhole,
  PencilLine,
  Play,
  Power,
  RefreshCw,
  Save,
  ShieldCheck,
  Star,
  User,
} from "lucide-react";
import styles from "./student-detail.module.css";

interface Student {
  id: number;
  full_name: string;
  grade_level: number;
  access_code: string;
  created_at: string;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible: boolean;
  core_completed_items: number;
  core_total_items: number;
  core_completed: boolean;
}

interface AdaptationDecision {
  decision_id: number;
  source: "automatic" | "manual";
  action: "promote" | "stay" | "support" | "demote" | "hold" | "override";
  mastery_score: number | null;
  previous_level: number;
  new_level: number;
  weakest_skill_id: number | null;
  recommended_item_id: number | null;
  valid_attempt_count: number;
  consecutive_low_count: number;
  explanation: Record<string, unknown>;
  manual_reason?: string | null;
  created_at: string;
}

interface RewardEvent {
  id: number;
  type: "stars" | "badge";
  stars: number | null;
  label: string;
  details: Record<string, unknown>;
  created_at: string;
}

type TabKey = "overview" | "journey" | "tests" | "recordings" | "adaptation" | "account" | "history";

const TABS: Array<{ key: TabKey; label: string; icon: typeof User }> = [
  { key: "overview", label: "نظرة عامة", icon: User },
  { key: "journey", label: "المسار والتقدم", icon: BookOpen },
  { key: "tests", label: "الاختبارات", icon: ClipboardList },
  { key: "recordings", label: "التسجيلات", icon: Headphones },
  { key: "adaptation", label: "التقوية والتكيف", icon: Activity },
  { key: "account", label: "الحساب", icon: KeyRound },
  { key: "history", label: "السجل", icon: History },
];

const ACTION_LABEL: Record<string, string> = {
  promote: "ترقية مستوى",
  stay: "استمرار في المستوى",
  support: "تقوية موجهة",
  demote: "خفض مستوى واحد",
  hold: "انتظار بيانات كافية",
  override: "تعديل يدوي",
};

const REASON_LABEL: Record<string, string> = {
  second_consecutive_low_mastery: "انخفاض الإتقان في قرارين متتاليين",
  low_mastery_support_first: "الإتقان منخفض؛ تبدأ التقوية قبل أي قرار آخر",
  top_level_mastery: "إتقان مرتفع في أعلى مستوى",
  promotion_waiting_for_skill_coverage: "الإتقان مرتفع لكن تغطية المهارات لم تكتمل",
  promotion_blocked_by_skill_floor: "توجد مهارة مطلوبة لم تصل إلى الحد المطلوب",
  mastery_and_skill_gates_passed: "اجتاز الإتقان وتغطية المهارات والبوابات المطلوبة",
  mastery_in_stability_band: "الأداء في نطاق الاستمرار الحالي",
  researcher_manual_override: "قرار يدوي موثق من المشرف",
};

function apiError(data: unknown, fallback: string) {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
  }
  return fallback;
}

export default function StudentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [student, setStudent] = useState<Student | null>(null);
  const [history, setHistory] = useState<AdaptationDecision[]>([]);
  const [rewards, setRewards] = useState<RewardEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [overrideLevel, setOverrideLevel] = useState("1");
  const [overrideReason, setOverrideReason] = useState("");
  const [editName, setEditName] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });

  useEffect(() => {
    let cancelled = false;
    if (!id) return;
    void Promise.all([
      fetch(`/api/researcher/students/${id}`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${id}/adaptation/history`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${id}/rewards`, { cache: "no-store" }),
    ])
      .then(async ([studentResponse, historyResponse, rewardsResponse]) => {
        if (!studentResponse.ok) {
          const body = await studentResponse.json().catch(() => null);
          throw new Error(apiError(body, studentResponse.status === 404 ? "لم يتم العثور على الطالب" : "تعذر تحميل بيانات الطالب"));
        }
        const studentData: Student = await studentResponse.json();
        if (cancelled) return;
        setStudent(studentData);
        setEditName(studentData.full_name);
        setOverrideLevel(String(studentData.current_level));
        setHistory(historyResponse.ok ? await historyResponse.json() : []);
        setRewards(rewardsResponse.ok ? await rewardsResponse.json() : []);
      })
      .catch((error: unknown) => {
        if (!cancelled) setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحميل بيانات الطالب" });
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  const latestDecision = useMemo(() => history.at(-1) ?? null, [history]);
  const totalStars = rewards.reduce((sum, reward) => sum + (reward.stars ?? 0), 0);
  const badges = rewards.filter((reward) => reward.type === "badge");

  const refreshAdaptiveEvidence = async () => {
    if (!student) return;
    const [historyResponse, rewardsResponse] = await Promise.all([
      fetch(`/api/researcher/students/${student.id}/adaptation/history`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${student.id}/rewards`, { cache: "no-store" }),
    ]);
    if (historyResponse.ok) setHistory(await historyResponse.json());
    if (rewardsResponse.ok) setRewards(await rewardsResponse.json());
  };

  const saveStudentName = async () => {
    if (!student || editName.trim() === student.full_name) return;
    setBusy("name"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ full_name: editName }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر حفظ اسم الطالب"));
      setStudent(data); setEditName(data.full_name); setMessage({ kind: "success", text: "تم تحديث اسم الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ اسم الطالب" }); }
    finally { setBusy(""); }
  };

  const toggleStudentStatus = async () => {
    if (!student) return;
    setBusy("status"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: student.status !== "active" }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث حالة الطالب"));
      setStudent(data); setMessage({ kind: "success", text: data.status === "active" ? "تم تفعيل حساب الطالب." : "تم إيقاف حساب الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث حالة الطالب" }); }
    finally { setBusy(""); }
  };

  const changeAccessCode = async (manual: boolean) => {
    if (!student) return;
    if (manual && !/^\d{6}$/.test(manualCode)) { setMessage({ kind: "error", text: "الرمز اليدوي يجب أن يتكون من 6 أرقام." }); return; }
    setBusy("code"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/access-code`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ access_code: manual ? manualCode : null }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث رمز الدخول"));
      setStudent(data); setManualCode(""); setMessage({ kind: "success", text: "تم تحديث رمز دخول الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث رمز الدخول" }); }
    finally { setBusy(""); }
  };

  const copyAccessCode = async () => {
    if (!student) return;
    await navigator.clipboard.writeText(student.access_code); setCopied(true); window.setTimeout(() => setCopied(false), 1500);
  };

  const updatePosttestAccess = async () => {
    if (!student) return;
    setBusy("posttest"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/posttest-access`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled: !student.posttest_enabled }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث إتاحة الاختبار البعدي"));
      setStudent(data); setMessage({ kind: "success", text: data.posttest_enabled ? "تم فتح الاختبار البعدي للطالب." : "تم إيقاف الاختبار البعدي للطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث إتاحة الاختبار البعدي" }); }
    finally { setBusy(""); }
  };

  const saveManualOverride = async () => {
    if (!student) return;
    setBusy("override"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/adaptation/manual-override`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ new_level: Number(overrideLevel), reason: overrideReason.trim() }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر حفظ التعديل اليدوي"));
      const refreshed = await fetch(`/api/researcher/students/${student.id}`, { cache: "no-store" });
      if (refreshed.ok) { const updated: Student = await refreshed.json(); setStudent(updated); setEditName(updated.full_name); }
      setOverrideReason(""); await refreshAdaptiveEvidence(); setMessage({ kind: "success", text: "تم حفظ قرار المشرف مع سببه في السجل." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ التعديل اليدوي" }); }
    finally { setBusy(""); }
  };

  if (loading) return <div className={styles.loading}><span /><span /><span /></div>;
  if (!student) return <div className={styles.page}><div className="alert-error">{message.text || "لم يتم العثور على الطالب"}</div><Link href="/admin/students" className="btn-primary mt-4">العودة إلى الطلاب</Link></div>;

  const progressPercent = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);
  const reasonKey = typeof latestDecision?.explanation?.reason === "string" ? latestDecision.explanation.reason : "";

  const tabContent = (() => {
    if (activeTab === "overview") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>ملخص الطالب</h2><p>أهم المعلومات التي يحتاجها المشرف بسرعة.</p></div><User size={20} /></div>
        <div className={styles.grid3}>
          <div className={styles.infoCard}><span>الصف</span><strong>الثالث الابتدائي</strong></div>
          <div className={styles.infoCard}><span>المستوى الحالي</span><strong>المستوى {student.current_level}</strong></div>
          <div className={styles.infoCard}><span>تاريخ الإضافة</span><strong>{new Date(student.created_at).toLocaleDateString("ar-SA")}</strong></div>
        </div>
        <div className={styles.rewardRow} style={{ marginTop: 14 }}>
          <div className={styles.reward}><span className={styles.muted}>النجوم المكتسبة</span><strong>{totalStars}</strong></div>
          <div className={styles.reward}><span className={styles.muted}>الشارات</span><strong>{badges.length}</strong></div>
          <div className={styles.reward}><span className={styles.muted}>تقدم المستوى</span><strong>{progressPercent}%</strong></div>
        </div>
        {badges.length > 0 && <div className={styles.rewardRow} style={{ marginTop: 12 }}>{badges.map((badge) => <span key={badge.id} className={`${styles.badge} ${styles.good}`}>{badge.label}</span>)}</div>}
      </section>
    );

    if (activeTab === "journey") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>المسار والتقدم</h2><p>المستوى الحالي وما أنجزه الطالب داخله.</p></div><BookOpen size={20} /></div>
        <div className={styles.progressBlock}>
          <div className={styles.progressMeta}><span>الأنشطة الأساسية المكتملة</span><strong>{student.core_completed_items} من {student.core_total_items}</strong></div>
          <div className={styles.track} aria-label={`تقدم الأنشطة ${progressPercent}%`}><div className={styles.fill} style={{ width: `${progressPercent}%` }} /></div>
        </div>
        <div className={styles.journey}>
          {[1,2,3].map((level) => {
            const completed = level < student.current_level;
            const current = level === student.current_level;
            const cls = completed ? styles.levelDone : current ? styles.levelCurrent : styles.levelLocked;
            return <div key={level} className={`${styles.level} ${cls}`}><small>المستوى {level}</small><strong>{completed ? "مكتمل" : current ? "المستوى الحالي" : "لاحقًا"}</strong></div>;
          })}
        </div>
        <p className={styles.muted} style={{ marginTop: 14 }}>المسار بعد تحديد نقطة البداية في الاختبار القبلي يتقدم للأعلى حتى المستوى الثالث. لا يفتح الاختبار البعدي قبل اكتمال المستوى الثالث.</p>
      </section>
    );

    if (activeTab === "tests") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>الاختبارات</h2><p>إتاحة الاختبار البعدي وحالة الجاهزية.</p></div><ClipboardList size={20} /></div>
        <div className={styles.grid2}>
          <div className={styles.infoCard}><span>الاختبار القبلي</span><strong>جزء من مسار الطالب وتحديد نقطة البداية</strong></div>
          <div className={styles.infoCard}><span>الاختبار البعدي</span><strong>{student.posttest_enabled ? "مفتوح الآن" : student.posttest_eligible ? "جاهز للفتح" : "غير جاهز بعد"}</strong></div>
        </div>
        <div className={styles.notice} style={{ marginTop: 14 }}>{student.posttest_enabled ? "الاختبار البعدي متاح للطالب الآن." : student.posttest_eligible ? "اكتمل المستوى الثالث ويمكن للمشرف فتح الاختبار البعدي." : "لا يمكن فتح الاختبار البعدي قبل إكمال رحلة التعلم حتى المستوى الثالث."}</div>
        <div className={styles.actions} style={{ marginTop: 14 }}><button className={styles.primary} onClick={() => void updatePosttestAccess()} disabled={busy === "posttest" || (!student.posttest_eligible && !student.posttest_enabled)}><Play size={17} />{busy === "posttest" ? "جاري الحفظ..." : student.posttest_enabled ? "إيقاف الإتاحة" : "فتح الاختبار البعدي"}</button></div>
      </section>
    );

    if (activeTab === "recordings") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>التسجيلات الصوتية</h2><p>الوصول إلى مراجعة قراءات الطالب.</p></div><Headphones size={20} /></div>
        <div className={styles.linkCard}><div><strong>مراجعة التسجيلات المنتظرة</strong><p>قائمة المراجعة تعرض اسم الطالب والنص المتوقع ونوع الجلسة عند توفر تسجيل ينتظر القرار.</p></div><Link href="/admin/audio-review" className={styles.primary}><Headphones size={17} /> فتح مراجعة الصوت</Link></div>
        <p className={styles.muted} style={{ marginTop: 12 }}>لا تعرض هذه الصفحة رقمًا غير موثق للتسجيلات؛ بيانات المراجعة تؤخذ من قائمة التسجيلات الفعلية.</p>
      </section>
    );

    if (activeTab === "adaptation") return (
      <section className={styles.panel} data-testid="adaptation-panel">
        <div className={styles.panelHeader}><div><h2>التقوية والتكيف</h2><p>آخر قرار محفوظ والتدخل اليدوي عند الحاجة.</p></div><Activity size={20} /></div>
        {!latestDecision ? <p className={styles.muted}>لا يوجد قرار تكيف محفوظ بعد.</p> : (
          <div className={styles.grid3}>
            <div className={styles.infoCard}><span>آخر قرار</span><strong>{ACTION_LABEL[latestDecision.action] || latestDecision.action}</strong></div>
            <div className={styles.infoCard}><span>الإتقان المتحرك</span><strong>{latestDecision.mastery_score == null ? "—" : `${latestDecision.mastery_score.toFixed(1)}%`}</strong></div>
            <div className={styles.infoCard}><span>المستوى</span><strong>{latestDecision.previous_level} ← {latestDecision.new_level}</strong></div>
          </div>
        )}
        {latestDecision && <p className={styles.muted} style={{ marginTop: 12 }}>{REASON_LABEL[reasonKey] || reasonKey || "سبب القرار محفوظ ضمن السجل."}</p>}
        <div className={styles.notice} style={{ marginTop: 14 }}>التعديل اليدوي لا يحذف القرار الآلي؛ يُحفظ كحدث مستقل مع السبب والتاريخ.</div>
        <div className={styles.grid2} style={{ marginTop: 14 }}>
          <div className={styles.field}><label htmlFor="override-level">المستوى</label><select id="override-level" className={styles.select} value={overrideLevel} onChange={(event) => setOverrideLevel(event.target.value)}><option value="1">المستوى 1</option><option value="2">المستوى 2</option><option value="3">المستوى 3</option></select></div>
          <div className={styles.field}><label htmlFor="override-reason">سبب التعديل</label><input id="override-reason" className={styles.input} value={overrideReason} onChange={(event) => setOverrideReason(event.target.value)} placeholder="اكتب سبب القرار" maxLength={1000} /></div>
        </div>
        <div className={styles.actions} style={{ marginTop: 12 }}><button className={styles.primary} onClick={() => void saveManualOverride()} disabled={busy === "override" || overrideReason.trim().length < 5}><ShieldCheck size={17} />{busy === "override" ? "جاري الحفظ..." : "حفظ القرار اليدوي"}</button></div>
      </section>
    );

    if (activeTab === "account") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>الحساب والدخول</h2><p>اسم الطالب ورمز الدخول وحالة الحساب.</p></div><LockKeyhole size={20} /></div>
        <div className={styles.formGrid}>
          <div className={styles.field}><label htmlFor="student-name">اسم الطالب</label><input id="student-name" className={styles.input} value={editName} onChange={(event) => setEditName(event.target.value)} minLength={2} maxLength={80} /></div>
          <button className={styles.primary} onClick={() => void saveStudentName()} disabled={busy === "name" || editName.trim() === student.full_name}><Save size={17} />{busy === "name" ? "جاري الحفظ..." : "حفظ الاسم"}</button>
        </div>
        <div className={styles.codeBox} style={{ marginTop: 16 }}><div><span className={styles.muted}>رمز الدخول الحالي</span><strong className={styles.code}>{student.access_code}</strong></div><button className={styles.secondary} onClick={() => void copyAccessCode()}>{copied ? <Check size={17} /> : <Copy size={17} />}{copied ? "تم النسخ" : "نسخ الرمز"}</button></div>
        <div className={styles.grid2}>
          <button className={styles.secondary} onClick={() => void changeAccessCode(false)} disabled={busy === "code"}><RefreshCw size={17} /> توليد رمز جديد</button>
          <div className={styles.formGrid}><div className={styles.field}><label htmlFor="manual-code">رمز يدوي من 6 أرقام</label><input id="manual-code" className={styles.input} inputMode="numeric" maxLength={6} value={manualCode} onChange={(event) => setManualCode(event.target.value.replace(/\D/g, "").slice(0,6))} placeholder="123456" dir="ltr" /></div><button className={styles.primary} onClick={() => void changeAccessCode(true)} disabled={busy === "code" || manualCode.length !== 6}>حفظ</button></div>
        </div>
      </section>
    );

    return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>السجل</h2><p>قرارات التكيف والتعديلات المحفوظة زمنيًا.</p></div><History size={20} /></div>
        {history.length === 0 ? <p className={styles.muted}>لا يوجد سجل قرارات حتى الآن.</p> : <div className={styles.history}>{[...history].reverse().map((decision) => <div key={decision.decision_id} className={styles.historyItem}><div><strong>{ACTION_LABEL[decision.action] || decision.action}</strong><p className={styles.muted}>{decision.source === "manual" ? "قرار يدوي" : "قرار آلي"}{decision.manual_reason ? ` · ${decision.manual_reason}` : ""}</p></div><small>{new Date(decision.created_at).toLocaleString("ar-SA")}</small></div>)}</div>}
      </section>
    );
  })();

  return (
    <div className={styles.page} dir="rtl">
      <header className={styles.header}>
        <div className={styles.identity}>
          <Link href="/admin/students" className={styles.back} aria-label="العودة إلى الطلاب"><ArrowRight size={22} /></Link>
          <div className={styles.avatar}><User size={25} /></div>
          <div className={styles.identityText}><small>ملف الطالب</small><h1>{student.full_name}</h1><p>الصف الثالث الابتدائي · المعرف #{student.id}</p></div>
        </div>
        <button className={`${styles.statusButton} ${student.status === "active" ? styles.statusButtonActive : styles.statusButtonInactive}`} onClick={() => void toggleStudentStatus()} disabled={busy === "status"}><Power size={17} />{busy === "status" ? "جاري الحفظ..." : student.status === "active" ? "إيقاف الحساب" : "تفعيل الحساب"}</button>
      </header>

      {message.text && <div className={styles.message}><div className={message.kind === "success" ? "alert-success" : "alert-error"}>{message.text}</div></div>}

      <section className={styles.summary} aria-label="ملخص الطالب">
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><User size={20} /></span><div><strong>{student.status === "active" ? "حساب نشط" : "حساب موقوف"}</strong><span>حالة الطالب</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><BookOpen size={20} /></span><div><strong>المستوى {student.current_level}</strong><span>المستوى الحالي</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><Star size={20} /></span><div><strong>{totalStars}</strong><span>النجوم</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><KeyRound size={20} /></span><div><strong className={styles.code}>{student.access_code}</strong><span>رمز الدخول</span></div></div>
      </section>

      <nav className={styles.tabs} aria-label="أقسام ملف الطالب">
        {TABS.map((tab) => { const Icon = tab.icon; return <button key={tab.key} className={`${styles.tab} ${activeTab === tab.key ? styles.tabActive : ""}`} onClick={() => setActiveTab(tab.key)} aria-current={activeTab === tab.key ? "page" : undefined}><Icon size={16} />{tab.label}</button>; })}
      </nav>

      {tabContent}
    </div>
  );
}
