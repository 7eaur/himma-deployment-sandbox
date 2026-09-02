"use client";

import { Bell } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./AdminNotifications.module.css";

interface NotificationItem {
  id: number;
  type: string;
  title: string;
  message: string;
  href: string;
  is_read: boolean;
  created_at: string;
}

interface NotificationPayload {
  unread_count: number;
  items: NotificationItem[];
}

function relativeTime(value: string) {
  const stamp = Date.parse(value);
  if (!Number.isFinite(stamp)) return "";
  const minutes = Math.max(0, Math.floor((Date.now() - stamp) / 60000));
  if (minutes < 1) return "الآن";
  if (minutes < 60) return `منذ ${minutes} د`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `منذ ${hours} س`;
  const days = Math.floor(hours / 24);
  return `منذ ${days} ي`;
}

export default function AdminNotifications() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<NotificationPayload>({ unread_count: 0, items: [] });
  const [error, setError] = useState("");
  const mounted = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/researcher/notifications?limit=24", { cache: "no-store" });
      const payload = await response.json().catch(() => null);
      if (!response.ok || !payload) throw new Error(payload?.detail || "تعذر تحميل الإشعارات");
      if (mounted.current) {
        setData(payload as NotificationPayload);
        setError("");
      }
    } catch (caught: unknown) {
      if (mounted.current) setError(caught instanceof Error ? caught.message : "تعذر تحميل الإشعارات");
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void refresh();
    const timer = window.setInterval(() => void refresh(), 30000);
    return () => {
      mounted.current = false;
      window.clearInterval(timer);
    };
  }, [refresh]);

  const openItem = async (item: NotificationItem) => {
    if (!item.is_read) {
      await fetch(`/api/researcher/notifications/${item.id}/read`, { method: "POST" }).catch(() => null);
      setData((current) => ({
        unread_count: Math.max(0, current.unread_count - 1),
        items: current.items.map((value) => value.id === item.id ? { ...value, is_read: true } : value),
      }));
    }
    setOpen(false);
    router.push(item.href);
  };

  const markAll = async () => {
    await fetch("/api/researcher/notifications/read-all", { method: "POST" }).catch(() => null);
    setData((current) => ({ unread_count: 0, items: current.items.map((item) => ({ ...item, is_read: true })) }));
  };

  return (
    <div className={styles.root}>
      {open && <button className={styles.scrim} aria-label="إغلاق الإشعارات" onClick={() => setOpen(false)} />}
      <button className={styles.trigger} aria-label="الإشعارات" aria-expanded={open} onClick={() => { setOpen((value) => !value); void refresh(); }}>
        <Bell size={20} aria-hidden="true" />
        {data.unread_count > 0 && <span className={styles.badge}>{data.unread_count > 99 ? "99+" : data.unread_count}</span>}
      </button>
      {open && (
        <div className={styles.popover} role="dialog" aria-label="إشعارات المشرف">
          <div className={styles.header}>
            <strong>الإشعارات</strong>
            {data.unread_count > 0 && <button className={styles.markAll} onClick={() => void markAll()}>تحديد الكل كمقروء</button>}
          </div>
          {error && <div className={styles.error}>{error}</div>}
          <div className={styles.list}>
            {data.items.length === 0 ? <div className={styles.empty}>لا توجد إشعارات تحتاج انتباهك الآن.</div> : data.items.map((item) => (
              <button key={item.id} className={`${styles.item} ${item.is_read ? "" : styles.unread}`} onClick={() => void openItem(item)}>
                <span className={styles.itemTop}><span className={styles.itemTitle}>{item.title}</span>{!item.is_read && <span className={styles.dot} />}</span>
                <span className={styles.message}>{item.message}</span>
                <span className={styles.time}>{relativeTime(item.created_at)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
