import hashlib
import json
import time
from .gateway import GateError


def ingest_webhook(gateway, jobs, headers, body, webhook_id):
    if gateway.provider.mode != "paypal":
        raise GateError("WEBHOOK_DISABLED", "PayPal webhooks require sandbox mode.", 503)
    if len(body) > 262144:
        raise GateError("WEBHOOK_TOO_LARGE", "Webhook body exceeds the size limit.", 413)
    try:
        event = json.loads(body)
        eid, kind = event["id"], event["event_type"]
        if not isinstance(eid, str) or len(eid) > 255 or not isinstance(kind, str):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise GateError("INVALID_WEBHOOK", "Expected a PayPal event ID and event type.", 400)
    gateway.provider.verify_webhook(headers, body, webhook_id)
    digest = hashlib.sha256(json.dumps(event, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    resource = event.get("resource", {})
    if not isinstance(resource, dict):
        raise GateError("INVALID_WEBHOOK", "Expected a PayPal resource object.", 400)
    supplemental = resource.get("supplementary_data", {})
    related = supplemental.get("related_ids", {}) if isinstance(supplemental, dict) else {}
    order_id = related.get("order_id") if isinstance(related, dict) else None
    if kind == "CHECKOUT.ORDER.APPROVED":
        order_id = resource.get("id")
    if order_id is not None and not isinstance(order_id, str):
        raise GateError("INVALID_WEBHOOK", "Expected a PayPal order identifier.", 400)
    with gateway.tx() as db:
        existing = db.execute("SELECT data FROM webhook_events WHERE id=?", (eid,)).fetchone()
        if existing:
            if json.loads(existing[0])["digest"] != digest:
                raise GateError("WEBHOOK_ID_COLLISION", "An event ID was reused with different content.")
            return {"accepted": True, "duplicate": True}
        # Store only event metadata, never the raw payer/account payload.
        metadata = {"id": eid, "event_type": kind, "digest": digest, "order_id": order_id, "received_at": time.time()}
        db.execute("INSERT INTO webhook_events VALUES (?, ?)", (eid, json.dumps(metadata)))
        proposals = [json.loads(r[0]) for r in db.execute("SELECT data FROM proposals").fetchall()]
        target = next((p for p in proposals if order_id and p.get("order_id") == order_id and p["payment_mode"] == "paypal"), None)
        if target and kind.startswith("PAYMENT.CAPTURE."):
            jobs.enqueue("reconcile", {"proposal_id": target["id"], "webhook_event_id": eid}, db=db)
        gateway.event(db, "webhook_verified", "Verified PayPal event recorded; payment updates require authoritative reconciliation.", event_type=kind, webhook_event_id=eid, proposal_id=target["id"] if target else None)
    return {"accepted": True, "duplicate": False, "matched": target is not None}


def reconcile_job(gateway, jobs, job):
    p = gateway.reconcile(job["payload"]["proposal_id"])
    jobs.update(job, state="completed", result={"proposal_id": p["id"], "state": p["state"]})
