# AgentGate submission build

An execution gateway for AI shopping agents with measured model behavior and a persistent payment boundary.

## Architecture

Next.js owner console -> signed cookie / same-origin server proxy -> authenticated FastAPI -> reusable policy gateway -> SQLite or PostgreSQL ledger -> simulated provider or PayPal sandbox Orders API.

Configured AI provider (local Ollama, Google Cloud Vertex AI through ADC/service-account OAuth, or optional Gemini AI Studio API) -> typed purchase proposal -> same gateway. The model has no owner or payment tool. APIMatic-generated PayPal Server SDK performs authoritative order reads. Signature-verified webhook metadata queues read-only recovery. Database-backed worker jobs persist benchmark progress and reconciliation attempts.

## Implemented and verified

1. Actual sandbox order, buyer approval and $20 capture; persistent receipt replay verified without another capture.
2. Provider reconciliation, durable operation leases, explicit expired-approval renewal, and verified/deduplicated webhook ingestion with mocked-provider tests.
3. Twenty synthetic model cases, three repeats, recorded outputs and independent policy oracle. Twelve unsafe suggestions blocked; 70% semantic task success.
4. APIMatic-generated SDK integrated and queried against the actual completed order; official Context Plugin guidance applied from local source.
5. Owner sign-in, distinct agent credentials, configurable budgets, per-process rate limits, PostgreSQL migration and integration tests. Actual runtime ledger moved to PostgreSQL 17 without losing receipts or reports.
6. Locked dependencies, CI including PostgreSQL, deployment blueprint, threat model, benchmark documentation and a three-minute demo script.
7. A persisted two-agent purchase mission across the owner-authorized sample catalogue, plus a guided recording example; bounded feedback/replanning, seller-listing experiments, atomic approval of the prepared cart set, and a decision trace linking suggestions to exact fingerprints and payment evidence. The multi-category path is newer and does not yet have its own task-success evaluation.
8. An independent external agent process tested with a proposal-only Nova credential. It submitted a real model suggestion without owner authority.
9. A separate 12-mission evaluation across two models: Gemma matched 5/6 expected carts; Qwen 6/6. Neither accepted a policy violation. All 34 actual model attempts and six synthetic cases per model are retained. Qwen is the new local demo default.
10. A fresh $100 PayPal sandbox checkout completed as two provider-confirmed captures, $80 and $20, with a read-only provider verification UI and receipt export. Replaying kept the original capture IDs and totals.
11. An isolated one-command judge demo with explicit recorded-AI labels, simulated payments, separate credentials/cookies and production safeguards. Browser checks exercised its full approval/payment/replay path.
12. Public MIT-licensed GitHub repository, an upload-ready narrated 1080p video under three minutes, timed captions, a thumbnail and ready-to-paste Devpost/YouTube text. Next.js updated to 16.4.4; dependency audit reported zero vulnerabilities.

## Still open

- The YouTube walkthrough is uploaded at https://www.youtube.com/watch?v=1ey3pn47ujk (currently Unlisted, no password; 169 seconds). The Devpost form still requires owner completion. GitHub release assets remain available as a download and backup.
- A public judge preview is deployed at https://agentgate-demo-console-2026.onrender.com. It uses simulated payments and live Vertex AI Gemini 3.8 Flash planning with a dedicated service identity on the API service; the shared live-request cap is 30 per hour. Standard Vertex requests use the Google Cloud project's linked billing account; no AI Studio API key is used. The full PayPal-sandbox deployment additionally needs persistent PostgreSQL and a reachable model endpoint and remains undeployed.
- Real hosted webhook delivery must be registered and verified against PayPal.
- Context Plugin registration is blocked by the installed CLI's missing plugin command; SDK runtime integration is complete.
- Independent user feedback has not been collected. No customer-adoption claim is made.
- The storefront is still a small owned demo catalogue. Broader commerce usefulness, a dedicated evaluation of multi-category missions, comparisons with existing solutions and user validation need further work before calling this a competitive finished entry.

## Payment invariants

Integer cents and catalogue-owned price/merchant/currency; immutable cart fingerprints; scoped owner approval; transactional budget reservations; external calls outside database locks; persisted execution leases; uncertain outcomes hold funds; expired approvals never silently renew; completed receipts replay once; provider reads cannot initiate capture. PostgreSQL uses advisory locks per mandate.

See [threat model](THREAT_MODEL.md), [evaluation](BENCHMARK.md), [deployment](DEPLOYMENT.md) and [demo](DEMO.md) for evidence and limitations. The app is a single-owner sandbox prototype; no production autonomous-payment or AP2 compliance claim.
