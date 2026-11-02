"use client";
import { useEffect, useState } from "react";
import { Download, FlaskConical } from "lucide-react";
type Report = { complete?: boolean; expected_runs?: number; methodology: string; limitations: string; summary: { model: string; missions: number; task_successes: number; model_attempts: number; unsafe_suggestions: number; accepted_policy_violations: number; errors: number; median_inference_ms: number | null }[]; runs: { case: string; model: string; task_success: boolean; unsafe_suggestions?: number; accepted_policy_violations?: number; model_errors?: number; error?: string }[] };
export default function MissionEvaluation() {
  const [report, setReport] = useState<Report | null>(null);
  const [message, setMessage] = useState("Loading recorded mission evaluation…");
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/gateway/evaluations/missions", { cache: "no-store", signal: controller.signal }).then(async r => { const data = await r.json(); if (!r.ok) throw new Error(data.message || "Evaluation unavailable."); setReport(data); }).catch(e => { if (e.name !== "AbortError") setMessage(e.message); });
    return () => controller.abort();
  }, []);
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = "agentgate-mission-evaluation.json"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section className="mission-evaluation"><div className="panel-title"><FlaskConical size={20} /><h2>Does the coordinated mission work?</h2>{report && <button className="text-button" onClick={download}><Download size={13} /> Raw evaluation</button>}</div>
    <p>Recorded actual model runs across different budgets, category scope and seller instructions. This evaluates the mission planner, including replanning, separately from the prompt-only benchmark below.</p>
    {!report ? <p>{message}</p> : <><div className="mission-eval-table"><table><thead><tr><th>Model</th><th>Exact tasks matched</th><th>Unsafe suggestions</th><th>Violations accepted</th><th>Errors</th><th>Median model time</th></tr></thead><tbody>{report.summary.map(r => <tr key={r.model}><th>{r.model}<small>{r.model_attempts} model attempts</small></th><td>{r.task_successes} / {r.missions}</td><td>{r.unsafe_suggestions}</td><td>{r.accepted_policy_violations}</td><td>{r.errors}</td><td>{r.median_inference_ms === null ? "—" : `${(r.median_inference_ms / 1000).toFixed(1)}s`}</td></tr>)}</tbody></table></div><p className="mission-eval-limits">{report.limitations}</p><details><summary>Inspect each mission outcome</summary><div className="mission-eval-table"><table><thead><tr><th>Case</th><th>Model</th><th>Exact task</th><th>Unsafe suggestions</th><th>Violations accepted</th></tr></thead><tbody>{report.runs.map(r => <tr key={`${r.model}-${r.case}`}><th>{r.case}</th><td>{r.model}</td><td>{r.error ? "Run error" : r.task_success ? "Matched" : "Missed"}</td><td>{r.unsafe_suggestions ?? "—"}</td><td>{r.accepted_policy_violations ?? "—"}</td></tr>)}</tbody></table></div></details></>}
  </section>;
}
