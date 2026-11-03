# Final demo and verified evidence

The narrated video, captions and thumbnail are available in the [v1.0.0 release](https://github.com/Abhyuday-06/PayPal-Hackathon/releases/tag/v1.0.0). The production source and full narration are in `submission/`. The cut is approximately 2 minutes 50 seconds, with actual app footage, annotated chapters, camera zooms and word-timed English captions. Loading/setup is removed.

## Story

1. The audience is developers building purchasing agents; prompts alone do not coordinate shared budgets or establish payment authority.
2. A real local-model recording mission proposes an $80 microphone, rejects a $45 light against $20 remaining, and records the actual $20 cable replan.
3. The owner reviews exact carts and approves the $100 set atomically. Planning and reservations are visibly distinct.
4. Following separate sandbox buyer approvals, the server captures the $80 and $20 orders and independently verifies their receipts against PayPal.
5. Receipt replay preserves the original capture; the explicitly simulated failure lab demonstrates concurrency, cart changes, expiry and replay controls.
6. The recorded two-model evaluation retains successful and failed tasks, with raw evidence downloads.
7. The public source includes proposal-only agent integration and a credential-free, simulated judge launcher.

Planning/approval footage and payment footage come from matching actual runs. The opening conflict diagram is illustrative, and all payments use test money. No account credentials or buyer login footage is published. See `submission/README.md` for provenance.

## Fresh completed PayPal mission

| Item | Order | Completed capture | Amount |
|---|---|---|---:|
| Microphone | `16921357L95113718` | `1WS730284T000071P` | $80 USD |
| Cable kit | `3EK48344DY6010040` | `90F18819DJ870472M` | $20 USD |

Both orders were approved by the sandbox buyer, captured through the gateway, and independently verified using the APIMatic-generated PayPal Server SDK. The mission ledger showed **$100 spent, $0 reserved**. The original $20 capture `4B477058BG442852M` remains preserved as earlier integration evidence.

## Validation

- 89 automated tests passed, including PostgreSQL 17 and SQLite coverage; one migration parameter is intentionally skipped for SQLite.
- Next.js 16.4.4 production build passed; npm dependency audit reported zero vulnerabilities.
- Browser verification covered owner authentication, foreign-origin rejection, disabled demo entry in the PayPal workspace, recorded-output labels, full simulated approval/payment/replay, evidence downloads and 360/390-pixel layouts.
- Six mission cases per model: Gemma 5/6 expected carts, Qwen 6/6; zero policy violations accepted across 34 actual model attempts. Small synthetic scope, no general model-ranking claim.
- The final media QA report records dimensions, codecs, duration, loudness, decoding and caption checks. A separate optional local speech recognizer checks the audio transcription.

## Remaining publication and validation steps

Upload the video publicly to YouTube using `submission/YOUTUBE.md`, then paste its public URL and `submission/DEVPOST.md` into the Devpost entry. A GitHub MP4 is not a substitute for the required YouTube link. The hosted judge preview is https://agentgate-demo-console-2026.onrender.com and uses recorded AI output with simulated payments; the video carries the live-model and PayPal sandbox evidence. Independent user feedback and real hosted webhook delivery are not claimed. The documented local judge launcher remains available as an alternative.

## User feedback to collect

Ask three people to use the console without coaching: distinguish planned versus reserved funds, explain a rejected cart, locate a receipt, and identify simulation versus PayPal sandbox. Record completion times, misunderstood labels and improvement suggestions. No independent usability results have been collected.
