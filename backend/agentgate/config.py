"""Deployment checks without exposing credential values in diagnostics."""
from urllib.parse import urlparse


def validate_deployment(env):
    if env.get("AGENTGATE_ENV") != "production":
        return
    if env.get("AGENTGATE_DEMO_MODE") == "true":
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
