import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import type { NextRequest } from "next/server";

export const SESSION_COOKIE = process.env.AGENTGATE_DEMO_MODE === "true" ? "agentgate_demo_owner" : "agentgate_owner";
export const SESSION_SECONDS = 8 * 60 * 60;

function key() {
  const token = process.env.AGENTGATE_OWNER_TOKEN;
  if (!token || token === "local-agentgate-owner-change-before-sharing") throw new Error("Configure a private owner access key before signing in.");
  if (["production", "demo"].includes(process.env.AGENTGATE_ENV || "") && token.length < 32) throw new Error("Deployment requires a private owner access key of at least 32 characters.");
  return token;
}

export function sameSecret(value: string) {
  return timingSafeEqual(createHash("sha256").update(value).digest(), createHash("sha256").update(key()).digest());
}

export function createSession() {
  const payload = Buffer.from(JSON.stringify({ role: "owner", expires: Date.now() + SESSION_SECONDS * 1000, nonce: randomBytes(16).toString("hex") })).toString("base64url");
  const signature = createHmac("sha256", key()).update("owner-session:" + payload).digest("base64url");
  return payload + "." + signature;
}

export async function authenticated() {
  const value = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!value || value.length > 2048) return false;
  try {
    const [payload, signature, extra] = value.split(".");
    if (extra || !payload || !signature) return false;
    const expected = createHmac("sha256", key()).update("owner-session:" + payload).digest();
    const supplied = Buffer.from(signature, "base64url");
    if (expected.length !== supplied.length || !timingSafeEqual(expected, supplied)) return false;
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    return claims.role === "owner" && Number.isFinite(claims.expires) && claims.expires > Date.now();
  } catch { return false; }
}

export function sameOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  const configured = process.env.AGENTGATE_CONSOLE_ORIGIN;
  const origins = configured ? [configured] : ["http://localhost:3000", "http://127.0.0.1:3000"];
  return !!origin && origins.includes(origin) && new URL(origin).host === request.headers.get("host");
}
