"use client";

import { useCallback, useEffect, useState } from "react";

import Login from "./components/Login";
import Mission, { type MissionRun } from "./components/Mission";
import MissionEvaluation from "./components/MissionEvaluation";
import PaymentEvidence from "./components/PaymentEvidence";

import BudgetForm from "./components/BudgetForm";

import Benchmark, { type BenchmarkRun } from "./components/Benchmark";

import { ArrowUpRight, Check, CheckCheck, ChevronRight, CircleHelp, FlaskConical, Fingerprint, Headphones, LockKeyhole, Network, Play, RefreshCw, ShieldCheck, ShoppingBag, Terminal, Target, X } from "lucide-react";

type Item = { sku: string; name: string; quantity: number; price_cents: number; merchant: string; category: string };

type Proposal = { mandate_id: string; payment_message?: string | null; id: string; agent: string; items: Item[]; amount_cents: number; currency: string; cart_hash: string; state: string; reason: string; source: string; payment_mode: string; approval_url: string | null; order_id: string | null; receipt: { id: string } | null };

type Mandate = { id: string; label: string; budget_cents: number; spent_cents: number; reserved_cents: number; available_cents: number; max_transaction_cents: number; merchants: string[]; categories: string[]; agents: string[]; expires_at: number; approval_ttl?: number };

type Event = { seq: number; kind: string; message: string; at: string; agent?: string; proposal_id?: string; mode?: string };

type Snapshot = { mandates: Mandate[]; proposals: Proposal[]; events: Event[]; payment_mode: string; model: string; benchmarks: BenchmarkRun[]; missions: MissionRun[] };

type Lab = { passed: number; total: number; results: { name: string; expected: string; observed: string; passed: boolean; duration_ms: number }[] };

const money = (cents: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100);

const label = (value: string) => value.replaceAll("_", " ");

async function api<T>(path: string, body?: unknown): Promise<T> {

  const response = await fetch(`/api/gateway/${path}`, body === undefined ? { cache: "no-store" } : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

  const data = await response.json();

  if (!response.ok) throw new Error(data.message || data.detail?.[0]?.msg || "The gateway could not complete this request.");

  return data as T;

}

export default function Console() {

  const [demoAvailable, setDemoAvailable] = useState(false);
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  const [selectedBudget, setSelectedBudget] = useState("");

  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);

  const [view, setView] = useState("mission");

  const [prompt, setPrompt] = useState("Find a USB microphone for recording demos. Stay within the shared budget.");

  const [agent, setAgent] = useState("iris");

  const [busy, setBusy] = useState("");

  const [notice, setNotice] = useState("");

  const [error, setError] = useState("");

  const [lab, setLab] = useState<Lab | null>(null);

  const [expanded, setExpanded] = useState<string | null>(null);

  const refresh = useCallback(async () => { setSnapshot(await api<Snapshot>("state")); }, []);

  useEffect(() => { fetch("/api/auth/session", { cache: "no-store" }).then(r => r.json()).then(async session => { setDemoAvailable(!!session.demo_available); setSignedIn(session.authenticated); if (session.authenticated) await refresh(); }).catch(() => setSignedIn(false)); }, [refresh]);

  useEffect(() => { if (!signedIn) return; const timer = setInterval(() => { refresh().catch(() => undefined); }, 5000); return () => clearInterval(timer); }, [signedIn, refresh]);

  async function run(key: string, fn: () => Promise<void>) {

    setBusy(key); setError(""); setNotice("");

    try { await fn(); } catch (e) { setError(e instanceof Error ? e.message : "Request failed."); }

    finally { try { await refresh(); } catch { setError("Gateway unavailable. Start the backend and refresh."); } setBusy(""); }

  }

  const mandate = snapshot?.mandates.find(m => m.id === selectedBudget) || snapshot?.mandates.find(m => m.id === snapshot.missions?.find(r => r.proposals.length > 0 && r.proposals.every(p => p.state === "captured"))?.payload.mandate_id) || snapshot?.mandates.find(m => m.id === snapshot.missions?.[0]?.payload.mandate_id) || snapshot?.mandates.find(m => m.id === "mandate-studio") || snapshot?.mandates[0];
  const proposals = snapshot?.proposals.filter(p => p.mandate_id === mandate?.id) || [];

  const simulated = snapshot?.payment_mode !== "paypal";

  const disabled = !!busy || !snapshot;

  async function fixture(sku: string, pair = false) {

    await run("fixture", async () => {

      const items = [{ sku, quantity: 1 }];

      if (pair) await Promise.all([api("proposals", { agent: "iris", items, mandate_id: mandate?.id }), api("proposals", { agent: "nova", items, mandate_id: mandate?.id })]);

      else await api("proposals", { agent, items, mandate_id: mandate?.id });

      setNotice(pair ? "Two $80 carts submitted. Review each against the selected shared budget." : "Fixture submitted through the gateway. No model was used.");

    });

  }

  async function action(p: Pick<Proposal, "id" | "cart_hash">, verb: string) {

    await run(p.id, async () => {

      if (verb === "execute") {

        await api(`proposals/${p.id}/order`, { cart_hash: p.cart_hash });

        await api(`proposals/${p.id}/capture`, { cart_hash: p.cart_hash });

        setNotice("Simulated payment completed. No money moved.");

      } else {

        await api(`proposals/${p.id}/${verb}`, verb === "cancel" ? {} : { cart_hash: p.cart_hash });

        setNotice(verb === "verify" ? "PayPal independently confirmed the saved order, capture, amount and currency. No payment was initiated." : verb === "approve" ? "Exact cart approved. Funds reserved against the shared budget." : verb === "renew" ? "Owner approval renewed for the same exact cart." : verb === "reconcile" ? "Provider status checked without initiating a new charge." : verb === "capture" ? "Capture confirmed. The receipt is recorded below." : verb === "order" ? "Sandbox order created. Complete buyer approval using the checkout link." : "Proposal cancelled.");

      }

    });

  }

  if (signedIn === null) return <main className="login-page"><p>Checking owner session…</p></main>;

  if (!signedIn) return <Login demoAvailable={demoAvailable} onSignedIn={async () => { setSignedIn(true); await refresh(); }} />;

  return <div className="app-shell">

    <aside className="sidebar">

      <a className="brand" href="/" aria-label="AgentGate home"><span className="brand-mark"><ShieldCheck size={24} /></span><span>AgentGate<span className="brand-sub">Payment execution control</span></span></a>

      <div className="workspace"><span className="workspace-icon">S</span><div>Studio workspace<small>Developer sandbox</small></div></div>

      <nav aria-label="Main navigation">

        {[{ id: "mission", name: "Recording mission", icon: Target }, { id: "gateway", name: "Gateway", icon: Network }, { id: "evidence", name: "Payment evidence", icon: ShieldCheck }, { id: "lab", name: "Failure lab", icon: FlaskConical }, { id: "benchmark", name: "Live benchmark", icon: Terminal }, { id: "policy", name: "Budget policy", icon: LockKeyhole }].map(({ id, name, icon: Icon }) => <button key={id} onClick={() => setView(id)} className={view === id ? "nav-item active" : "nav-item"} aria-current={view === id ? "page" : undefined}><Icon size={18} />{name}{view === id && <ChevronRight size={16} />}</button>)}

      </nav>

      <div className="sidebar-note"><Fingerprint size={22} /><p>Every payment starts with an exact-cart approval.</p><small>Agents propose. You authorize.</small></div>

      <div className="sidebar-bottom"><span className="owner-avatar">AV</span><div>Workspace owner<small>Authenticated owner</small></div><button className="logout-button" onClick={async () => { await fetch("/api/auth/logout", { method: "POST" }); setSignedIn(false); setSnapshot(null); }}>Sign out</button></div>

    </aside>

    <main>

      <header className="topbar"><div className="breadcrumb">Studio workspace <ChevronRight size={14} /> <span>{view === "evidence" ? "Payment evidence" : view === "mission" ? "Recording mission" : view === "lab" ? "Failure lab" : view === "benchmark" ? "Live benchmark" : view === "policy" ? "Budget policy" : "Gateway"}</span></div><div className="topbar-actions"><span className="mode-tag"><span className={simulated ? "dot amber" : "dot"} />{simulated ? "Simulated payments" : "PayPal sandbox"}</span><button className="icon-button" onClick={() => run("refresh", async () => { await refresh(); })} disabled={disabled} title="Refresh gateway" aria-label="Refresh gateway"><RefreshCw size={16} className={busy === "refresh" ? "spin" : ""} /></button></div></header>

      <div className="content">

        <div className="page-heading"><div><div className="section-kicker"><ShieldCheck size={16} /> Owner-controlled execution</div><h1>{view === "evidence" ? "A payment should leave evidence." : view === "mission" ? "One mission. Two agents. A shared budget." : view === "lab" ? "Test the payment boundary." : view === "benchmark" ? "See what the model actually does." : view === "policy" ? "Set the rules before the request." : "Give agents a budget. Keep control."}</h1><p>{view === "evidence" ? "Inspect the exact cart, independently verify the provider receipt, and replay without another charge." : view === "mission" ? "Follow each recommendation, revision and approval as your agents assemble a useful recording setup." : view === "lab" ? "Reproduce failure cases against an isolated ledger. Your workspace budget stays untouched." : view === "benchmark" ? "Compare actual model suggestions with the policy gateway using saved, reproducible trial results." : view === "policy" ? "Choose budgets and purchase scopes. Existing approvals retain the policy you reviewed." : "Review what your agents want to buy, approve the exact cart, and follow every payment."}</p></div><span className="version">Submission build</span></div>

        {error && <div className="message error" role="alert"><CircleHelp size={18} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><X size={16} /></button></div>}

        {notice && <div className="message success" role="status"><Check size={18} /><span>{notice}</span><button onClick={() => setNotice("")} aria-label="Dismiss notification"><X size={16} /></button></div>}

        {!snapshot && <div className="loading-state"><Network size={28} /><h2>Connecting to the gateway</h2><p>Start the backend on port 8000, then refresh.</p><button className="primary" disabled={!!busy} onClick={() => run("refresh", refresh)}>Refresh connection</button></div>}

        {snapshot && mandate && <>

          {view !== "evidence" && <><div className="budget-selector"><label htmlFor="selected-budget">Active budget</label><select id="selected-budget" value={mandate.id} onChange={e => { setSelectedBudget(e.target.value); const m = snapshot.mandates.find(m => m.id === e.target.value); if (m && !m.agents.includes(agent)) setAgent(m.agents[0]); }}>{snapshot.mandates.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}</select></div><section className="budget-strip" aria-label="Shared budget"><div className="budget-intro"><div className="budget-symbol"><LockKeyhole size={22} /></div><div><strong>{mandate.label}</strong><span>{mandate.agents.map(a => a === "iris" ? "Iris" : "Nova").join(" and ")} <span className="small-dot">•</span> USD</span></div></div><div className="budget-numbers"><div><span>Budget</span><strong>{money(mandate.budget_cents)}</strong></div><div><span>Spent</span><strong>{money(mandate.spent_cents)}</strong></div><div><span>Reserved</span><strong>{money(mandate.reserved_cents)}</strong></div><div className="available"><span>Available</span><strong>{money(mandate.available_cents)}</strong></div></div><div className="budget-meter" aria-label={`${money(mandate.available_cents)} available`}><span className="spent-meter" style={{ width: `${mandate.spent_cents / mandate.budget_cents * 100}%` }} /><span className="held-meter" style={{ width: `${mandate.reserved_cents / mandate.budget_cents * 100}%` }} /></div></section></>}

          {view === "mission" && <Mission runs={snapshot.missions || []} budget={mandate} model={snapshot.model} disabled={disabled} simulated={simulated}
            onRecorded={simulated ? () => run("recorded", async () => { const result = await api<MissionRun>("demo/recorded-mission", {}); setSelectedBudget(result.payload.mandate_id); setNotice("Recorded AI loaded into a fresh simulated budget. No live inference was performed."); }) : undefined}
            onStart={body => run("mission", async () => { await api("missions", body); setNotice("Mission queued. Actual agent decisions will appear as planning progresses."); })}
            onFreshBudget={() => run("fresh-budget", async () => { const created = await api<Mandate>("mandates", { label: "Recording mission " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), budget_cents: 10000, max_transaction_cents: 10000, categories: ["audio", "lighting", "accessories"], agents: ["iris", "nova"], lifetime_hours: 24, approval_ttl: 1800 }); setSelectedBudget(created.id); setNotice("Fresh $100 policy budget created. No funds are reserved until you approve exact carts."); })}
            onApprove={(id, carts) => run("mission-approve", async () => { await api(`missions/${id}/approve`, { carts }); setNotice("Exact mission carts approved together. Their combined amount is now reserved."); })}
            onAction={action} />}
          {view === "evidence" && <PaymentEvidence receipts={snapshot.proposals.filter(p => p.state === "captured")} disabled={disabled} onVerify={p => action(p, "verify")} onReplay={p => run("receipt-replay", async () => { await api(`proposals/${p.id}/capture`, { cart_hash: p.cart_hash }); setNotice("Original receipt returned. No new capture was initiated."); })} />}
          {view === "gateway" && <>

            <div className="workspace-grid">

              <section className="planner"><div className="panel-title"><span className="title-icon"><Terminal size={19} /></span><h2>Ask an agent</h2><span className="quiet-tag">Local AI</span></div><p className="panel-description">The planner reads the catalogue and budget. It can suggest a cart; it cannot approve a payment.</p><form onSubmit={(e) => { e.preventDefault(); run("agent", async () => { const result = await api<{ reason: string; model: string; latency_ms: number }>("agent/run", { agent, prompt, mandate_id: mandate?.id }); setNotice(`${result.model}: ${result.reason} (${(result.latency_ms / 1000).toFixed(1)}s)`); }); }}><label htmlFor="agent">Agent</label><select id="agent" value={agent} onChange={(e) => setAgent(e.target.value)} disabled={disabled}>{mandate.agents.map(a => <option value={a} key={a}>{a === "iris" ? "Iris / recording assistant" : "Nova / equipment assistant"}</option>)}</select><label htmlFor="mission">Purchase request</label><textarea id="mission" value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={4} maxLength={3000} required disabled={disabled} /><div className="model-line"><span className="dot" />{snapshot.model} <span>via Ollama</span></div><button className="primary wide" disabled={disabled || prompt.trim().length < 3} type="submit">{busy === "agent" ? <><RefreshCw className="spin" size={16} /> Planning purchase…</> : <><Play size={16} /> Generate proposal</>}</button></form>

                <div className="fixtures"><div className="fixture-heading"><FlaskConical size={16} /><strong>Repeatable fixtures</strong><span>No model calls</span></div><p>Use these to inspect the gateway even when the local model is unavailable.</p><div className="fixture-buttons"><button disabled={disabled} onClick={() => fixture("mic-80")}><Headphones size={14} /> $80 microphone</button><button disabled={disabled} onClick={() => fixture("cable-20")}>$20 cable kit</button><button disabled={disabled} onClick={() => fixture("mic-80", true)}>Two agents, two $80 carts</button><button disabled={disabled} onClick={() => fixture("rig-140")}>Over-budget request</button><button disabled={disabled} onClick={() => fixture("watch-300")}>Disallowed product</button></div></div>

              </section>

              <section className="review-panel"><div className="panel-title"><span className="title-icon"><ShoppingBag size={19} /></span><h2>Proposal review</h2><span className="count-tag">{proposals.filter(p => p.state === "pending").length} pending</span></div>

                <div className="proposal-list">{proposals.length === 0 ? <div className="empty-proposals"><span className="empty-icon"><Fingerprint size={38} /></span><h3>Your approval is the gate.</h3><p>Ask an agent or submit a fixture. Every cart appears here before it can reserve funds.</p><div className="flow-hint"><span>Propose</span><ChevronRight size={14} /><span>Review</span><ChevronRight size={14} /><span>Pay</span></div></div> : proposals.map(p => <article key={p.id} className={`proposal ${p.state === "blocked" ? "proposal-blocked" : ""}`}><div className="proposal-top"><div className={`agent-avatar ${p.agent}`}>{p.agent[0].toUpperCase()}</div><div><strong>{p.agent === "iris" ? "Iris" : "Nova"}</strong><small>{p.source.startsWith("ollama:") ? "Local AI proposal" : p.source === "agent_api" ? "External agent proposal" : "Fixture proposal"}</small></div><span className={`state-tag state-${p.state}`}>{label(p.state)}</span></div><div className="cart-lines">{p.items.map(item => <div key={item.sku}><span>{item.name}<small>{item.quantity} × {money(item.price_cents)} · {item.merchant}</small></span><strong>{money(item.price_cents * item.quantity)}</strong></div>)}</div><p className="proposal-reason">{p.reason}</p>{p.payment_message && <p className="proposal-reason">{p.payment_message}</p>}<div className="proposal-actions">

                  {p.state === "pending" && <><button className="primary" disabled={disabled} onClick={() => action(p, "approve")}><Check size={15} /> Approve {money(p.amount_cents)}</button><button className="text-button" disabled={disabled} onClick={() => action(p, "cancel")}>Decline</button></>}

                  {p.state === "approved" && <><button className="primary" disabled={disabled} onClick={() => action(p, simulated ? "execute" : "order")}>{simulated ? "Execute simulated payment" : "Create sandbox checkout"}<ArrowUpRight size={15} /></button><button className="text-button" disabled={disabled} onClick={() => action(p, "cancel")}>Release reservation</button></>}

                  {(p.state === "order_ready" || p.state === "capture_uncertain") && <>{p.approval_url && <a className="checkout-link" href={p.approval_url}>Approve in PayPal sandbox <ArrowUpRight size={14} /></a>}<button className="primary" disabled={disabled} onClick={() => action(p, "capture")}>{p.state === "capture_uncertain" ? "Reconcile capture" : "Confirm capture"}</button></>}

                  {p.state === "expired" && <button className="secondary" disabled={disabled} onClick={() => action(p, "renew")}>Renew owner approval</button>}{p.state === "capture_uncertain" && <button className="secondary" disabled={disabled} onClick={() => action(p, "reconcile")}>Read provider status</button>}{p.state === "create_uncertain" && <button className="secondary" disabled={disabled} onClick={() => action(p, "order")}>Retry the same order</button>}

                  {p.state === "captured" && <><span className="receipt-summary"><CheckCheck size={16} />{simulated ? "Simulation complete" : "Sandbox capture complete"}</span><button className="text-button" disabled={disabled} onClick={() => action(p, "capture")}>Test replay</button></>}

                </div><button className="details-button" onClick={() => setExpanded(expanded === p.id ? null : p.id)} aria-expanded={expanded === p.id}><Fingerprint size={13} /> Approval details <ChevronRight size={12} /></button>{expanded === p.id && <div className="approval-details"><span>Cart fingerprint</span><code>{p.cart_hash}</code><span>Proposal</span><code>{p.id}</code>{p.receipt && <><span>Receipt</span><code>{p.receipt.id}</code></>}<span>Mode: {p.payment_mode === "simulated" ? "simulated / no money moved" : "PayPal sandbox"}</span></div>}</article>)}</div>

              </section>

            </div>

            <section className="trace-panel"><div className="panel-title"><span className="title-icon"><Network size={19} /></span><h2>Execution trace</h2><span className="quiet-tag">Persistent audit log</span><button className="text-button trace-refresh" disabled={disabled} onClick={() => run("refresh", refresh)}>Refresh</button></div><div className="trace-list">{snapshot.events.map(event => <div className="trace-event" key={event.seq}><span className={`trace-dot ${event.kind === "blocked" || event.kind === "uncertain" ? "red" : event.kind === "captured" || event.kind === "approved" ? "green" : ""}`} /><time>{new Date(event.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</time><span className="event-kind">{label(event.kind)}</span><p>{event.message}</p>{event.agent && <span className="event-agent">{event.agent}</span>}</div>)}</div></section>

          </>}

          {view === "lab" && <section className="lab-panel"><div className="lab-intro"><span className="lab-icon"><FlaskConical size={32} /></span><div><h2>Ten reproducible gateway scenarios</h2><p>These test deterministic controls using simulated payments. They do not measure live-model prompt-injection resistance.</p></div><button className="primary" disabled={disabled} onClick={() => run("lab", async () => { setLab(await api<Lab>("lab/run", {})); })}>{busy === "lab" ? <RefreshCw size={16} className="spin" /> : <Play size={16} />} Run suite</button></div>{lab ? <><div className="lab-score"><strong>{lab.passed}<span> / {lab.total}</span></strong><div>Scenarios passed<small>Isolated ledger · simulated provider · no model calls</small></div></div><div className="results-table" role="table" aria-label="Gateway scenario results"><div className="result-row result-header" role="row"><span>Scenario</span><span>Expected behaviour / observed result</span><span>Result</span></div>{lab.results.map(row => <div className="result-row" role="row" key={row.name}><strong>{row.name}</strong><span>{row.expected}<small>{row.observed}</small></span><span className={`state-tag ${row.passed ? "state-captured" : "state-blocked"}`}>{row.passed ? "Passed" : "Failed"}</span></div>)}</div></> : <div className="lab-empty"><ShieldCheck size={40} /><h3>Exercise the failure paths.</h3><p>Includes concurrent spending, expired approvals, cart changes, forbidden merchants, and repeated capture requests.</p></div>}</section>}

          {view === "benchmark" && <><MissionEvaluation /><Benchmark runs={snapshot.benchmarks || []} disabled={disabled} onStart={() => run("benchmark", async () => { await api("benchmarks", { repeats: 3 }); setNotice("A 60-trial live-model benchmark is queued. Results update automatically."); })} /></>}

          {view === "policy" && <section className="policy-panel"><div className="panel-title"><LockKeyhole size={20} /><h2>{mandate.label}</h2><span className="quiet-tag">Immutable approval scope</span></div><dl><div><dt>Budget ID</dt><dd><code>{mandate.id}</code></dd></div><div><dt>Total shared budget</dt><dd>{money(mandate.budget_cents)} USD</dd></div><div><dt>Maximum per purchase</dt><dd>{money(mandate.max_transaction_cents)}</dd></div><div><dt>Assigned agents</dt><dd>{mandate.agents.join(", ")}</dd></div><div><dt>Permitted merchant</dt><dd>{mandate.merchants.join(", ")}</dd></div><div><dt>Permitted categories</dt><dd>{mandate.categories.join(", ")}</dd></div><div><dt>Budget expires</dt><dd>{new Date(mandate.expires_at * 1000).toLocaleString()}</dd></div><div><dt>Approval lifetime</dt><dd>{(mandate.approval_ttl || 600) / 60} minutes, capped by budget expiry</dd></div><div><dt>Payment environment</dt><dd>{simulated ? "Simulation. No PayPal requests or money movement." : "PayPal sandbox. Buyer approval required."}</dd></div></dl><div className="policy-explanation"><ShieldCheck size={20} /><p>Owner approvals reserve funds immediately. Uncertain payment outcomes keep their reservation until reconciliation. Agents can read the catalogue and propose carts; their credentials cannot approve or execute payments.</p></div><BudgetForm disabled={disabled} onCreate={body => run("budget", async () => { const created = await api<Mandate>("mandates", body); setSelectedBudget(created.id); setAgent(created.agents[0]); setNotice("New budget created. Its policy applies to new proposals."); })} /></section>}

          <footer><span>AgentGate / authenticated owner workspace</span><span>{simulated ? "No real payments. No production security claim." : "Sandbox only. No real money."}</span>{simulated && <button className="text-button" disabled={disabled} onClick={() => run("reset", async () => { await api("demo/reset", {}); setNotice("Simulated workspace reset to a fresh $100 budget."); })}>Reset demo</button>}</footer>

        </>}

      </div>

    </main>

  </div>;

}

