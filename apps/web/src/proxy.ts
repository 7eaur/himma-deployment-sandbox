import { NextRequest, NextResponse } from "next/server";

const STUDENT_LOGIN = "/student/login";
const ADMIN_LOGIN = "/admin/login";

function redirectToLogin(request: NextRequest, loginPath: string) {
  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = loginPath;
  loginUrl.search = "";
  loginUrl.searchParams.set("next", `${request.nextUrl.pathname}${request.nextUrl.search}`);
  return NextResponse.redirect(loginUrl);
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Login pages are always public. Everything else below /student and /admin
  // is protected before the page UI is allowed to render.
  if (pathname === STUDENT_LOGIN || pathname === ADMIN_LOGIN) {
    return NextResponse.next();
  }

  const isStudentRoute = pathname === "/student" || pathname.startsWith("/student/");
  const isAdminRoute = pathname === "/admin" || pathname.startsWith("/admin/");

  if (!isStudentRoute && !isAdminRoute) {
    return NextResponse.next();
  }

  if (!request.cookies.get("access_token")?.value) {
    return redirectToLogin(request, isStudentRoute ? STUDENT_LOGIN : ADMIN_LOGIN);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/student/:path*", "/admin/:path*"],
};
