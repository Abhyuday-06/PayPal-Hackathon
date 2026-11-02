"""An independent, proposal-only agent process using AgentGate's public API."""
import argparse
import os
from pathlib import Path
import sys
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from agentgate.agent import generate_plan
from agentgate.gateway import GateError


def main():
    load_dotenv(Path(__file__).with_name(".env"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mandate", required=True, help="Owner-assigned budget ID")
    parser.add_argument("--request", required=True, help="Purchase task")
    args = parser.parse_args()
    token = os.getenv("AGENTGATE_AGENT_TOKEN")
    if not token:
        raise SystemExit("Configure a proposal-only AGENTGATE_AGENT_TOKEN in examples/.env.")
    try:
        with httpx.Client(base_url=os.getenv("AGENTGATE_API_URL", "http://127.0.0.1:8000"), headers={"X-Agent-Token": token}, timeout=20) as client:
            catalog = client.get("/agent/catalog")
            catalog.raise_for_status()
            data = catalog.json()
            budget = next((m for m in data["mandates"] if m["id"] == args.mandate), None)
            if not budget:
                raise SystemExit("This agent is not assigned to that budget.")
            plan = generate_plan(args.request, budget, data["catalog"], os.getenv("OLLAMA_URL", "http://localhost:11434"), os.getenv("OLLAMA_MODEL", "gemma2:2b"))
            if not plan["items"]:
                print("Agent declined: " + plan["reason"])
                return
            response = client.post("/agent/proposals", json={"mandate_id": args.mandate, "items": plan["items"], "reason": plan["reason"]})
            response.raise_for_status()
            p = response.json()
            print({"agent": data["agent"], "proposal_id": p["id"], "state": p["state"], "amount_cents": p["amount_cents"], "model": plan["model"], "payment_authority": "none"})
    except (httpx.HTTPError, GateError):
        raise SystemExit("Agent request failed. Check its private credentials, budget and model availability.") from None


if __name__ == "__main__":
    main()
