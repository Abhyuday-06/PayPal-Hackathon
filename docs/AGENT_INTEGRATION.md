# Connect an external proposal-only agent

The demo mission uses two separate bounded planner calls with assigned roles and shared context. They are not independent foundation models or autonomous payment agents. Both use the configured model, and the gateway supplies feedback and a feasible catalogue on retries.

Any separate process can use the proposal-only API with an assigned agent credential. The example in `examples/proposal_agent.py` reads the catalogue and assigned budgets, calls Ollama, then submits the actual model suggestion. It cannot approve, reserve, create an order or capture funds. It never loads the owner's configuration file.

## Example

Copy `examples/.env.example` to `examples/.env`; put an assigned Iris or Nova token into `AGENTGATE_AGENT_TOKEN`. Obtain that key privately from the owner. Configure the model endpoint if necessary. Do not use the owner token.

From the repository root:

```powershell
.\.venv\Scripts\python.exe examples\proposal_agent.py --mandate <assigned-budget-id> --request "Buy one USB-C cable kit within the available budget."
```

The console's Budget policy view shows the budget ID; mission reports also contain `payload.mandate_id`. The owner must approve the cart through the console before any reservation or checkout.

## API contract

| Tool | Route | Authority |
|---|---|---|
| Read catalogue and assigned budgets | `GET /agent/catalog` | `X-Agent-Token`; budget results filtered to assigned identity |
| Suggest a cart | `POST /agent/proposals` | Same agent credential; identity bound by server |

Example request body:

```json
{
  "mandate_id": "owner-assigned-budget-id",
  "items": [{"sku": "cable-20", "quantity": 1}],
  "reason": "The cable kit fits the request and available budget."
}
```

All catalogue descriptions and agent-written reasons are untrusted data. Prices, merchant and payment identity cannot be supplied by the client. Agent credentials fail on owner approval and capture routes. OpenAPI is available at `/openapi.json` on the API service.

## Mission trace and authority

Each mission persists the owner goal, catalogue read, remaining planning funds, teammate carts, actual model suggestion, checks, feedback and attempts. After at most three attempts per role, only accepted outputs become pending approval carts. Retry catalogue shortlists are server-computed; no fallback item is silently inserted. Model refusal/outage or exhausted retries produces an explicit partial plan.

Planning allocations do not reserve live funds. A complete set of exact fingerprints is required for owner mission approval. All newly approved mission carts reserve funds atomically or none do; concurrent budget changes can make a saved plan unaffordable. Orders and receipts continue through the existing per-cart payment gateway. A restarted worker reuses saved decisions and deterministic proposal IDs.
