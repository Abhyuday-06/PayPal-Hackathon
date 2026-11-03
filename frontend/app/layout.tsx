import type { Metadata } from "next";
import "./globals.css";
import "./mission.css";
import "./readability.css";

export const metadata: Metadata = { title: "AgentGate | Payment control for AI agents", description: "Review exact-cart approvals, shared budgets, and payment execution traces." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
