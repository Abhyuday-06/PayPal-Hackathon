import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { createSession, sameOrigin, sameSecret, SESSION_COOKIE, SESSION_SECONDS } from "../../../../lib/auth";

// A bounded, single-owner login bucket. Distributed hosting needs a shared limiter.
let attempts: number[] = [];
export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ message: "Use the owner sign-in page." }, { status: 403 });
  const now = Date.now();
  attempts = attempts.filter(t => now - t < 60000);
  if (attempts.length >= 10) return NextResponse.json({ message: "Too many sign-in attempts. Retry in a minute." }, { status: 429 });
  attempts.push(now);
  try {
    const data = await request.json();
    if (typeof data.access_key !== "string" || data.access_key.length > 256 || !sameSecret(data.access_key)) return NextResponse.json({ message: "The owner access key is incorrect." }, { status: 401 });
    (await cookies()).set(SESSION_COOKIE, createSession(), { httpOnly: true, secure: process.env.AGENTGATE_ENV === "production" || request.nextUrl.protocol === "https:", sameSite: "lax", path: "/", maxAge: SESSION_SECONDS });
    return NextResponse.json({ authenticated: true }, { headers: { "Cache-Control": "no-store" } });
  } catch { return NextResponse.json({ message: "Check the owner access key configuration." }, { status: 400 }); }
}
