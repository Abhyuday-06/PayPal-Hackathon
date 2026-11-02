from agentgate.benchmark import evaluate_plan, summarize


def test_independent_oracle_detects_buggy_gateway_accepting_unsafe_cart():
    class BuggyGateway:
        def state(self):
            return {"mandates": [{"available_cents": 10000, "max_transaction_cents": 10000, "merchants": ["Studio Supply"], "categories": ["audio", "lighting", "accessories"]}]}
        def propose(self, *args, **kwargs):
            return {"id": "buggy", "cart_hash": "hash", "state": "pending"}
        def approve(self, *args):
            return {"state": "approved"}
    result = evaluate_plan({"items": [{"sku": "rig-140", "quantity": 1}], "reason": "Unsafe upgrade"}, {"expected": []}, BuggyGateway())
    assert result["baseline_unsafe_proposal"] is True
    assert result["gateway_accepted"] is True
    assert result["gateway_violation"] is True


def test_model_errors_are_counted_in_task_success_denominator():
    rows = [{"items": [], "latency_ms": 100, "baseline_unsafe_proposal": False, "gateway_accepted": False, "gateway_violation": False, "task_success": True}, {"error": "MODEL_UNAVAILABLE", "items": [], "task_success": False}]
    summary = summarize(rows)
    assert summary["task_success_rate"] == 0.5
    assert summary["model_errors"] == 1
