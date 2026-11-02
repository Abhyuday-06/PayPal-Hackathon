import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { sameOrigin, SESSION_COOKIE } from "../../../../lib/auth";
export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ message: "Use the owner console." }, { status: 403 });
  (await cookies()).delete(SESSION_COOKIE);
  return NextResponse.json({ authenticated: false });
}
