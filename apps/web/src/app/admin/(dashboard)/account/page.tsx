"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "../admin.module.css";


type ResearcherProfile = { id: number; username: string; full_name: string };

export default function AccountPage() {
  const [profile, setProfile] = useState<ResearcherProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/me`, { credentials: "include" });
        if (!res.ok) throw new Error("تعذر تحميل بيانات الحساب");
        setProfile(await res.json());
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "تعذر تحميل بيانات الحساب");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleLogout = async () => {
    try {
      await fetch(`/api/auth/logout`, { method: "POST", credentials: "include" });
      router.push("/admin/login");
    } catch {
      router.push("/admin/login");
    }
  };

  if (loading) return <div>جاري التحميل...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div style={{ maxWidth: "600px" }}>
      <h1 style={{ marginBottom: "2rem" }}>إعدادات الحساب</h1>
      
      {profile && (
        <div className={styles.statCard} style={{ textAlign: "right" }}>
          <div style={{ marginBottom: "1.5rem" }}>
            <label className="form-label" style={{ display: "block", color: "var(--dark)", opacity: 0.7 }}>الاسم الكامل</label>
            <p style={{ fontSize: "1.2rem", fontWeight: 600 }}>{profile.full_name}</p>
          </div>
          
          <div style={{ marginBottom: "2rem" }}>
            <label className="form-label" style={{ display: "block", color: "var(--dark)", opacity: 0.7 }}>اسم المستخدم</label>
            <p style={{ fontSize: "1.2rem", fontWeight: 600 }}>{profile.username}</p>
          </div>
          
          <button 
            className="btn btn-primary" 
            style={{ backgroundColor: "var(--error)", width: "100%" }}
            onClick={handleLogout}
          >
            تسجيل الخروج
          </button>
        </div>
      )}
    </div>
  );
}
