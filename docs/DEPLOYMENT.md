# Deployment handoff

`render.yaml` defines two explicitly free web services: the Python API and Next.js console. No paid service or database is created by this file. The configuration has not been deployed or validated against an authenticated Render account.

## Required inputs

1. A public or Render-accessible Git repository containing this source.
2. A persistent PostgreSQL connection string, preferably TLS-required, with a dedicated empty database/schema. Do not point development tests at a shared production schema. The running local database at port 15432 is not reachable by Render.
3. An HTTPS Ollama-compatible endpoint with structured JSON output support and its installed/available model name. `localhost:11434` refers to the hosted container, not your laptop. For Ollama cloud, set `OLLAMA_URL=https://ollama.com`, choose a current available API model, and set the private `OLLAMA_API_KEY`. Cloud inference and structured-output compatibility must be verified before announcing the hosted demo. See [Ollama cloud documentation](https://docs.ollama.com/cloud).
4. Existing PayPal **sandbox** app credentials and the matching sandbox merchant ID. These belong only in backend service secrets.
5. One random owner access key of at least 32 characters, identical in both services. Generate it locally with `secrets.token_urlsafe(32)` and transfer it privately. The blueprint generates distinct agent keys for the backend.

## Configure and launch

Connect the repository in Render and import the blueprint. Set its requested variables before launch. Use the assigned console HTTPS origin as both backend `FRONTEND_URL` and frontend `AGENTGATE_CONSOLE_ORIGIN`; use the backend HTTPS origin as frontend `AGENTGATE_API_URL`. These are exact origins, without trailing slashes. A free backend requires its public HTTPS URL because free web services cannot receive private network traffic.

Use `AGENTGATE_ENV=production` in both services. The backend refuses short/default/duplicate keys, SQLite, a non-HTTPS console URL, or a localhost/non-HTTPS model endpoint. Payment adapter code fixes its API environment to PayPal sandbox. Never use `NEXT_PUBLIC_` for access keys or payment credentials.

Register backend `https://<api-host>/webhooks/paypal` in the same sandbox app for `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED` and `CHECKOUT.ORDER.APPROVED`, then save the resulting `PAYPAL_WEBHOOK_ID` privately. Without it, signature verification rejects deliveries. Real provider webhook delivery remains unverified locally. Events only enqueue authoritative read-only reconciliation; they do not initiate capture or trust event amounts. Failed reconciliation jobs retry with backoff, up to five attempts. No periodic provider polling service is claimed.

## Persistence and availability

The ledger and background-job progress live in PostgreSQL. JSON report exports also live in database jobs, so the frontend download survives ephemeral report-file loss. Run one API instance initially; request/login throttles are in-process. Worker leases fence stale jobs, and per-budget advisory locks serialize reservations; external API calls occur outside database locks.

Render free services sleep after 15 idle minutes and may take roughly a minute to wake. Both services share the workspace's free-hour allowance. Free Render Postgres expires after 30 days and has no managed backups. Choose a database lifetime covering the entire review period, and export backups; this blueprint deliberately does not provision an expiring database. Review bandwidth/build overage settings. See [Render free-service limits](https://render.com/docs/free) and [blueprint reference](https://render.com/docs/blueprint-spec).

## Verification before sharing

- Health returns `paypal` and `postgresql`; anonymous gateway access returns 401.
- Sign in, load budgets, submit a live AI request, and download a completed report. Verify secure HttpOnly owner cookies and same-origin mutations.
- Create a fresh small sandbox cart, approve the exact cart, approve as a sandbox buyer, and capture. Replaying returns the same receipt. Restart the API and verify spent totals/receipts persist.
- Confirm real webhook signature verification and provider reconciliation. Record actual order/capture IDs and webhook event ID privately as evidence.
- Run the failure lab and a new benchmark for the deployed model. Do not label the local gemma2 report as a hosted-model result.
- Test phone layout, sign-out, incorrect credentials, and a model outage. Give judges access through a private owner key; anyone holding it has owner authority.

## Moving the current SQLite ledger

Stop the API and finish all background jobs first. Back up the source file. Set private `DATABASE_URL` to an empty PostgreSQL database; from `backend`, run:

```powershell
..\.venv\Scripts\python.exe -m agentgate.migrate --sqlite agentgate-sandbox.db
```

The command refuses destination project data and active jobs/payment operations. The source is read-only and retained. It copies mandates, proposals, audit events, webhook metadata and jobs in one destination transaction. The local sandbox ledger has already been migrated to the dedicated PostgreSQL 17 container, keeping its original SQLite file.
