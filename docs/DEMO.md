# Three-minute demo and evidence

## Script

**0:00–0:20 — Problem.** “Two shopping agents can each make a reasonable recommendation and still overspend their shared budget. AgentGate coordinates a purchase mission and keeps payment authority with the owner.” Open Recording mission with a fresh $100 budget.

**0:20–0:55 — Actual AI and coordination.** Plan a recording setup. Show Iris's audio input, the budget handed to Nova and the actual supporting-gear choice. Use the saved Gemma trace to show its $45 light rejected against $20 remaining, then its actual $20 cable replan. Label that trace as recorded; a live Qwen run may choose the compliant cable immediately. Inspect the model context and authoritative price check.

**0:55–1:35 — Payment boundary.** Review and approve the exact mission carts together. Show the planned allocation becoming an actual reservation. Then show PayPal sandbox buyer approval and a completed receipt. A full mission payment video still requires the owner/buyer to complete the new carts; do not label the earlier $20 receipt as this new $100 mission. Replay a completed receipt to show spent totals remain unchanged.

**1:35–2:00 — Untrusted listings and failure controls.** Show the editable seller experiment and its actual recorded result. The latest tested malicious-listing run was resisted by the model; do not claim successful compromise. The isolated Failure lab can separately demonstrate concurrent overspending and lost-response/replay controls with explicitly simulated fault inputs.

**2:00–2:35 — Measured model behavior.** Open Live benchmark. Show the separate six-case mission comparison: Gemma matched 5/6 expected carts, Qwen 6/6; neither accepted a policy violation. Inspect the failed Gemma quantity-override mission and download the raw report. The earlier 60-trial prompt-only comparison remains a separate evaluation: 12 unsafe suggestions blocked and 70% exact task matching.

**2:35–2:55 — Architecture and takeaway.** Point to the audit trail and PostgreSQL persistence. “The model proposes. Exact-cart owner approval reserves budget atomically. PayPal buyer approval and authoritative amount/merchant checks precede capture. Uncertain outcomes hold funds until recovery.”

## Verified local evidence

- PayPal sandbox order: `93X87952FC4790325`.
- Completed $20 USD capture: `4B477058BG442852M`.
- Replay returned the original receipt, with $20 spent, $0 reserved and $80 available in the original $100 budget.
- APIMatic-generated PayPal Server SDK 2.4.0 independently read the completed order and confirmed the recorded receipt.
- The migrated PostgreSQL ledger retained that receipt and the completed benchmark.
- Automated suite: 85 passed, one migration test skipped for its SQLite parameter; PostgreSQL 17 integration tests were included. Frontend production build passed. Browser verification covered sign-in/out, protected routes, mission coordination/replanning, atomic $100 approval/release, evidence downloads, report rendering, capture replay and layouts at 360/390 pixels.
- A live Gemma mission prepared $80 audio input plus a $20 cable after rejecting a $45 light against the $20 remaining planning budget. Its earlier unsuccessful three-attempt light plan remains in history.
- An external Nova process submitted a real model suggestion using only a proposal credential. It received no approval/capture authority.
- The separate 12-mission evaluation retained 34 actual model attempts across Gemma and Qwen. Current local missions use Qwen based on this limited comparison; the catalogue is still a small demo storefront.

The sandbox represents test money, not a production charge. Webhook ingestion is tested with mocked signature responses; real remote webhook delivery still needs hosted registration and verification. Public hosting, public repository release, independent user feedback and a final video submission remain separate tasks.

## User feedback to collect

Ask three people to use the console without coaching. Have each describe available versus reserved budget, propose an allowed cart, explain a blocked request, identify the payment mode, and locate its receipt. Record completion time, misunderstood labels and one improvement suggestion. Obtain permission before recording someone or including their comments. No independent usability results have been collected yet.

## Resume wording

“Built AgentGate, an AI purchase policy gateway using Next.js, FastAPI, PostgreSQL and PayPal sandbox APIs; implemented atomic shared-budget reservations, immutable cart approval, durable payment recovery and receipt replay protection. Evaluated 60 local-model trials: blocked 12 policy-violating suggestions, with 70% task accuracy.”

Add a prize only after it is awarded. Add hosted/public links only after they work.
