import pytest
from agentgate.gateway import Gateway, GateError
from agentgate.payments import SimulatedPayments


def test_renewal_requires_expiry_and_reserves_again(tmp_path):
    g = Gateway(str(tmp_path / "renew.db"), SimulatedPayments())
    now = g.clock()
    g.clock = lambda: now
    p = g.propose("iris", [{"sku": "cable-20", "quantity": 1}], ttl=1)
    g.approve(p["id"], p["cart_hash"])
    g.order(p["id"], p["cart_hash"])
    with pytest.raises(GateError):
        g.renew(p["id"], p["cart_hash"])
    g.clock = lambda: now + 2
    assert g.state()["mandates"][0]["available_cents"] == 10000
    renewed = g.renew(p["id"], p["cart_hash"])
    assert renewed["state"] == "order_ready" and renewed["order_id"] == g.state()["proposals"][0]["order_id"]
    assert g.state()["mandates"][0]["reserved_cents"] == 2000


def test_renewal_cannot_overspend_after_other_approval(tmp_path):
    g = Gateway(str(tmp_path / "renew.db"), SimulatedPayments())
    now = g.clock()
    g.clock = lambda: now
    p = g.propose("iris", [{"sku": "mic-80", "quantity": 1}], ttl=1)
    g.approve(p["id"], p["cart_hash"])
    g.clock = lambda: now + 2
    other = g.propose("nova", [{"sku": "light-45", "quantity": 1}])
    g.approve(other["id"], other["cart_hash"])
    with pytest.raises(GateError) as exc:
        g.renew(p["id"], p["cart_hash"])
    assert exc.value.code == "BUDGET_EXCEEDED"
