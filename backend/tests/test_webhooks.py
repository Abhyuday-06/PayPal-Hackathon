import json
import pytest
from agentgate.gateway import Gateway, GateError
from agentgate.jobs import Jobs
from agentgate.payments import SimulatedPayments, PayPalSandbox
from agentgate.webhooks import ingest_webhook, reconcile_job


class VerifiedProvider(SimulatedPayments):
    mode = "paypal"
    def verify_webhook(self, headers, body, webhook_id):
        if headers.get("verified") != "yes":
            raise GateError("INVALID_WEBHOOK_SIGNATURE", "Rejected", 401)
        return True
    def reconcile(self, p):
        return super().capture(p)


@pytest.fixture
def service(tmp_path):
    g = Gateway(str(tmp_path / "hook.db"), VerifiedProvider())
    p = g.propose("iris", [{"sku": "cable-20", "quantity": 1}])
    g.approve(p["id"], p["cart_hash"])
    g.order(p["id"], p["cart_hash"])
    return g, Jobs(g), p


def body(p, eid="WH-ONE", value="999999.00"):
    return json.dumps({"id": eid, "event_type": "PAYMENT.CAPTURE.COMPLETED", "resource": {"amount": {"value": value}, "supplementary_data": {"related_ids": {"order_id": "SIM-" + p["id"][:16]}}}}).encode()


def test_duplicate_verified_event_enqueues_once(service):
    g, jobs, p = service
    assert ingest_webhook(g, jobs, {"verified": "yes"}, body(p), "hook")["duplicate"] is False
    assert ingest_webhook(g, jobs, {"verified": "yes"}, body(p), "hook")["duplicate"] is True
    assert len(jobs.list()) == 1
    # An event alone cannot mark a payment spent, even after verification.
    assert g.state()["mandates"][0]["spent_cents"] == 0
    job = jobs.claim()
    reconcile_job(g, jobs, job)
    assert g.state()["mandates"][0]["spent_cents"] == 2000
    assert jobs.get(job["id"])["state"] == "completed"


def test_unverified_event_cannot_mutate_ledger(service):
    g, jobs, p = service
    with pytest.raises(GateError):
        ingest_webhook(g, jobs, {}, body(p), "hook")
    assert jobs.list() == []
    assert g.state()["mandates"][0]["spent_cents"] == 0


def test_verified_malformed_resource_is_rejected_without_mutation(service):
    g, jobs, p = service
    raw = json.dumps({"id": "WH-BAD", "event_type": "PAYMENT.CAPTURE.COMPLETED", "resource": []}).encode()
    with pytest.raises(GateError) as exc:
        ingest_webhook(g, jobs, {"verified": "yes"}, raw, "hook")
    assert exc.value.code == "INVALID_WEBHOOK"
    assert jobs.list() == []


def test_duplicate_id_with_changed_event_rejected(service):
    g, jobs, p = service
    ingest_webhook(g, jobs, {"verified": "yes"}, body(p), "hook")
    with pytest.raises(GateError) as exc:
        ingest_webhook(g, jobs, {"verified": "yes"}, body(p, value="1.00"), "hook")
    assert exc.value.code == "WEBHOOK_ID_COLLISION"


def test_signature_verification_preserves_raw_event_json():
    provider = PayPalSandbox("client", "secret", "merchant", "http://localhost:3000")
    raw = b'{ "id" : "WH-ONE", "event_type" : "PAYMENT.CAPTURE.COMPLETED" }'
    headers = {"paypal-transmission-id": "t", "paypal-transmission-time": "now", "paypal-cert-url": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-ONE", "paypal-auth-algo": "SHA256withRSA", "paypal-transmission-sig": "signature"}
    calls = []
    provider.request = lambda method, path, payload: (calls.append(payload) or {"verification_status": "SUCCESS"})
    assert provider.verify_webhook(headers, raw, "hook")
    assert raw.decode() in calls[0]
    headers["paypal-cert-url"] = "http://127.0.0.1/private"
    with pytest.raises(GateError):
        provider.verify_webhook(headers, raw, "hook")
