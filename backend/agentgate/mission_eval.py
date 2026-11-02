"""Evaluate actual mission runs in isolated simulation; no PayPal calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import tempfile
import time
from dotenv import load_dotenv
from .benchmark import canonical, reference_policy
from .gateway import Gateway
from .jobs import Jobs
from .missions import run_mission, mission_view
from .payments import SimulatedPayments

CASE_PATH = Path(__file__).resolve().parents[1] / "benchmarks/mission_cases.json"


def evaluate(models, output, ollama_url):
    cases = json.loads(CASE_PATH.read_text(encoding="utf-8"))
    report = {"evaluation": "mission-v1", "created_at": time.time(), "dataset_sha256": hashlib.sha256(CASE_PATH.read_bytes()).hexdigest(), "methodology": "Actual two-agent mission runs; independent policy oracle scores each recorded suggestion using that call's available planning funds. Fresh isolated simulated ledger per case. No PayPal calls. Exact expected carts score task success separately.", "limitations": "Six synthetic cases per model, one run each; small fixed catalogue, no statistical generalization or production security claim. This tests the coordinated mission planner including retry shortlists, not the original prompt-only benchmark.", "models": models, "runs": []}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    for model in models:
        for case in cases:
            with tempfile.TemporaryDirectory(prefix="agentgate-mission-eval-") as folder:
                g = Gateway(str(Path(folder) / "ledger.db"), SimulatedPayments())
                m = g.create_mandate(case["id"], case["budget_cents"], case["budget_cents"], case.get("categories", ["audio", "lighting", "accessories"]), ["iris", "nova"])
                jobs = Jobs(g)
                jobs.enqueue("mission", {"objective": case["objective"], "mandate_id": m["id"], "model": model, "seller_text": case.get("seller_text", "")})
                job = jobs.claim()
                start = time.perf_counter()
                try:
                    run_mission(job, jobs, g, ollama_url)
                    result = mission_view(g, jobs.get(job["id"]))
                    unsafe, accepted_unsafe = 0, 0
                    for row in result["rows"]:
                        independent_m = {**m, "available_cents": row["remaining_cents"]}
                        unsafe_cart = not reference_policy(row["items"], independent_m)
                        unsafe += unsafe_cart
                        accepted_unsafe += unsafe_cart and row["decision"] == "ready"
                    actual = [i for p in result["proposals"] for i in p["items"]]
                    error_count = sum(r["decision"] == "model_error" for r in result["rows"])
                    record = {"case": case["id"], "model": model, "duration_ms": round((time.perf_counter() - start) * 1000), "expected": case["expected"], "task_success": not error_count and canonical(actual) == canonical(case["expected"]), "unsafe_suggestions": unsafe, "accepted_policy_violations": accepted_unsafe, "model_errors": error_count, "result": result}
                except Exception as exc:
                    record = {"case": case["id"], "model": model, "task_success": False, "error": type(exc).__name__}
            report["runs"].append(record)
            report["expected_runs"] = len(models) * len(cases)
            report["complete"] = len(report["runs"]) == report["expected_runs"]
            report["summary"] = []
            for name in models:
                runs = [r for r in report["runs"] if r["model"] == name]
                latencies = [row["latency_ms"] for r in runs for row in r.get("result", {}).get("rows", []) if "latency_ms" in row]
                report["summary"].append({"model": name, "missions": len(runs), "task_successes": sum(r["task_success"] for r in runs), "model_attempts": sum(len(r.get("result", {}).get("rows", [])) for r in runs), "unsafe_suggestions": sum(r.get("unsafe_suggestions", 0) for r in runs), "accepted_policy_violations": sum(r.get("accepted_policy_violations", 0) for r in runs), "errors": sum(bool(r.get("error")) + r.get("model_errors", 0) for r in runs), "median_inference_ms": round(statistics.median(latencies)) if latencies else None})
            output.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps({k: record[k] for k in ("case", "model", "task_success")}), flush=True)
    return report


if __name__ == "__main__":
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["gemma2:2b", "qwen2.5:7b"])
    parser.add_argument("--output", default="reports/mission-evaluation.json")
    args = parser.parse_args()
    result = evaluate(args.models, args.output, os.getenv("OLLAMA_URL", "http://localhost:11434"))
    print(json.dumps(result["summary"]), flush=True)
