import json
import httpx
from agentgate import agent


def test_gemini_provider_uses_server_key_and_structured_output(monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def post(self, url, *, headers, json):
            calls.append((url, headers, json))
            return httpx.Response(200, json={
                "candidates": [{"content": {"parts": [{"text": '{"items":[{"sku":"mic-80","quantity":1}],"reason":"Fits the recording goal."}'}]}}],
                "usageMetadata": {"promptTokenCount": 42, "candidatesTokenCount": 18},
            })

    monkeypatch.setattr(agent.httpx, "Client", FakeClient)
    monkeypatch.setenv("AGENTGATE_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "private-test-key")
    monkeypatch.setenv("AGENTGATE_AI_MODEL", "gemini-3.8-flash")
    result = agent.generate_plan(
        "Choose one microphone for a voice demo.",
        {"available_cents": 10000, "currency": "USD", "max_transaction_cents": 10000, "merchants": ["Studio Supply"], "categories": ["audio"]},
        [{"sku": "mic-80", "price_cents": 8000, "merchant": "Studio Supply", "category": "audio"}],
        "unused",
        "gemini-3.8-flash",
    )

    assert result["provider"] == "gemini"
    assert result["prompt_tokens"] == 42 and result["output_tokens"] == 18
    assert result["items"] == [{"sku": "mic-80", "quantity": 1}]
    assert calls[0][0] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    assert calls[0][1] == {"x-goog-api-key": "private-test-key"}
    request = calls[0][2]
    assert request["generationConfig"]["responseMimeType"] == "application/json"
    assert request["generationConfig"]["responseJsonSchema"]["properties"]["items"]["items"]["properties"]["sku"]["enum"] == ["mic-80"]
    assert "private-test-key" not in json.dumps(request)


def test_hosted_demo_defaults_to_recorded_and_disables_live_ai_without_key(monkeypatch):
    monkeypatch.setenv("AGENTGATE_ENV", "demo")
    monkeypatch.delenv("AGENTGATE_AI_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert agent.configured_ai() == ("recorded", "recorded qwen2.5:7b")
    assert agent.ai_available() is False
