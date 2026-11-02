import { NextResponse } from "next/server";
import { authenticated } from "../../../../lib/auth";
export async function GET() {
  return NextResponse.json({ authenticated: await authenticated(), demo_available: process.env.AGENTGATE_DEMO_MODE === "true" && process.env.AGENTGATE_ENV !== "production" }, { headers: { "Cache-Control": "no-store" } });
}
