"""Replay recorded AI evidence inside a strictly simulated judge workspace."""
import copy
import json
from pathlib import Path
from .gateway import GateError
from .jobs import Jobs


def recorded_mission(gateway):
    if gateway.provider.mode != "simulated":
        raise GateError("SIMULATION_REQUIRED", "Recorded mission replay is available only in a simulated workspace.", 403)
    report = json.loads((Path(__file__).resolve().parents[1] / "reports/mission-evaluation.json").read_text(encoding="utf-8"))
    original = next(r["result"] for r in report["runs"] if r["model"] == "qwen2.5:7b" and r["case"] == "standard-100")
    budget = gateway.create_mandate("Judge demo · recorded AI", 10000, 10000, ["audio", "lighting", "accessories"], ["iris", "nova"], approval_ttl=1800)
    jobs = Jobs(gateway)
    with gateway.tx() as db:
        job = jobs.enqueue("mission", {"objective": original["payload"]["objective"], "model": original["payload"]["model"], "mandate_id": budget["id"], "seller_text": "", "recorded": True}, db=db)
        job.update(state="preparing")
        db.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(job), job["id"]))
    ids = []
    for p in original["proposals"]:
        cart = gateway.propose(p["agent"], [{"sku": i["sku"], "quantity": i["quantity"]} for i in p["items"]], p["reason"], source="recorded:" + original["payload"]["model"], mandate_id=budget["id"], mission_id=job["id"])
        ids.append(cart["id"])
    return jobs.update(job, state="completed", recorded_at=original["created_at"], model=original["payload"]["model"], rows=copy.deepcopy(original["rows"]), budget_snapshot={**budget, "available_cents":10000}, summary=original["summary"], proposal_ids=ids, progress=2, total=2)
