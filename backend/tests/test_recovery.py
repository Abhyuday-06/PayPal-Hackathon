import json
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from agentgate.gateway import Gateway, GateError
from agentgate.jobs import Jobs
from agentgate.payments import SimulatedPayments
from agentgate.migrate import migrate
from agentgate.config import validate_deployment
from test_gateway import gate


def test_slow_provider_does_not_lock_ledger_and_duplicate_call_is_rejected(gate):
    entered, release = Event(), Event()
    calls = []
    class SlowProvider(SimulatedPayments):
        def create(self, p):
            calls.append(p["id"])
            entered.set()
            assert release.wait(5)
            return super().create(p)
    gate.provider = SlowProvider()
    other = Gateway(gate.path, SimulatedPayments())
    p = gate.propose("iris", [{"sku": "cable-20", "quantity": 1}])
    gate.approve(p["id"], p["cart_hash"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        operation = pool.submit(gate.order, p["id"], p["cart_hash"])
        try:
            assert entered.wait(2)
            snapshot = pool.submit(other.state).result(timeout=2)
            assert snapshot["mandates"][0]["reserved_cents"] == 2000
            with pytest.raises(GateError) as exc:
                other.order(p["id"], p["cart_hash"])
            assert exc.value.code == "PAYMENT_BUSY"
        finally:
            release.set()
        assert operation.result(timeout=3)["state"] == "order_ready"
    assert len(calls) == 1


def test_job_recovery_fences_old_worker_and_preserves_progress(gate):
    first, second = Jobs(gate), Jobs(Gateway(gate.path, SimulatedPayments()))
    first.enqueue("benchmark", {})
    old = first.claim()
    assert second.claim() is None
    first.update(old, rows=[{"case": "saved"}])
    with gate.tx() as db:
        job = json.loads(db.execute("SELECT data FROM jobs WHERE id=?", (old["id"],)).fetchone()[0])
        job["lease_until"] = time.time() - 1
        db.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(job), job["id"]))
    recovered = second.claim()
    assert recovered["rows"] == [{"case": "saved"}] and recovered["attempts"] == 2
    with pytest.raises(GateError) as exc:
        first.update(old, state="completed")
    assert exc.value.code == "JOB_LEASE_LOST"
    second.update(recovered, state="completed")
    assert first.claim() is None


def test_provider_recovery_failure_retains_reservation_and_hides_error_details(gate):
    p = gate.propose("iris", [{"sku": "cable-20", "quantity": 1}])
    gate.approve(p["id"], p["cart_hash"])
    gate.order(p["id"], p["cart_hash"])
    def failed_lookup(_):
        raise RuntimeError("private provider response")
    gate.provider.reconcile = failed_lookup
    with pytest.raises(GateError) as exc:
        gate.reconcile(p["id"])
    assert exc.value.code == "PROVIDER_UNAVAILABLE"
    assert "private provider response" not in exc.value.message
    mandate = gate.state()["mandates"][0]
    assert mandate["spent_cents"] == 0 and mandate["reserved_cents"] == 2000


def test_migration_preserves_receipt_and_rejects_existing_project_data(gate, tmp_path):
    if not gate.path.startswith("postgres"):
        pytest.skip("Migration requires the PostgreSQL integration fixture.")
    source = Gateway(str(tmp_path / "source.db"), SimulatedPayments())
    p = source.propose("iris", [{"sku": "cable-20", "quantity": 1}])
    source.approve(p["id"], p["cart_hash"])
    source.order(p["id"], p["cart_hash"])
    receipt = source.capture(p["id"], p["cart_hash"])["receipt"]
    counts = migrate(source.path, gate.path)
    assert counts["proposals"] == 1
    assert gate.capture(p["id"], p["cart_hash"])["receipt"] == receipt
    assert gate.state()["mandates"][0]["spent_cents"] == 2000
    with pytest.raises(ValueError, match="project data"):
        migrate(source.path, gate.path)
    assert source.state()["mandates"][0]["spent_cents"] == 2000


def test_deployment_fails_closed_without_persistent_database_or_private_keys():
    env = {"AGENTGATE_ENV": "production", "AGENTGATE_OWNER_TOKEN": "o" * 40, "AGENTGATE_IRIS_TOKEN": "i" * 40, "AGENTGATE_NOVA_TOKEN": "n" * 40, "DATABASE_URL": "postgresql://example/ledger", "FRONTEND_URL": "https://console.example", "OLLAMA_URL": "https://ollama.com"}
    validate_deployment(env)
    for changes in [{"DATABASE_URL": ""}, {"AGENTGATE_OWNER_TOKEN": "short"}, {"AGENTGATE_IRIS_TOKEN": env["AGENTGATE_OWNER_TOKEN"]}, {"FRONTEND_URL": "http://console.example"}, {"OLLAMA_URL": "http://localhost:11434"}]:
        with pytest.raises(RuntimeError):
            validate_deployment({**env, **changes})
