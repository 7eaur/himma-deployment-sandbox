import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function proxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const upstream_path = path.join("/");
  const search = req.nextUrl.search;
  const url = `${API_URL}/${upstream_path}${search}`;

  const cookieHeader = req.headers.get("cookie") ?? "";
  const contentType = req.headers.get("content-type") ?? "";
  const idempotencyKey = req.headers.get("idempotency-key");

  const headers: Record<string, string> = {
    "content-type": contentType,
    cookie: cookieHeader,
  };
  if (idempotencyKey) {
    headers["idempotency-key"] = idempotencyKey;
  }

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = await req.blob();
  }

  const upstream = await fetch(url, init);
  const body = await upstream.arrayBuffer();

  const res = new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" },
  });

  // Forward Set-Cookie (critical for auth)
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) {
    res.headers.set("set-cookie", setCookie);
  }

  return res;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
