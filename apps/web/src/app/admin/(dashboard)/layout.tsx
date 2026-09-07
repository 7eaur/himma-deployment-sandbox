"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { BarChart3, ClipboardList, Eye, LayoutDashboard, LogOut, Menu, Mic, Settings, UserPlus, Users, X } from "lucide-react";
import ReinforcementReviewPanel from "@/components/ReinforcementReviewPanel";
import AdminNotifications from "@/components/admin/AdminNotifications";
import styles from "./dashboard-layout.module.css";

const navSections = [
  { label: "المتابعة", items: [{ href: "/admin", label: "نظرة عامة", icon: LayoutDashboard }, { href: "/admin/audio-review", label: "مراجعة التسجيلات", icon: Mic }] },
  { label: "الطلاب", items: [{ href: "/admin/students", label: "جميع الطلاب", icon: Users }, { href: "/admin/students/new", label: "إضافة طالب", icon: UserPlus }] },
  { label: "النتائج والتقارير", items: [{ href: "/admin/reports", label: "التقارير", icon: BarChart3 }, { href: "/admin/skill-reports", label: "ملخص المهارات", icon: ClipboardList }] },
  { label: "إدارة المنصة", items: [{ href: "/admin/content-preview", label: "معاينة رحلة الطالب", icon: Eye }, { href: "/admin/settings", label: "الإعدادات والمشرفون", icon: Settings }] },
] as const;

interface SidebarContentProps { pathname: string; supervisorName: string; onNavigate: () => void; onLogout: () => void; }
function SidebarContent({ pathname, supervisorName, onNavigate, onLogout }: SidebarContentProps) {
  const initial = supervisorName.trim().charAt(0) || "م";
  return <><div className={styles.brand}><div className={styles.brandRow}><Image src="/brand/logo-navy.svg" alt="هِمّة" width={112} height={38} priority /><AdminNotifications /></div><span className={styles.brandLabel}>مركز متابعة المشرف</span></div><nav className={styles.nav} aria-label="التنقل في لوحة المشرف">{navSections.map((section) => <div className={styles.navSection} key={section.label}><div className={styles.navSectionTitle}>{section.label}</div><div className={styles.navSectionItems}>{section.items.map((item) => { const isActive = pathname === item.href || (item.href !== "/admin" && pathname.startsWith(`${item.href}/`)); const Icon = item.icon; return <Link key={item.href} href={item.href} onClick={onNavigate} className={`sidebar-nav-item ${styles.navItem} ${isActive ? styles.navItemActive : ""}`} aria-current={isActive ? "page" : undefined}><Icon size={19} className={styles.navIcon} aria-hidden="true" /><span>{item.label}</span></Link>; })}</div></div>)}</nav><div className={styles.sidebarFooter}><div className={styles.user}><div className={styles.avatar} aria-hidden="true">{initial}</div><div className={styles.userMeta}><div className={styles.userName}>{supervisorName || "المشرف"}</div><div className={styles.userRole}>مشرف المنصة</div></div></div><button onClick={onLogout} className={styles.logout}><LogOut size={18} aria-hidden="true" /><span>تسجيل الخروج</span></button></div></>;
}

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname(); const router = useRouter(); const [mobileMenuOpen, setMobileMenuOpen] = useState(false); const [authState, setAuthState] = useState<"checking" | "ready">("checking"); const [supervisorName, setSupervisorName] = useState("");
  useEffect(() => { let alive = true; const verify = async () => { try { const response = await fetch("/api/auth/me", { cache: "no-store" }); const data = await response.json().catch(() => null); if (!response.ok || data?.role !== "researcher") { router.replace("/admin/login"); return; } if (alive) { setSupervisorName(data.display_name || "المشرف"); setAuthState("ready"); } } catch { router.replace("/admin/login"); } }; void verify(); return () => { alive = false; }; }, [router]);
  const handleLogout = async () => { try { await fetch("/api/auth/logout", { method: "POST" }); } finally { router.replace("/admin/login"); router.refresh(); } };
  if (authState !== "ready") return <div className={styles.guard} dir="rtl" data-testid="admin-auth-guard"><Image src="/brand/logo-navy.svg" alt="هِمّة" width={130} height={46} priority /><div className="spinner w-12 h-12 border-4" /><p>جاري التحقق من جلسة المشرف...</p></div>;
  const sidebarProps = { pathname, supervisorName, onNavigate: () => setMobileMenuOpen(false), onLogout: handleLogout };
  return <div className={styles.dashboardShell} dir="rtl"><aside className={styles.sidebarDesktop}><SidebarContent {...sidebarProps} /></aside>{mobileMenuOpen && <div className={styles.mobileOverlay}><button className={styles.mobileBackdrop} onClick={() => setMobileMenuOpen(false)} aria-label="إغلاق القائمة" /><div className={styles.mobilePanel} role="dialog" aria-modal="true" aria-label="قائمة لوحة المشرف"><button onClick={() => setMobileMenuOpen(false)} className={styles.mobileClose} aria-label="إغلاق القائمة"><X size={24} /></button><SidebarContent {...sidebarProps} /></div></div>}<main className={styles.content}><div className={styles.mobileBar}><button onClick={() => setMobileMenuOpen(true)} className={styles.menuButton} aria-label="فتح القائمة"><Menu size={23} /></button><Image src="/brand/logo-navy.svg" alt="هِمّة" width={92} height={30} /><span className={styles.mobileBarText}>الإدارة</span><AdminNotifications /></div><ReinforcementReviewPanel />{children}</main></div>;
}
