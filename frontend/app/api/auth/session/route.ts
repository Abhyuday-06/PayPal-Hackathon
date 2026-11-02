import { NextResponse } from "next/server";
import { authenticated } from "../../../../lib/auth";
export async function GET() {
  return NextResponse.json({ authenticated: await authenticated() }, { headers: { "Cache-Control": "no-store" } });
}
