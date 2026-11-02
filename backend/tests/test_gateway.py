from concurrent.futures import ThreadPoolExecutor
import pytest
from agentgate.gateway import Gateway, GateError
from agentgate.payments import SimulatedPayments, PayPalSandbox
from agentgate.lab import run_lab
import os
import uuid
from urllib.parse import urlencode, quote


@pytest.fixture(params=["sqlite", "postgres"] if os.getenv("TEST_DATABASE_URL") else ["sqlite"])
def gate(tmp_path, request):
    if request.param == "sqlite":
        yield Gateway(str(tmp_path / "ledger.db"), SimulatedPayments())
        return
    import psycopg
    from psycopg import sql
    schema = "agentgate_test_" + uuid.uuid4().hex[:12]
    url = os.environ["TEST_DATABASE_URL"]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        scoped = url + ("&" if "?" in url else "?") + urlencode({"options": "-c search_path=" + schema}, quote_via=quote)
        yield Gateway(scoped, SimulatedPayments())
    finally:
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def proposal(g, sku="mic-80", agent="iris", **kwargs):
    return g.propose(agent, [{"sku": sku, "quantity": 1}], **kwargs)


def test_two_independent_workers_cannot_overspend(gate):
    other = Gateway(gate.path, SimulatedPayments())
    a, b = proposal(gate), proposal(other, agent="nova")
    def approve(args):
        g, p = args
        try:
            return g.approve(p["id"], p["cart_hash"])["state"]
        except GateError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(approve, [(gate, a), (other, b)]))
    assert sorted(outcomes) == ["BUDGET_EXCEEDED", "approved"]
    assert gate.state()["mandates"][0]["reserved_cents"] == 8000
    assert gate.state()["mandates"][0]["available_cents"] == 2000


def test_capture_replay_is_durable_across_gateway_instances(gate):
    p = proposal(gate, "cable-20")
    gate.approve(p["id"], p["cart_hash"])
    gate.order(p["id"], p["cart_hash"])
    first = gate.capture(p["id"], p["cart_hash"])
    restarted = Gateway(gate.path, SimulatedPayments())
    second = restarted.capture(p["id"], p["cart_hash"])
    assert first["receipt"] == second["receipt"]
    assert restarted.state()["mandates"][0]["spent_cents"] == 2000


def test_approving_twice_reserves_once(gate):
    p = proposal(gate)
    for _ in range(2):
        gate.approve(p["id"], p["cart_hash"])
    assert gate.state()["mandates"][0]["reserved_cents"] == 8000


def test_expired_order_cannot_capture_and_releases_unused_reservation(gate):
    now = gate.clock()
    gate.clock = lambda: now
    p = proposal(gate, ttl=1)
    gate.approve(p["id"], p["cart_hash"])
    gate.order(p["id"], p["cart_hash"])
    gate.clock = lambda: now + 2
    with pytest.raises(GateError) as exc:
        gate.capture(p["id"], p["cart_hash"])
    assert exc.value.code == "ORDER_REQUIRED"
    assert gate.state()["mandates"][0]["available_cents"] == 10000


def test_changed_cart_cannot_execute_but_original_can(gate):
    p = proposal(gate)
    gate.approve(p["id"], p["cart_hash"])
    with pytest.raises(GateError) as exc:
        gate.order(p["id"], "forged-hash")
    assert exc.value.code == "CART_CHANGED"
    assert gate.state()["mandates"][0]["reserved_cents"] == 8000
    assert gate.order(p["id"], p["cart_hash"])["state"] == "order_ready"


def test_unapproved_proposal_cannot_create_order(gate):
    p = proposal(gate)
    with pytest.raises(GateError) as exc:
        gate.order(p["id"], p["cart_hash"])
    assert exc.value.code == "APPROVAL_REQUIRED"


@pytest.mark.parametrize("sku,code", [("rig-140", "TRANSACTION_LIMIT"), ("watch-300", "CATEGORY_NOT_ALLOWED"), ("external-20", "MERCHANT_NOT_ALLOWED")])
def test_prohibited_products_cannot_be_approved(gate, sku, code):
    p = proposal(gate, sku)
    assert p["block_code"] == code
    with pytest.raises(GateError):
        gate.approve(p["id"], p["cart_hash"])
    assert gate.state()["mandates"][0]["reserved_cents"] == 0


@pytest.mark.parametrize("qty", [0, -1, 11, 1.5, True, "1"])
def test_quantity_cannot_bypass_integer_amount_rules(gate, qty):
    with pytest.raises(GateError):
        gate.propose("iris", [{"sku": "mic-80", "quantity": qty}])


def test_duplicate_lines_cannot_hide_quantities(gate):
    with pytest.raises(GateError):
        gate.propose("iris", [{"sku": "mic-80", "quantity": 1}] * 2)


def test_cancelled_reservation_is_available_to_other_agent(gate):
    first = proposal(gate)
    gate.approve(first["id"], first["cart_hash"])
    gate.cancel(first["id"])
    second = proposal(gate, agent="nova")
    assert gate.approve(second["id"], second["cart_hash"])["state"] == "approved"


class TimeoutOnce(SimulatedPayments):
    def __init__(self):
        self.saved_receipt = None

    def capture(self, p, allow_new=True):
        if self.saved_receipt:
            return self.saved_receipt
        self.saved_receipt = super().capture(p, allow_new)
        raise TimeoutError("Payment succeeded but the response was lost")


def test_uncertain_capture_keeps_funds_and_reconciles_even_after_expiry(gate):
    gate.provider = TimeoutOnce()
    now = gate.clock()
    gate.clock = lambda: now
    p = proposal(gate, ttl=1)
    gate.approve(p["id"], p["cart_hash"])
    gate.order(p["id"], p["cart_hash"])
    with pytest.raises(GateError) as exc:
        gate.capture(p["id"], p["cart_hash"])
    assert exc.value.code == "PROVIDER_UNCERTAIN"
    gate.clock = lambda: now + 2
    assert gate.state()["mandates"][0]["reserved_cents"] == 8000
    with pytest.raises(GateError):
        gate.cancel(p["id"])
    assert gate.capture(p["id"], p["cart_hash"])["state"] == "captured"
    m = gate.state()["mandates"][0]
    assert m["spent_cents"] == 8000 and m["reserved_cents"] == 0


def test_provider_change_cannot_turn_simulation_into_paypal_charge(gate):
    p = proposal(gate)
    gate.approve(p["id"], p["cart_hash"])
    gate.provider = type("DifferentProvider", (), {"mode": "paypal"})()
    with pytest.raises(GateError) as exc:
        gate.order(p["id"], p["cart_hash"])
    assert exc.value.code == "MODE_CHANGED"


def test_process_crash_during_capture_cannot_release_reserved_money(gate):
    class CrashingProvider(SimulatedPayments):
        def capture(self, p, allow_new=True):
            raise KeyboardInterrupt("Simulated process death during external request")
    p = proposal(gate, ttl=1)
    gate.approve(p["id"], p["cart_hash"])
    gate.order(p["id"], p["cart_hash"])
    gate.provider = CrashingProvider()
    with pytest.raises(KeyboardInterrupt):
        gate.capture(p["id"], p["cart_hash"])
    now = gate.clock()
    restarted = Gateway(gate.path, SimulatedPayments(), clock=lambda: now + 2)
    assert restarted.state()["proposals"][0]["state"] == "capture_uncertain"
    assert restarted.state()["mandates"][0]["reserved_cents"] == 8000


def authoritative_order(p, status="APPROVED"):
    return {"id": p["order_id"], "intent": "CAPTURE", "status": status, "purchase_units": [{"custom_id": p["id"], "payee": {"merchant_id": "MERCHANT"}, "amount": {"currency_code": "USD", "value": "80.00"}}]}


@pytest.mark.parametrize("field", ["amount", "currency", "merchant", "reference"])
def test_paypal_verifies_remote_order_before_capture(gate, field):
    p = proposal(gate)
    p["order_id"] = "ORDER"
    order = authoritative_order(p)
    unit = order["purchase_units"][0]
    if field == "amount": unit["amount"]["value"] = "81.00"
    if field == "currency": unit["amount"]["currency_code"] = "EUR"
    if field == "merchant": unit["payee"]["merchant_id"] = "OTHER"
    if field == "reference": unit["custom_id"] = "OTHER"
    provider = PayPalSandbox("client", "secret", "MERCHANT", "http://localhost:3000")
    calls = []
    def fake_request(method, *args):
        calls.append(method)
        return order
    provider.request = fake_request
    with pytest.raises(GateError) as exc:
        provider.capture(p)
    assert exc.value.code == "ORDER_MISMATCH"
    assert calls == ["GET"]


def test_paypal_reconciliation_does_not_post_a_second_capture(gate):
    p = proposal(gate)
    p["order_id"] = "ORDER"
    order = authoritative_order(p, "COMPLETED")
    order["purchase_units"][0]["payments"] = {"captures": [{"id": "CAPTURE", "status": "COMPLETED", "amount": {"value": "80.00", "currency_code": "USD"}}]}
    provider = PayPalSandbox("client", "secret", "MERCHANT", "http://localhost:3000")
    calls = []
    provider.request = lambda method, *args: (calls.append(method) or order)
    assert provider.capture(p, allow_new=False)["id"] == "CAPTURE"
    assert calls == ["GET"]


def test_lab_isolated_and_all_checks_pass(gate):
    before = gate.state()
    report = run_lab()
    assert report["passed"] == report["total"] == 10
    assert report["uses_live_model"] is False
    assert gate.state() == before
