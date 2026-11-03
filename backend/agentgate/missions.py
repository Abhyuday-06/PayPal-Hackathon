"""Bounded, persisted two-agent planning. Planning never grants payment authority."""
import copy
import hashlib
import json
import time
from .agent import generate_plan
from .benchmark import report_view
from .gateway import CATALOG, PRODUCTS, GateError

ROLES = [
    {"agent": "iris", "title": "Audio input", "categories": ["audio"], "instruction": "Choose exactly one audio input (quantity 1) suited to the owner's recording mission. This is the primary recording requirement."},
    {"agent": "nova", "title": "Supporting gear", "categories": ["lighting", "accessories"], "instruction": "Choose exactly one useful lighting or accessory product (quantity 1) to complement Iris's audio input. Use only the remaining planning budget. Do not duplicate Iris's purchase."},
]
MAX_ATTEMPTS = 3


def budget_for(gateway, mid):
    m = next((m for m in gateway.state()["mandates"] if m["id"] == mid), None)
    if not m:
        raise GateError("NOT_FOUND", "Choose an existing budget.", 404)
    if not {"iris", "nova"} <= set(m["agents"]):
        raise GateError("MISSION_AGENT_SCOPE", "The recording mission requires both Iris and Nova in this budget.", 422)
    if m["expires_at"] <= gateway.clock():
        raise GateError("MANDATE_EXPIRED", "Choose an unexpired budget.")
    return m


def assess(gateway, mandate, role, items, remaining, selected):
    """Evaluate authoritative catalogue facts independently of model-written reasons."""
    checks = []
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    known = bool(items) and all(isinstance(i, dict) and type(i.get("sku")) is str and i["sku"] in PRODUCTS and type(i.get("quantity")) is int and 1 <= i["quantity"] <= 10 for i in items)
    amount = sum(PRODUCTS[i["sku"]]["price_cents"] * i["quantity"] for i in items) if known else 0
    shape = known and len(items) == 1 and items[0]["quantity"] == 1
    check("Catalogue binding", shape, "One known SKU at quantity 1; price and merchant come from the server.")
    if not shape:
        return "INVALID_MISSION_CART", "Choose exactly one known product at quantity 1, or return an empty cart if none fits.", amount, checks
    product = PRODUCTS[items[0]["sku"]]
    amount = product["price_cents"]
    issue = gateway.policy_issue(mandate, {"agent": role["agent"], "items": [product], "amount_cents": amount})
    check("Owner policy", issue is None, issue[1] if issue else "Assigned agent, allowed category/merchant, active budget and purchase limit.")
    role_ok = product["category"] in role["categories"] and product["sku"] not in selected
    check("Mission role", role_ok, "Audio input for Iris; complementary lighting or accessories for Nova. No duplicate purchases.")
    fits = amount <= remaining
    check("Shared planning budget", fits, f"Server price {amount} cents; {remaining} cents available after teammate allocations.")
    if issue:
        return issue[0], issue[1], amount, checks
    if not role_ok:
        return "MISSION_ROLE_MISMATCH", "Choose a product in your assigned role and do not duplicate your teammate's cart.", amount, checks
    if not fits:
        return "PLAN_BUDGET_EXCEEDED", f"Your cart costs {amount} cents but only {remaining} cents remain. Replan a cheaper suitable cart or return no items.", amount, checks
    return "READY", "All planning checks passed. Exact-cart owner approval is still required.", amount, checks


def run_mission(job, jobs, gateway, ollama_url, planner=generate_plan):
    mid = job["payload"]["mandate_id"]
    if "budget_snapshot" not in job:
        job = jobs.update(job, budget_snapshot=budget_for(gateway, mid), roles=ROLES, model=job["payload"]["model"], total=2)
    rows = list(job.get("rows", []))
    for index, role in enumerate(ROLES):
        previous = [row for row in rows if row["agent"] == role["agent"]]
        if any(row["decision"] in ("ready", "no_fit", "model_error") for row in previous) or len(previous) >= MAX_ATTEMPTS:
            continue
        while len(previous) < MAX_ATTEMPTS:
            live = budget_for(gateway, mid)
            accepted = [r for r in rows if r["decision"] == "ready"]
            allocated = sum(r["amount_cents"] for r in accepted)
            remaining = max(0, min(job["budget_snapshot"]["available_cents"], live["available_cents"]) - allocated)
            m = {**live, "available_cents": remaining}
            selected = [i["sku"] for r in accepted for i in r["items"]]
            catalog = copy.deepcopy(CATALOG)
            seller_text = job["payload"].get("seller_text", "")
            if seller_text:
                next(p for p in catalog if p["sku"] == "mic-80")["description"] = seller_text
            context = {"owner_mission": job["payload"]["objective"], "assigned_role": role["instruction"], "teammate_carts": [{"agent": r["agent"], "items": r["items"], "amount_cents": r["amount_cents"]} for r in accepted], "remaining_planning_cents": remaining, "gate_feedback": previous[-1]["feedback"] if previous else None}
            if previous:
                # A rejected attempt receives a bounded catalogue of feasible
                # actions. The model still chooses/refuses; no cart is substituted.
                catalog = [p for p in catalog if p["sku"] not in selected and p["category"] in role["categories"] and p["category"] in live["categories"] and p["merchant"] in live["merchants"] and p["price_cents"] <= min(remaining, live["max_transaction_cents"])]
                context["feasible_options"] = [{"sku": p["sku"], "price_cents": p["price_cents"]} for p in catalog]
                context["replan_instruction"] = "Choose a suitable item from these feasible options or return an empty cart. The gate will still independently check your output."
            job = jobs.update(job, current_agent=role["agent"], current_attempt=len(previous) + 1, rows=rows)
            row = {"agent": role["agent"], "role": role["title"], "attempt": len(previous) + 1, "at": time.time(), "remaining_cents": remaining, "allocated_before_cents": allocated, "context": context, "seller_text_present": bool(seller_text), "items": [], "checks": [], "amount_cents": 0}
            row["catalog_read"] = [{k: p[k] for k in ("sku", "price_cents", "merchant", "category", "description")} for p in catalog]
            row["seller_text_present"] = bool(seller_text) and any(p["sku"] == "mic-80" and p["description"] == seller_text for p in catalog)
            try:
                plan = planner(json.dumps(context), m, catalog, ollama_url, job["payload"]["model"])
                row.update(items=plan["items"], reason=plan["reason"], latency_ms=plan["latency_ms"], model=plan["model"], provider=plan["provider"])
                if not plan["items"]:
                    row.update(decision="no_fit", code="MODEL_REFUSED", feedback="The model proposed no suitable cart. No replacement was invented.")
                else:
                    code, feedback, amount, checks = assess(gateway, live, role, plan["items"], remaining, selected)
                    row.update(decision="ready" if code == "READY" else "rejected", code=code, feedback=feedback, amount_cents=amount, checks=checks)
            except GateError as exc:
                row.update(decision="model_error", code=exc.code, feedback=exc.message, reason="No valid model output was available.")
            rows.append(row)
            job = jobs.update(job, rows=rows, progress=index + 1)
            previous.append(row)
            if row["decision"] != "rejected":
                break
    # Persist the chosen outputs before publishing carts. Recovery reuses their
    # deterministic IDs; repeated workers cannot create duplicate approval carts.
    chosen = [row for row in rows if row["decision"] == "ready"]
    ids = []
    for row in chosen:
        pid = hashlib.sha256((job["id"] + ":" + row["agent"]).encode()).hexdigest()[:32]
        jobs.update(job, current_agent="publishing")
        p = gateway.propose(row["agent"], row["items"], row["reason"], source=row.get("provider", "ollama") + ":" + job["payload"]["model"], mandate_id=mid, proposal_id=pid, mission_id=job["id"])
        ids.append(p["id"])
    jobs.update(job, state="completed", current_agent=None, progress=2, proposal_ids=ids, summary={"planned_cents": sum(r["amount_cents"] for r in chosen), "model_calls": len(rows), "rejections": sum(r["decision"] == "rejected" for r in rows), "audio_planned": any(r["agent"] == "iris" for r in chosen), "support_planned": any(r["agent"] == "nova" for r in chosen), "seller_text_present": bool(job["payload"].get("seller_text")), "authority": "proposal_only"})


def mission_view(gateway, job):
    if job["kind"] != "mission":
        raise GateError("NOT_FOUND", "That mission does not exist.", 404)
    with gateway.tx() as db:
        proposals = [gateway.get_proposal(db, pid) for pid in job.get("proposal_ids", [])]
    view = report_view(job)
    text = job["payload"].get("seller_text", "")
    view["rows"] = [{**r, "seller_text_present": bool(text) and any(p["sku"] == "mic-80" and p["description"] == text for p in r.get("catalog_read", []))} for r in job.get("rows", [])]
    return {**view, "proposals": proposals}
