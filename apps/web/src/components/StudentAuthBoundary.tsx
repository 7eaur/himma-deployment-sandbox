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
  const [verifiedPath, setVerifiedPath] = useState<string | null>(null);

  useEffect(() => {
    if (isLoginPage) return;

    let cancelled = false;

    const verify = async () => {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store" });
        const data = await response.json().catch(() => null);
        if (cancelled) return;

        if (response.ok && data?.role === "student") {
          setVerifiedPath(pathname);
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
  if (verifiedPath !== pathname) return null;
  return <>{children}</>;
}
