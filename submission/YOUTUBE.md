# Published video

The walkthrough is uploaded at [AgentGate Walkthrough (PayPal Hackathon Submission)](https://www.youtube.com/watch?v=1ey3pn47ujk). YouTube currently reports it as Unlisted and 169 seconds long. The entry form accepts Public or Unlisted, but the official rules require the video to be publicly visible; set it to Public before submitting to remove ambiguity.

The final release video is 169 seconds, with larger interface text, a visible cursor, click highlights and action-timed zooms. Captions and the thumbnail are available in the [v1.1.0 GitHub release](https://github.com/Abhyuday-06/PayPal-Hackathon/releases/tag/v1.1.0).

## Description

AgentGate is a working payment-control prototype for developers building purchasing agents. The walkthrough shows two planner roles coordinating a recording-equipment purchase under a shared owner budget. The current console also supports goal-based planning across a small, owner-authorized sample catalogue. The gateway checks authoritative catalogue prices, returns feedback for replanning, reserves exact carts atomically after owner approval, and verifies completed PayPal sandbox captures independently through the provider API.

Source and interactive judge setup:
https://github.com/Abhyuday-06/PayPal-Hackathon

MIT licensed. Python/FastAPI, Next.js, PostgreSQL/SQLite, local Ollama models and the APIMatic-generated PayPal Server SDK.

Video: actual app recordings with loading/setup removed, edited across matching live planning demonstrations and the completed checkout evidence. The payment segment shows fresh read-only verification of the existing $80 and $20 captures; it does not initiate additional payments. Narration is AI-generated. All payments use PayPal sandbox test money. The failure lab and credential-free judge workspace are explicitly simulated; recorded model output is labelled. The small synthetic evaluations do not establish production security or universal attack resistance.

The working catalogue is a small owned demo storefront. The project does not claim production autonomous-payment authorization, AP2 compliance or independent customer adoption.

## Submission note

Paste the YouTube URL above into Devpost's demonstration-video field. The GitHub MP4 is a backup/download and does not replace the YouTube link. The Devpost form itself still needs to be submitted by the project owner.
