# AgentGate

## Tagline

Give purchasing agents a budget. Keep approval and payment authority with the owner.

## Elevator pitch

Let AI agents plan purchases while the owner keeps budget, approval, and PayPal payment authority.

## Built with

PayPal Sandbox, PayPal Orders v2, APIMatic-generated PayPal Server SDK, Google Cloud Vertex AI, Gemini 3.8 Flash, Python, FastAPI, Next.js, React, PostgreSQL, SQLite, Ollama, Qwen 2.5, Gemma 2, Render, GitHub Actions.

## Inspiration

Developers can ask a language model to respect a budget, but a prompt does not coordinate concurrent reservations or prove that a retry will not initiate another charge. Seller descriptions can also contain instructions that conflict with the owner's request. AgentGate explores an explicit execution boundary between AI purchase suggestions and PayPal payment authority.

## What it does

An owner defines a USD budget, permitted categories, merchant and assigned agents. Goal-based missions plan across a small, server-owned sample catalogue of audio, video, lighting, accessories and office gear: Iris selects one primary item, then Nova sees that cart and the remaining planning funds and may add one useful complement. A guided recording mission preserves the verified end-to-end example. The model receives precise feedback after a rejected suggestion and a bounded feasible shortlist for replanning. Its actual outputs, catalogue reads, policy checks and decisions remain inspectable.

Planning does not reserve funds. The owner approves exact cart fingerprints; one transaction rechecks and reserves the full reviewed cart set or none. PayPal sandbox buyer approval remains a separate step. Order/capture requests bind to stored server-side carts. Completed receipts replay without another capture; uncertain outcomes retain their reservation until authoritative recovery.

The Payment evidence view re-reads completed orders through the PayPal sandbox API using the APIMatic-generated server SDK. It checks the saved capture, amount, currency and merchant and exports the evidence. An external example agent has proposal-only credentials and cannot approve, create an order or capture a payment.

## How we built it

Next.js/React owner console; FastAPI policy and payment API; PostgreSQL advisory locks per budget, with SQLite for an isolated local judge workspace; persisted job/payment leases; local Ollama structured model output, Google Cloud Vertex AI through ADC/service-account OAuth, and an optional server-side Gemini AI Studio provider; PayPal Orders v2 sandbox checkout and capture; generated PayPal Server SDK for authoritative reads. AI providers return schema-constrained proposals that are validated against the server-owned catalogue and policy. Verified webhooks queue read-only reconciliation. Real hosted webhook delivery has not been validated. The public preview runs live Vertex AI Gemini 3.8 Flash with a 30-call hourly cap; standard Vertex usage bills through the linked Google Cloud project. All hosted preview payments remain simulated.

The public repo includes an MIT licence, locked dependencies, tests, raw model evaluations, a separate agent example and a one-command judge launcher. `python scripts/start_demo.py` provides an interactive simulated workspace with explicitly recorded AI evidence; it needs no private payment credentials or model download. Live AI and PayPal setup is documented separately.

## What we verified

- A fresh $100 recording mission completed in PayPal sandbox as $80 and $20 captures. Independent provider lookups matched both receipts; the ledger showed $100 spent and $0 reserved.
- A real planning run rejected a $45 light against $20 remaining and recorded the model's subsequent $20 cable replan.
- Six synthetic guided-recording missions per model: Gemma matched 5/6 exact expected carts and Qwen 6/6; neither accepted a policy-violating cart in that small evaluation. All 34 attempts, including the failed task, are retained. The newer multi-category mode has not yet received a separate task-success evaluation.
- The earlier, separate 60-trial benchmark recorded 12 unsafe suggestions blocked and 70% exact task matching. The two evaluations measure different workflows and are not combined into one accuracy claim.
- Latest GitHub Actions run on the submitted revision: 97 backend tests passed with PostgreSQL 17 and SQLite coverage (one intentional skip); frontend typecheck and production build passed. The local SQLite run passed 60 tests with one PostgreSQL-only integration skip. Earlier browser checks covered the judge workflow, auth boundaries, evidence downloads and phone-width layouts.

## Challenges and lessons

A small model can repeat an unaffordable suggestion despite verbal feedback. Explicit feasible options improved the bounded replan without silently substituting an item. Task usefulness and policy compliance require separate measurements. A successful provider capture can also be followed by a lost response: persisting intent and holding ambiguous reservations matters as much as a happy-path checkout.

## Scope and next steps

This is a single-owner prototype with a small server-owned sample catalogue and two bounded planner roles, not a universal payment firewall or an open-market shopping service. Goal-based missions work only with catalogue items, categories and merchants allowed by the owner. There is no independent user-adoption claim or production security assessment. Next steps are more catalogue/merchant integrations, a dedicated evaluation of the newer multi-category mission mode, independent usability feedback and recovery validation under hosted provider/webhook failures.

## Links for submission

- Public source: https://github.com/Abhyuday-06/PayPal-Hackathon
- Release/video download: https://github.com/Abhyuday-06/PayPal-Hackathon/releases/tag/v1.1.0
- Hosted demo: https://agentgate-demo-console-2026.onrender.com (live Vertex AI planning and simulated payments; first load may take up to a minute after idle).
- Working build instructions: repository README, “Judge quick start”.
- YouTube demonstration video (currently Unlisted, no password): https://www.youtube.com/watch?v=1ey3pn47ujk

## Other Devpost fields

- **Built with / sponsor tools:** Select APIMatic (the APIMatic-generated PayPal Server SDK performs authoritative order reads) and Render (free hosted console and API). Do not claim AG Grid or APIMatic Context Plugin use; the plugin was not registered or invoked.
- **Project status:** New. Repository history begins November 2, 2026, after the October 1 submission-period start. If asked what existed before October 1, enter `N/A — new project`.
- **Public code repository:** https://github.com/Abhyuday-06/PayPal-Hackathon
- **Working demo:** https://agentgate-demo-console-2026.onrender.com
- **Testing instructions:** Open the hosted demo and choose **Explore public demo**. On **Purchase mission**, click **Create a fresh $100 mission budget** to enable the full sample catalogue; older budgets keep their original category limits. Choose **Sample catalogue** and start a goal such as Remote work or Online teaching. The hosted preview provides live Vertex AI planning, capped at 30 calls per hour, with simulated payments. No test credentials are required. The first request may take about a minute while the free service wakes. For a credential-free local run, follow **Judge quick start** in the repository README; that path uses explicitly labelled recorded AI and simulated payments. The video shows the separate real PayPal sandbox checkout and provider verification.
- **Upload file:** `submission/AgentGate-Devpost-Upload.zip` (source-only archive; below the 35 MB limit). The project thumbnail is in the archive at `submission/render-v2/AgentGate-Thumbnail.png`.
- **AI tools used:** OpenAI Codex for development assistance; Google Cloud Vertex AI Gemini 3.8 Flash for hosted planning; local Ollama with Qwen 2.5 7B and Gemma 2 2B for model runs and evaluation.
- **APIMatic Context Plugin experience:** Not used. The runtime uses the APIMatic-generated PayPal Server SDK; no Context Plugin invocation is claimed.
- **AG Grid experience:** Not used.
- **PayPal integration rating:** Choose your own honest 1–10 rating. Suggested feedback: “PayPal sandbox Orders v2 made checkout and capture reproducible. The harder work was binding approval to the exact server-side cart and safely reconciling uncertain outcomes. The generated SDK made authoritative order verification clearer.”
- **Open to follow-up PayPal feedback:** Choose Yes or No based on your preference.
- **Learning level / career value:** Choose these yourself; they describe your personal experience.
- **Submitter type, country, organization, and eligibility declarations:** Entrant must choose and affirm these personally. Use `N/A` for Canadian province if you do not reside in Canada, and for organization name if entering as an individual.

The YouTube video is currently Unlisted. The submission form copy accepts Public or Unlisted, but the official rules say the video must be publicly visible; set it to **Public** before submitting to remove ambiguity.
