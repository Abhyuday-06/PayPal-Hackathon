import { NextResponse } from "next/server";
import { authenticated } from "../../../../lib/auth";
export async function GET() {
  const hostedDemo = process.env.AGENTGATE_ENV === "demo";
  const aiProvider = process.env.AGENTGATE_AI_PROVIDER || (hostedDemo ? "recorded" : "ollama");
  const aiEnabled = process.env.AGENTGATE_AI_ENABLED === "true" || (!hostedDemo && aiProvider === "ollama");
  const defaultModel = aiProvider === "gemini" || aiProvider === "vertex" ? "gemini-3.8-flash" : aiProvider === "ollama" ? "qwen2.5:7b" : "recorded Qwen 2.5 7B";
  return NextResponse.json({ authenticated: await authenticated(), demo_available: process.env.AGENTGATE_DEMO_MODE === "true" && process.env.AGENTGATE_ENV !== "production", ai_enabled: aiEnabled, ai_provider: aiProvider, ai_model: process.env.AGENTGATE_AI_MODEL || defaultModel }, { headers: { "Cache-Control": "no-store" } });
}
