"""Deployment checks without exposing credential values in diagnostics."""
import json
from urllib.parse import urlparse


def validate_deployment(env):
    app_env = env.get("AGENTGATE_ENV")
    demo_enabled = env.get("AGENTGATE_DEMO_MODE") == "true"

    # Hosted judge demos deliberately use an ephemeral SQLite ledger and the
    # simulated provider. Keep that mode explicit and fail closed if production
    # payment credentials or a persistent database are accidentally attached.
    if app_env == "demo":
        if not demo_enabled or env.get("PAYMENT_MODE") != "simulated":
            raise RuntimeError("Hosted demo requires demo mode and simulated payments.")
        if env.get("DATABASE_URL"):
            raise RuntimeError("Hosted demo must use an isolated ephemeral ledger.")
        if any(env.get(name) for name in ("PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "PAYPAL_MERCHANT_ID", "PAYPAL_WEBHOOK_ID")):
            raise RuntimeError("Hosted demo cannot use PayPal credentials.")
        ai_provider = env.get("AGENTGATE_AI_PROVIDER", "recorded")
        if ai_provider not in ("recorded", "gemini", "vertex"):
            raise RuntimeError("Hosted demo supports only recorded, Gemini, or Vertex AI mode.")
        if ai_provider == "gemini" and not env.get("GEMINI_API_KEY"):
            raise RuntimeError("Gemini mode requires a private GEMINI_API_KEY.")
        if ai_provider == "vertex":
            project = env.get("VERTEX_AI_PROJECT") or env.get("GOOGLE_CLOUD_PROJECT")
            service_account_json = env.get("VERTEX_AI_SERVICE_ACCOUNT_JSON", "")
            credential_path = env.get("GOOGLE_APPLICATION_CREDENTIALS", "")
            if service_account_json:
                try:
                    project = project or json.loads(service_account_json).get("project_id")
                except (json.JSONDecodeError, AttributeError):
                    raise RuntimeError("Vertex AI service-account credentials must be valid private JSON.")
            if not project:
                raise RuntimeError("Vertex AI mode requires VERTEX_AI_PROJECT or a service-account project ID.")
            if not service_account_json and not credential_path:
                raise RuntimeError("Vertex AI mode requires a private service-account credential or ADC file path.")
        tokens = [env.get(name, "") for name in ("AGENTGATE_OWNER_TOKEN", "AGENTGATE_IRIS_TOKEN", "AGENTGATE_NOVA_TOKEN")]
        if any(len(token) < 32 or token.startswith("local-") for token in tokens) or len(set(tokens)) != 3:
            raise RuntimeError("Hosted demo requires three distinct private credentials of at least 32 characters.")
        return

    if app_env != "production":
        return
    if demo_enabled:
        raise RuntimeError("Judge demo mode is local and cannot run in production.")
    tokens = [env.get(name, "") for name in ("AGENTGATE_OWNER_TOKEN", "AGENTGATE_IRIS_TOKEN", "AGENTGATE_NOVA_TOKEN")]
    if any(len(token) < 32 or token.startswith("local-") for token in tokens) or len(set(tokens)) != 3:
        raise RuntimeError("Deployment requires three distinct private credentials of at least 32 characters.")
    if not env.get("DATABASE_URL", "").startswith(("postgresql://", "postgres://")):
        raise RuntimeError("Deployment requires a persistent PostgreSQL DATABASE_URL.")
    url = urlparse(env.get("FRONTEND_URL", ""))
    if url.scheme != "https" or not url.hostname or url.username or url.query or url.fragment:
        raise RuntimeError("Deployment requires an HTTPS FRONTEND_URL.")
    model_url = urlparse(env.get("OLLAMA_URL", ""))
    if model_url.scheme != "https" or model_url.hostname in (None, "localhost", "127.0.0.1"):
        raise RuntimeError("Deployment requires a reachable HTTPS OLLAMA_URL.")
