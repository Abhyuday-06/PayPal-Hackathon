# AgentGate

**Give AI agents a budget. Keep payment authority with the owner.**

AgentGate combines a real Ollama shopping planner, exact-cart approval, atomic shared-budget reservations, PayPal sandbox checkout/capture, a PostgreSQL ledger, and a reproducible evaluation console. The agent proposes purchases; owner approval and PayPal buyer approval remain separate steps.

The v0.3 recording mission coordinates two bounded planner calls: Iris chooses audio input, then Nova receives its cart and the remaining planning budget to choose supporting gear. Rejected attempts receive policy feedback and a feasible catalogue for replanning. Actual suggestions, catalogue reads, checks and fingerprints are inspectable and downloadable. Planning does not reserve funds; exact mission carts are approved together atomically.

## Verified behavior

- Server-owned catalogue prices, integer USD cents, merchant/category/agent scope, immutable cart fingerprints and expiring approvals.
- Distinct owner and proposal-only agent credentials. Next.js sign-in uses a signed HttpOnly cookie and same-origin mutations.
- Persistent payment leases, unknown-outcome reservations, read-only reconciliation, webhook signature verification/deduplication and saved-receipt replay.
- PostgreSQL per-budget locks; external calls happen outside database locks. SQLite remains available for local simulation.
- Live model benchmark, raw JSON download, ten deterministic failure scenarios, configurable budgets and a responsive audit console.
- Actual $20 PayPal sandbox capture verified; replay returned the same receipt. APIMatic-generated PayPal Server SDK 2.4.0 performs authoritative order reads in the runtime adapter.

Recorded local benchmark: 60 trials, 12 unsafe suggestions, all 12 blocked, zero accepted policy violations, **70% task success**. Read [methodology and limits](docs/BENCHMARK.md); the small synthetic dataset is not a production fraud evaluation.

A separate recorded mission evaluation covers six cases each on Gemma and Qwen: **5/6 and 6/6 expected carts matched**, respectively; 34 model attempts in total and zero policy-violating suggestions accepted. These are different evaluations and should not be combined into one accuracy claim. New local missions use Qwen based on this limited comparison.

This is a single-owner sandbox prototype, with test money and a small owned storefront. [Threat model](docs/THREAT_MODEL.md) explains its boundaries.

## Fresh local setup (PowerShell)

Requires Python 3.11+, Node.js 20.9+ and optionally Ollama. Run from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
.\.venv\Scripts\python.exe scripts\bootstrap.py
Set-Location frontend
npm.cmd ci
Set-Location ..
```

Bootstrap creates missing private environment files, generates distinct keys and synchronizes the server-only owner key to the frontend. Existing payment settings are preserved. Sign in with `AGENTGATE_OWNER_TOKEN` from `backend/.env`; never commit or expose it. No credentials are printed. Default payment mode is clearly labelled simulation.

Backend terminal:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn agentgate.api:app --host 127.0.0.1 --port 8000
```

Frontend terminal:

```powershell
Set-Location frontend
npm.cmd run dev
```

Open [the console](http://127.0.0.1:3000). Backend [health](http://127.0.0.1:8000/health) and [API docs](http://127.0.0.1:8000/docs) are local. Owner requests require `X-Owner-Token`; agent catalogue/proposal routes require an assigned `X-Agent-Token`. Prefer the IPv4 URL if another local app binds localhost through IPv6.

For actual local AI, install Ollama and run `ollama pull qwen2.5:7b`. Start `ollama serve` only if the service is not already running. Configure `OLLAMA_URL` and `OLLAMA_MODEL` privately. `gemma2:2b` is a smaller tested alternative. A model outage produces an error; fixture buttons are explicitly labelled as having no model call.

## PayPal sandbox

Set `PAYMENT_MODE=paypal`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_MERCHANT_ID` and `FRONTEND_URL` in `backend/.env`. Use the merchant ID belonging to the sandbox REST app and a separate sandbox buyer. Use a separate ledger when changing payment providers; existing proposal modes cannot change. For fresh SQLite sandbox storage set `AGENTGATE_DB_PATH=agentgate-sandbox.db`. A configured `DATABASE_URL` takes precedence.

Propose a cart, approve its exact fingerprint, create the order, explicitly approve in PayPal sandbox, then capture. Approval expires; renewal is a separate owner action. Unknown outcomes retain funds and expose read-only recovery. Never delete an uncertain record to restore budget.

The current local instance uses a dedicated PostgreSQL 17 container on port 15432, configured privately. The original SQLite ledger is retained. Fresh clones default to isolated SQLite simulation and do not depend on that container.

## Verify

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ..\frontend
npm.cmd run typecheck
npm.cmd run build
```

Set `TEST_DATABASE_URL` to a dedicated test PostgreSQL database to include integration coverage. Tests create unique temporary schemas and drop only those schemas. GitHub Actions provisions PostgreSQL 17. Tests force simulation and an isolated API ledger; they never capture PayPal money or use the user's real credentials.

## Demo and deployment

- [Three-minute script and verified payment evidence](docs/DEMO.md)
- [Hosting configuration and verification checklist](docs/DEPLOYMENT.md), using `render.yaml`
- [PayPal/APIMatic usage record](docs/SPONSOR_USAGE.md)
- [Current project status](docs/PROJECT_SPEC.md)
- [External proposal-only agent example](docs/AGENT_INTEGRATION.md)

Hosting configuration is prepared; public deployment and repository release are pending. Real hosted webhook delivery, independent usability feedback, supported Context Plugin registration and the final video remain open. The generated PayPal SDK is integrated and verified; Context Plugin registration is not claimed.

MIT licensed. No prize or production security guarantee is claimed.
