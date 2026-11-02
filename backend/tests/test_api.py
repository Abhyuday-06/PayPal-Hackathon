import pytest
from fastapi.testclient import TestClient
from agentgate import api
from agentgate.gateway import Gateway
from agentgate.payments import SimulatedPayments


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "gateway", Gateway(str(tmp_path / "api.db"), SimulatedPayments()))
    return TestClient(api.app)


def test_owner_routes_require_owner_not_agent_credential(client):
    assert client.get("/api/state").status_code == 401
    assert client.get("/api/state", headers={"X-Agent-Token": api.AGENT_TOKENS["iris"]}).status_code == 401
    assert client.get("/api/state", headers={"X-Owner-Token": api.OWNER_TOKEN}).status_code == 200


def test_agent_identity_is_bound_to_credential(client):
    headers = {"X-Agent-Token": api.AGENT_TOKENS["iris"]}
    result = client.post("/agent/proposals", headers=headers, json={"items": [{"sku": "cable-20", "quantity": 1}]})
    assert result.status_code == 200 and result.json()["agent"] == "iris"
    assert client.post("/agent/proposals", headers=headers, json={"agent": "nova", "items": [{"sku": "cable-20", "quantity": 1}]}).status_code == 422


def test_price_injection_rejected(client):
    result = client.post("/agent/proposals", headers={"X-Agent-Token": api.AGENT_TOKENS["iris"]}, json={"items": [{"sku": "mic-80", "quantity": 1, "price_cents": 1}]})
    assert result.status_code == 422


def test_agent_cannot_approve_or_capture(client):
    headers = {"X-Agent-Token": api.AGENT_TOKENS["iris"]}
    p = client.post("/agent/proposals", headers=headers, json={"items": [{"sku": "cable-20", "quantity": 1}]}).json()
    for verb in ("approve", "order", "capture"):
        assert client.post(f"/api/proposals/{p['id']}/{verb}", headers=headers, json={"cart_hash": p["cart_hash"]}).status_code == 401


def test_missions_require_owner_and_cannot_embed_payment_authority(client):
    h = {"X-Owner-Token": api.OWNER_TOKEN}
    body = {"objective": "Build a recording setup"}
    assert client.post("/api/missions", json=body).status_code == 401
    assert client.post("/api/missions", headers={"X-Agent-Token": api.AGENT_TOKENS["iris"]}, json=body).status_code == 401
    assert client.post("/api/missions", headers=h, json={**body, "auto_approve": True}).status_code == 422
    response = client.post("/api/missions", headers=h, json=body)
    assert response.status_code == 200 and "lease_token" not in response.json()
    jid = response.json()["id"]
    assert client.post("/api/missions", headers=h, json=body).status_code == 409
    assert client.post(f"/api/missions/{jid}/approve", headers=h, json={"carts": [{"id": "0" * 32, "cart_hash": "fake"}]}).status_code == 409
    assert client.get(f"/api/missions/{jid}", headers=h).json()["proposals"] == []


def test_full_owner_flow_and_replay(client):
    h = {"X-Owner-Token": api.OWNER_TOKEN}
    p = client.post("/api/proposals", headers=h, json={"agent": "iris", "items": [{"sku": "cable-20", "quantity": 1}]}).json()
    for verb in ("approve", "order", "capture", "capture"):
        assert client.post(f"/api/proposals/{p['id']}/{verb}", headers=h, json={"cart_hash": p["cart_hash"]}).status_code == 200
    m = client.get("/api/state", headers=h).json()["mandates"][0]
    assert m["spent_cents"] == 2000 and m["available_cents"] == 8000
