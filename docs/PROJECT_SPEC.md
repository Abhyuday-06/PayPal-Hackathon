# AgentGate submission build

An execution gateway for AI shopping agents with measured model behavior and a persistent payment boundary.

## Architecture

Next.js owner console -> signed cookie / same-origin server proxy -> authenticated FastAPI -> reusable policy gateway -> SQLite or PostgreSQL ledger -> simulated provider or PayPal sandbox Orders API.

Configured AI provider (local Ollama or optional Gemini API) -> typed purchase proposal -> same gateway. The model has no owner or payment tool. APIMatic-generated PayPal Server SDK performs authoritative order reads. Signature-verified webhook metadata queues read-only recovery. Database-backed worker jobs persist benchmark progress and reconciliation attempts.

## Implemented and verified

1. Actual sandbox order, buyer approval and $20 capture; persistent receipt replay verified without another capture.
2. Provider reconciliation, durable operation leases, explicit expired-approval renewal, and verified/deduplicated webhook ingestion with mocked-provider tests.
3. Twenty synthetic model cases, three repeats, recorded outputs and independent policy oracle. Twelve unsafe suggestions blocked; 70% semantic task success.
4. APIMatic-generated SDK integrated and queried against the actual completed order; official Context Plugin guidance applied from local source.
5. Owner sign-in, distinct agent credentials, configurable budgets, per-process rate limits, PostgreSQL migration and integration tests. Actual runtime ledger moved to PostgreSQL 17 without losing receipts or reports.
6. Locked dependencies, CI including PostgreSQL, deployment blueprint, threat model, benchmark documentation and a three-minute demo script.
7. A persisted two-agent recording mission, bounded feedback/replanning, editable seller-listing experiments, atomic approval of the prepared cart set, and a decision trace linking actual suggestions to exact fingerprints and payment evidence.
8. An independent external agent process tested with a proposal-only Nova credential. It submitted a real model suggestion without owner authority.
9. A separate 12-mission evaluation across two models: Gemma matched 5/6 expected carts; Qwen 6/6. Neither accepted a policy violation. All 34 actual model attempts and six synthetic cases per model are retained. Qwen is the new local demo default.
10. A fresh $100 PayPal sandbox checkout completed as two provider-confirmed captures, $80 and $20, with a read-only provider verification UI and receipt export. Replaying kept the original capture IDs and totals.
11. An isolated one-command judge demo with explicit recorded-AI labels, simulated payments, separate credentials/cookies and production safeguards. Browser checks exercised its full approval/payment/replay path.
12. Public MIT-licensed GitHub repository, an upload-ready narrated 1080p video under three minutes, timed captions, a thumbnail and ready-to-paste Devpost/YouTube text. Next.js updated to 16.4.4; dependency audit reported zero vulnerabilities.

## Still open

- Public YouTube upload/link and the Devpost form still require completion. GitHub release assets are not a substitute for the required public YouTube URL.
- A public judge preview is deployed at https://agentgate-demo-console-2026.onrender.com. It uses simulated payments and recorded AI unless the private Gemini API key is added and the new provider build is deployed. The full PayPal-sandbox deployment additionally needs persistent PostgreSQL and a reachable model endpoint and remains undeployed.
- Real hosted webhook delivery must be registered and verified against PayPal.
- Context Plugin registration is blocked by the installed CLI's missing plugin command; SDK runtime integration is complete.
- Independent user feedback has not been collected. No customer-adoption claim is made.
- The storefront is still a small owned demo catalogue. Broader commerce usefulness, comparisons with existing solutions and user validation need further work before calling this a competitive finished entry.

## Payment invariants

Integer cents and catalogue-owned price/merchant/currency; immutable cart fingerprints; scoped owner approval; transactional budget reservations; external calls outside database locks; persisted execution leases; uncertain outcomes hold funds; expired approvals never silently renew; completed receipts replay once; provider reads cannot initiate capture. PostgreSQL uses advisory locks per mandate.

See [threat model](THREAT_MODEL.md), [evaluation](BENCHMARK.md), [deployment](DEPLOYMENT.md) and [demo](DEMO.md) for evidence and limitations. The app is a single-owner sandbox prototype; no production autonomous-payment or AP2 compliance claim.
