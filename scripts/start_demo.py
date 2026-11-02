"""One command: isolated simulated judge demo, with recorded AI evidence."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-port", type=int, default=8100)
    parser.add_argument("--port", type=int, default=3100)
    args = parser.parse_args()
    for port in (args.api_port, args.port):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise SystemExit(f"Port {port} is in use. Choose --api-port and --port for a separate demo.")
    if not shutil.which("node") or not shutil.which("npm"):
        raise SystemExit("Install Node.js 22 LTS (including npm) first.")
    python = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
    if not python.exists():
        subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
    if subprocess.run([str(python), "-c", "import fastapi,uvicorn,psycopg,paypalserversdk"], capture_output=True).returncode:
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(ROOT / "backend/requirements.lock.txt")], check=True)
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not (ROOT / "frontend/node_modules/next").exists():
        subprocess.run([npm, "ci"], cwd=ROOT / "frontend", check=True)
    key = secrets.token_urlsafe(32)
    env = {**os.environ, "AGENTGATE_ENV": "development", "AGENTGATE_BUILD_DIR": ".next-demo", "AGENTGATE_DEMO_MODE": "true", "PAYMENT_MODE": "simulated", "DATABASE_URL": "", "AGENTGATE_DB_PATH": str(ROOT / "backend/judge-demo.db"), "AGENTGATE_OWNER_TOKEN": key, "AGENTGATE_IRIS_TOKEN": secrets.token_urlsafe(32), "AGENTGATE_NOVA_TOKEN": secrets.token_urlsafe(32), "AGENTGATE_API_URL": f"http://127.0.0.1:{args.api_port}", "AGENTGATE_CONSOLE_ORIGIN": f"http://127.0.0.1:{args.port}", "FRONTEND_URL": f"http://127.0.0.1:{args.port}"}
    processes = []
    try:
        processes.append(subprocess.Popen([str(python), "-m", "uvicorn", "agentgate.api:app", "--host", "127.0.0.1", "--port", str(args.api_port)], cwd=ROOT / "backend", env=env))
        node = shutil.which("node")
        processes.append(subprocess.Popen([node, str(ROOT / "frontend/node_modules/next/dist/bin/next"), "dev", "--hostname", "127.0.0.1", "--port", str(args.port)], cwd=ROOT / "frontend", env=env))
        print(f"\nAgentGate judge demo: http://127.0.0.1:{args.port}\nClick Explore simulated demo. No PayPal credentials, Docker or model download required.\nRecorded AI is labelled; live planning requires Ollama. Ctrl+C stops both servers.\n", flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    main()
