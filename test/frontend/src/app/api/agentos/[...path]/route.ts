import { AGENTOS_URL } from "@/lib/config";
import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy AgentOS REST APIs to avoid CORS and keep the backend URL server-side.
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const targetPath = path.join("/");
  const url = new URL(`${AGENTOS_URL}/${targetPath}`);
  req.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value);
  });

  const res = await fetch(url.toString(), { method: "GET" });
  const body = await res.text();

  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
  });
}
