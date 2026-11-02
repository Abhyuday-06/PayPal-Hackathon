import pytest
from agentgate.demo import recorded_mission
from agentgate.gateway import GateError, Gateway
from agentgate.payments import SimulatedPayments


def test_recorded_demo_is_explicit_and_still_requires_owner_approval(tmp_path):
    g = Gateway(str(tmp_path / "demo.db"), SimulatedPayments())
    job = recorded_mission(g)
    assert job["payload"]["recorded"] is True
    with g.tx() as db:
        proposals = [g.get_proposal(db, pid) for pid in job["proposal_ids"]]
    assert len(proposals) == 2 and all(p["source"].startswith("recorded:") and p["state"] == "pending" for p in proposals)
    p = proposals[0]
    with pytest.raises(GateError):
        g.order(p["id"], p["cart_hash"])
    g.approve_many([{"id": p["id"], "cart_hash": p["cart_hash"]} for p in proposals], job["payload"]["mandate_id"])
    for p in proposals:
        g.order(p["id"], p["cart_hash"])
        g.capture(p["id"], p["cart_hash"])
    m = next(m for m in g.state()["mandates"] if m["id"] == job["payload"]["mandate_id"])
    assert m["spent_cents"] == 10000 and m["reserved_cents"] == 0


def test_recorded_replay_cannot_enter_paypal_workspace(tmp_path):
    class Sandbox(SimulatedPayments):
        mode = "paypal"
    g = Gateway(str(tmp_path / "sandbox.db"), Sandbox())
    with pytest.raises(GateError) as exc:
        recorded_mission(g)
    assert exc.value.code == "SIMULATION_REQUIRED"


def test_demo_reset_clears_completed_mission_references_but_refuses_active_jobs(tmp_path):
    from agentgate.jobs import Jobs
    g = Gateway(str(tmp_path / "reset.db"), SimulatedPayments())
    recorded_mission(g)
    g.reset_demo()
    assert Jobs(g).list() == [] and g.state()["proposals"] == []
    Jobs(g).enqueue("mission", {})
    with pytest.raises(GateError) as exc:
        g.reset_demo()
    assert exc.value.code == "RESET_BUSY"
