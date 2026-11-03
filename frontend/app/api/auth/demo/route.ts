import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { createSession, sameOrigin, SESSION_COOKIE, SESSION_SECONDS } from "../../../../lib/auth";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request) || process.env.AGENTGATE_DEMO_MODE !== "true" || process.env.AGENTGATE_ENV === "production") return NextResponse.json({ message: "The isolated simulated demo is not enabled." }, { status: 403 });
  try {
    // Free hosting may need close to a minute to wake after idle. Keep the
    // first judge login alive through the cold start instead of failing early.
    const r = await fetch(`${process.env.AGENTGATE_API_URL}/health`, { cache: "no-store", signal: AbortSignal.timeout(75_000) });
    const health = await r.json();
    if (!r.ok || health.payment_mode !== "simulated") return NextResponse.json({ message: "Demo entry requires an isolated simulated backend." }, { status: 403 });
    (await cookies()).set(SESSION_COOKIE, createSession(), { httpOnly: true, sameSite: "lax", secure: request.nextUrl.protocol === "https:", path: "/", maxAge: SESSION_SECONDS });
    return NextResponse.json({ authenticated: true, simulated: true }, { headers: { "Cache-Control": "no-store" } });
  } catch { return NextResponse.json({ message: "The demo backend is not ready yet." }, { status: 503 }); }
}
