"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

function currentStudentDestination() {
  if (typeof window === "undefined") return "/student";
  return `${window.location.pathname}${window.location.search}`;
}

function goToStudentLogin() {
  if (typeof window === "undefined") return;
  const next = currentStudentDestination();
  const login = new URL("/student/login", window.location.origin);
  login.searchParams.set("next", next);
  window.location.replace(login.toString());
}

export default function StudentAuthBoundary({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/student/login";
  const [authorized, setAuthorized] = useState(isLoginPage);

  useEffect(() => {
    if (isLoginPage) {
      setAuthorized(true);
      return;
    }

    let cancelled = false;
    setAuthorized(false);

    const verify = async () => {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store" });
        const data = await response.json().catch(() => null);
        if (cancelled) return;

        if (response.ok && data?.role === "student") {
          setAuthorized(true);
          return;
        }

        goToStudentLogin();
      } catch {
        if (!cancelled) goToStudentLogin();
      }
    };

    void verify();
    return () => {
      cancelled = true;
    };
  }, [isLoginPage, pathname]);

  if (isLoginPage) return <>{children}</>;
  if (!authorized) return null;
  return <>{children}</>;
}
