"""Create private development credentials; preserve existing payment settings."""
from pathlib import Path
import secrets
from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parents[1]


def bootstrap(root=ROOT):
    backend, frontend = root / "backend/.env", root / "frontend/.env.local"
    for destination, example in [(backend, root / "backend/.env.example"), (frontend, root / "frontend/.env.example")]:
        if not destination.exists():
            destination.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    existing = dotenv_values(backend)
    for name in ("AGENTGATE_OWNER_TOKEN", "AGENTGATE_IRIS_TOKEN", "AGENTGATE_NOVA_TOKEN"):
        if not existing.get(name) or existing[name].startswith("local-"):
            set_key(str(backend), name, secrets.token_urlsafe(32))
    set_key(str(frontend), "AGENTGATE_OWNER_TOKEN", dotenv_values(backend)["AGENTGATE_OWNER_TOKEN"])
    print("Private credentials configured. Sign in using AGENTGATE_OWNER_TOKEN from backend/.env. No credentials printed.")


if __name__ == "__main__":
    bootstrap()
