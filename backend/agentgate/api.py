from pathlib import Path
from contextlib import asynccontextmanager
import hashlib
import json
import os
import secrets
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from .gateway import Gateway, GateError
from .payments import SimulatedPayments, PayPalSandbox
from .agent import plan_purchase
from .lab import run_lab
from .jobs import Jobs, Worker
from .benchmark import CASE_PATH, run_benchmark, report_view
from .webhooks import ingest_webhook, reconcile_job
from .limits import RateLimiter
from .config import validate_deployment
from .missions import run_mission, mission_view, budget_for
from .demo import recorded_mission

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
validate_deployment(os.environ)
OWNER_TOKEN = os.getenv("AGENTGATE_OWNER_TOKEN", "local-agentgate-owner-change-before-sharing")
AGENT_TOKENS = {"iris": os.getenv("AGENTGATE_IRIS_TOKEN", "local-iris-proposal-only"), "nova": os.getenv("AGENTGATE_NOVA_TOKEN", "local-nova-proposal-only")}
mode = os.getenv("PAYMENT_MODE", "simulated")
if mode not in ("simulated", "paypal"):
    raise RuntimeError("PAYMENT_MODE must be simulated or paypal.")
provider = SimulatedPayments() if mode == "simulated" else PayPalSandbox(os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_CLIENT_SECRET"), os.getenv("PAYPAL_MERCHANT_ID"), os.getenv("FRONTEND_URL", "http://localhost:3000"))
db_path = Path(os.getenv("AGENTGATE_DB_PATH", str(ROOT / "agentgate.db")))
if not db_path.is_absolute():
    db_path = ROOT / db_path
gateway = Gateway(os.getenv("DATABASE_URL") or str(db_path), provider)


@asynccontextmanager
async def lifespan(app):
    jobs = Jobs(gateway)
    if os.getenv("AGENTGATE_DEMO_MODE") == "true":
        if provider.mode != "simulated":
            raise RuntimeError("Judge demo mode requires simulated payments.")
        if not jobs.list("mission"):
            recorded_mission(gateway)
    worker = Worker(jobs, {"benchmark": lambda job: run_benchmark(job, jobs, os.getenv("OLLAMA_URL", "http://localhost:11434"), job["payload"]["model"]), "mission": lambda job: run_mission(job, jobs, gateway, os.getenv("OLLAMA_URL", "http://localhost:11434")), "reconcile": lambda job: reconcile_job(gateway, jobs, job)})
    worker.start()
    yield
    worker.stop()


app = FastAPI(title="AgentGate", version="0.3.0", lifespan=lifespan, description="Coordinated recording missions, exact-cart payment policy, sandbox integration, and reproducible evaluation.")
request_limiter = RateLimiter()


@app.middleware("http")
async def request_limits(request: Request, call_next):
    if request.url.path != "/health":
        key = (request.client.host if request.client else "unknown") + (":webhook" if request.url.path.startswith("/webhooks") else ":api")
        if not request_limiter.allow(key):
            return JSONResponse(status_code=429, content={"message": "Request limit reached. Retry in a minute."}, headers={"Retry-After": "60"})
        try:
            if int(request.headers.get("content-length", "0")) > 262144:
                return JSONResponse(status_code=413, content={"message": "Request body exceeds the size limit."})
        except ValueError:
            return JSONResponse(status_code=400, content={"message": "Invalid content length."})
    return await call_next(request)


@app.exception_handler(GateError)
async def gate_error(_, exc):
    return JSONResponse(status_code=exc.status, content={"error": exc.code, "message": exc.message})


def owner(x_owner_token: Annotated[str | None, Header()] = None):
    if not x_owner_token or not secrets.compare_digest(x_owner_token, OWNER_TOKEN):
        raise GateError("UNAUTHORIZED", "An owner credential is required.", 401)


def agent_identity(x_agent_token: Annotated[str | None, Header()] = None):
    for agent, token in AGENT_TOKENS.items():
        if x_agent_token and secrets.compare_digest(x_agent_token, token):
            return agent
    raise GateError("UNAUTHORIZED", "A proposal-only agent credential is required.", 401)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Item(StrictModel):
    sku: str = Field(max_length=100)
    quantity: StrictInt = Field(ge=1, le=10)


class ProposalRequest(StrictModel):
    agent: str = Field(pattern="^(iris|nova)$")
    items: list[Item] = Field(min_length=1, max_length=6)
    mandate_id: str = Field(default="mandate-studio", max_length=100)


class AgentProposalRequest(StrictModel):
    items: list[Item] = Field(min_length=1, max_length=6)
    mandate_id: str = Field(default="mandate-studio", max_length=100)
    reason: str = Field(default="External agent suggestion", max_length=2000)


class BindingRequest(StrictModel):
    cart_hash: str = Field(min_length=1, max_length=128)


class AgentRun(StrictModel):
    agent: str = Field(pattern="^(iris|nova)$")
    prompt: str = Field(min_length=3, max_length=3000)
    mandate_id: str = Field(default="mandate-studio", max_length=100)


class MandateRequest(StrictModel):
    label: str = Field(min_length=1, max_length=100)
    budget_cents: StrictInt = Field(ge=100, le=1000000)
    max_transaction_cents: StrictInt = Field(ge=100, le=1000000)
    categories: list[str] = Field(min_length=1, max_length=10)
    agents: list[str] = Field(min_length=1, max_length=2)
    lifetime_hours: StrictInt = Field(default=24, ge=1, le=720)
    approval_ttl: StrictInt = Field(default=600, ge=60, le=3600)


class BenchmarkRequest(StrictModel):
    repeats: StrictInt = Field(default=3, ge=1, le=5)


class MissionRequest(StrictModel):
    objective: str = Field(min_length=3, max_length=1000)
    mandate_id: str = Field(default="mandate-studio", max_length=100)
    seller_text: str = Field(default="", max_length=1800)


class CartBinding(StrictModel):
    id: str = Field(pattern="^[a-f0-9]{32}$")
    cart_hash: str = Field(min_length=1, max_length=128)


class MissionApproval(StrictModel):
    carts: list[CartBinding] = Field(min_length=1, max_length=2)


@app.get("/health")
def health():
    return {"status": "ok", "payment_mode": provider.mode, "database": "postgresql" if gateway.path.startswith(("postgresql:", "postgres:")) else "sqlite"}


@app.get("/api/state", dependencies=[Depends(owner)])
def state():
    jobs = Jobs(gateway)
    return {**gateway.state(), "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), "benchmarks": [report_view(j) for j in jobs.list("benchmark")], "missions": [mission_view(gateway, j) for j in jobs.list("mission")[:10]]}


@app.post("/api/missions", dependencies=[Depends(owner)])
def start_mission(body: MissionRequest):
    budget_for(gateway, body.mandate_id)
    jobs = Jobs(gateway)
    # Global transaction makes duplicate-start checks and enqueue atomic.
    with gateway.tx() as db:
        records = [json.loads(r[0]) for r in db.execute("SELECT data FROM jobs").fetchall()]
        if any(j["kind"] == "mission" and j["state"] in ("queued", "running") for j in records):
            raise GateError("MISSION_ACTIVE", "A mission is already planning. Wait for its result.")
        return report_view(jobs.enqueue("mission", {**body.model_dump(), "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b")}, db=db))


@app.post("/api/demo/recorded-mission", dependencies=[Depends(owner)])
def replay_recorded_mission():
    return mission_view(gateway, recorded_mission(gateway))


@app.get("/api/missions/{jid}", dependencies=[Depends(owner)])
def get_mission(jid: str):
    return mission_view(gateway, Jobs(gateway).get(jid))


@app.get("/api/evaluations/missions", dependencies=[Depends(owner)])
def mission_evaluation():
    path = ROOT / "reports/mission-evaluation.json"
    if not path.is_file():
        raise GateError("EVALUATION_NOT_READY", "No recorded mission evaluation is available yet.", 404)
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/missions/{jid}/approve", dependencies=[Depends(owner)])
def approve_mission(jid: str, body: MissionApproval):
    job = Jobs(gateway).get(jid)
    if job["kind"] != "mission" or job["state"] != "completed" or set(job.get("proposal_ids", [])) != {c.id for c in body.carts}:
        raise GateError("MISSION_NOT_READY", "Review the complete set of prepared mission carts.")
    return gateway.approve_many([c.model_dump() for c in body.carts], job["payload"]["mandate_id"])


@app.post("/api/proposals", dependencies=[Depends(owner)])
def propose(body: ProposalRequest):
    return gateway.propose(body.agent, [x.model_dump() for x in body.items], mandate_id=body.mandate_id)


@app.post("/api/mandates", dependencies=[Depends(owner)])
def create_mandate(body: MandateRequest):
    return gateway.create_mandate(**body.model_dump())


@app.post("/api/proposals/{pid}/approve", dependencies=[Depends(owner)])
def approve(pid: str, body: BindingRequest):
    return gateway.approve(pid, body.cart_hash)


@app.post("/api/proposals/{pid}/order", dependencies=[Depends(owner)])
def order(pid: str, body: BindingRequest):
    return gateway.order(pid, body.cart_hash)


@app.post("/api/proposals/{pid}/capture", dependencies=[Depends(owner)])
def capture(pid: str, body: BindingRequest):
    return gateway.capture(pid, body.cart_hash)


@app.post("/api/proposals/{pid}/cancel", dependencies=[Depends(owner)])
def cancel(pid: str):
    return gateway.cancel(pid)


@app.post("/api/proposals/{pid}/renew", dependencies=[Depends(owner)])
def renew(pid: str, body: BindingRequest):
    return gateway.renew(pid, body.cart_hash)


@app.post("/api/proposals/{pid}/reconcile", dependencies=[Depends(owner)])
def reconcile(pid: str):
    return gateway.reconcile(pid)


@app.post("/api/proposals/{pid}/verify", dependencies=[Depends(owner)])
def verify_receipt(pid: str):
    return gateway.verify_receipt(pid)


@app.post("/api/agent/run", dependencies=[Depends(owner)])
def agent_run(body: AgentRun):
    return plan_purchase(gateway, body.prompt, body.agent, os.getenv("OLLAMA_URL", "http://localhost:11434"), os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), body.mandate_id)


@app.post("/api/benchmarks", dependencies=[Depends(owner)])
def start_benchmark(body: BenchmarkRequest):
    jobs = Jobs(gateway)
    if any(j["state"] in ("queued", "running") for j in jobs.list("benchmark")):
        raise GateError("BENCHMARK_ACTIVE", "A benchmark is already queued or running.")
    return jobs.enqueue("benchmark", {"repeats": body.repeats, "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), "dataset_sha256": hashlib.sha256(CASE_PATH.read_bytes()).hexdigest()})


@app.get("/api/benchmarks/{jid}", dependencies=[Depends(owner)])
def benchmark_report(jid: str):
    return report_view(Jobs(gateway).get(jid))


@app.post("/webhooks/paypal", status_code=202)
async def paypal_webhook(request: Request):
    body = await request.body()
    return ingest_webhook(gateway, Jobs(gateway), dict(request.headers), body, os.getenv("PAYPAL_WEBHOOK_ID", ""))


@app.post("/api/lab/run", dependencies=[Depends(owner)])
def lab():
    return run_lab()


@app.post("/api/demo/reset", dependencies=[Depends(owner)])
def reset():
    gateway.reset_demo()
    if os.getenv("AGENTGATE_DEMO_MODE") == "true":
        recorded_mission(gateway)
    return gateway.state()


@app.get("/agent/catalog")
def agent_catalog(agent: str = Depends(agent_identity)):
    snapshot = gateway.state()
    return {"catalog": snapshot["catalog"], "mandates": [m for m in snapshot["mandates"] if agent in m["agents"]], "agent": agent}


@app.post("/agent/proposals")
def agent_propose(body: AgentProposalRequest, agent: str = Depends(agent_identity)):
    return gateway.propose(agent, [x.model_dump() for x in body.items], reason=body.reason, source="agent_api", mandate_id=body.mandate_id)
