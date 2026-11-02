import pytest
from agentgate.gateway import Gateway, GateError
from agentgate.payments import SimulatedPayments


class Provider(SimulatedPayments):
    mode = "paypal"
    def reconcile(self, p):
        return p["receipt"]


def test_provider_verification_reads_without_spending_again(tmp_path):
    g = Gateway(str(tmp_path / "evidence.db"), Provider())
    p = g.propose("iris", [{"sku":"cable-20", "quantity":1}])
    g.approve(p["id"], p["cart_hash"]); g.order(p["id"], p["cart_hash"]); g.capture(p["id"], p["cart_hash"])
    def forbidden(*args, **kwargs):
        pytest.fail("Verification must not create or capture.")
    g.provider.create = g.provider.capture = forbidden
    verified = g.verify_receipt(p["id"])
    assert verified["provider_verification"]["capture_id"] == verified["receipt"]["id"]
    assert g.state()["mandates"][0]["spent_cents"] == 2000
    g.provider.reconcile = lambda p: {**p["receipt"], "amount_cents":1}
    with pytest.raises(GateError) as exc:
        g.verify_receipt(p["id"])
    assert exc.value.code == "RECEIPT_MISMATCH"
    assert g.state()["mandates"][0]["spent_cents"] == 2000
