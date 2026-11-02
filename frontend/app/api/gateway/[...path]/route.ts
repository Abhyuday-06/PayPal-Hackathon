import { NextRequest, NextResponse } from "next/server";
import { authenticated, sameOrigin } from "../../../../lib/auth";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (!await authenticated()) return NextResponse.json({ message: "Sign in to the owner console." }, { status: 401 });
  const { path } = await context.params;
  const route = path.join("/");
  const allowed = /^(state|mandates|proposals|proposals\/[a-f0-9]{32}\/(approve|order|capture|cancel|renew|reconcile|verify)|agent\/run|lab\/run|demo\/reset|demo\/recorded-mission|benchmarks|benchmarks\/[a-f0-9]{32}|missions|missions\/[a-f0-9]{32}(\/approve)?|evaluations\/missions)$/;
  if (!allowed.test(route)) return NextResponse.json({ message: "Unknown gateway route." }, { status: 404 });
  if (request.method !== "GET") {
    if (!sameOrigin(request)) return NextResponse.json({ message: "Use the same-origin owner console." }, { status: 403 });
  }
  try {
    const result = await fetch(`${process.env.AGENTGATE_API_URL || "http://127.0.0.1:8000"}/api/${route}`, {
      method: request.method, cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Owner-Token": process.env.AGENTGATE_OWNER_TOKEN || "local-agentgate-owner-change-before-sharing" },
      ...(request.method === "POST" ? { body: await request.text() } : {}),
      signal: AbortSignal.timeout(route === "agent/run" ? 190000 : 65000),
    });
    return new NextResponse(await result.text(), { status: result.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ message: "Gateway unavailable. Start the FastAPI backend and retry." }, { status: 503 });
  }
}

export { proxy as GET, proxy as POST };
