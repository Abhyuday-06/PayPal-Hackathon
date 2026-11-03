# AgentGate

## Tagline

Give purchasing agents a budget. Keep approval and payment authority with the owner.

## Inspiration

Developers can ask a language model to respect a budget, but a prompt does not coordinate concurrent reservations or prove that a retry will not initiate another charge. Seller descriptions can also contain instructions that conflict with the owner's request. AgentGate explores an explicit execution boundary between AI purchase suggestions and PayPal payment authority.

## What it does

An owner defines a USD budget, permitted categories, merchant and assigned agents. In the demo recording mission, Iris proposes an audio input and Nova receives its cart and the remaining planning funds to select supporting gear. The model receives precise feedback after a rejected suggestion, with a bounded shortlist for replanning. Its actual outputs, catalogue reads, checks and decisions remain inspectable.

Planning does not reserve funds. The owner approves exact cart fingerprints; one transaction rechecks and reserves the full reviewed cart set or none. PayPal sandbox buyer approval remains a separate step. Order/capture requests bind to stored server-side carts. Completed receipts replay without another capture; uncertain outcomes retain their reservation until authoritative recovery.

The Payment evidence view re-reads completed orders through the PayPal sandbox API using the APIMatic-generated server SDK. It checks the saved capture, amount, currency and merchant and exports the evidence. An external example agent has proposal-only credentials and cannot approve, create an order or capture a payment.

## How we built it

Next.js/React owner console; FastAPI policy and payment API; PostgreSQL advisory locks per budget, with SQLite for an isolated local judge workspace; persisted job/payment leases; local Ollama structured model output and an optional server-side Google Gemini AI Studio provider for hosted judge missions; PayPal Orders v2 sandbox checkout and capture; generated PayPal Server SDK for authoritative reads. Both AI providers return schema-constrained proposals that are validated against server-owned catalogue and policy. Verified webhooks queue read-only reconciliation. Real hosted webhook delivery has not been validated. The public preview uses recorded AI until its Gemini API key is privately configured; all hosted preview payments remain simulated.

The public repo includes an MIT licence, locked dependencies, tests, raw model evaluations, a separate agent example and a one-command judge launcher. `python scripts/start_demo.py` provides an interactive simulated workspace with explicitly recorded AI evidence; it needs no private payment credentials or model download. Live AI and PayPal setup is documented separately.

## What we verified

- A fresh $100 recording mission completed in PayPal sandbox as $80 and $20 captures. Independent provider lookups matched both receipts; the ledger showed $100 spent and $0 reserved.
- A real planning run rejected a $45 light against $20 remaining and recorded the model's subsequent $20 cable replan.
- Six synthetic missions per model: Gemma matched 5/6 exact expected carts and Qwen 6/6; neither accepted a policy-violating cart in that small evaluation. All 34 attempts, including the failed task, are retained.
- The earlier, separate 60-trial benchmark recorded 12 unsafe suggestions blocked and 70% exact task matching. The two evaluations measure different workflows and are not combined into one accuracy claim.
- 89 automated tests passed with PostgreSQL and SQLite coverage, plus browser checks for the judge workflow, auth boundaries, evidence downloads and phone-width layouts. Dependency audit reported zero vulnerabilities after the Next.js update.

## Challenges and lessons

A small model can repeat an unaffordable suggestion despite verbal feedback. Explicit feasible options improved the bounded replan without silently substituting an item. Task usefulness and policy compliance require separate measurements. A successful provider capture can also be followed by a lost response: persisting intent and holding ambiguous reservations matters as much as a happy-path checkout.

## Scope and next steps

This is a single-owner prototype with a small server-owned catalogue and two bounded planner roles, not a universal payment firewall or an open-market shopping service. There is no independent user-adoption claim or production security assessment. Next steps are broader catalogue/integration support, independent usability feedback and recovery validation under hosted provider/webhook failures.

## Links for submission

- Public source: https://github.com/Abhyuday-06/PayPal-Hackathon
- Release/video download: https://github.com/Abhyuday-06/PayPal-Hackathon/releases/tag/v1.1.0
- Hosted demo: https://agentgate-demo-console-2026.onrender.com (simulated payments; live Gemini planning will be enabled after the Gemini-capable API build and private key are deployed; first load may take up to a minute after idle).
- Working build instructions: repository README, “Judge quick start”.
- Public YouTube URL: add after uploading the final release video.
