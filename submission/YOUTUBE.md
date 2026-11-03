# YouTube upload

The earlier upload at [AgentGate Walkthrough (PayPal Hackathon Submission)](https://www.youtube.com/watch?v=1ey3pn47ujk) is 169 seconds and Unlisted. The updated video is `submission/render-v2/AgentGate-Cursor-Walkthrough.mp4` (171.7 seconds, 1920×1080, H.264). Upload this revised cut and set it to **Public** before submitting; use its new YouTube URL in Devpost.

The revised walkthrough adds the live multi-category mission to the existing cursor-led recording-mission and PayPal sandbox evidence. Captions, narration, thumbnail, and QA report ship in the [v1.2.0 GitHub release](https://github.com/Abhyuday-06/PayPal-Hackathon/releases/tag/v1.2.0).

## Description

AgentGate is a working payment-control prototype for developers building purchasing agents. In the live catalogue example, Iris proposes a $35 USB call headset for a remote-work goal; Nova receives the remaining $65 planning budget and proposes a $60 webcam. The server validates both against its own catalogue and policy. The walkthrough then shows the guided recording example, owner approval, actual PayPal sandbox captures, and independent provider verification.

Source and interactive judge setup:
https://github.com/Abhyuday-06/PayPal-Hackathon

MIT licensed. Python/FastAPI, Next.js, Google Cloud Vertex AI Gemini 3.8 Flash, local Ollama models, PayPal Orders v2 sandbox, and the APIMatic-generated PayPal Server SDK.

Video: actual app recordings with login and model-loading screens removed. It shows a completed live Vertex AI catalog plan and the separate completed PayPal sandbox recording mission. The payment segment verifies the existing $80 and $20 captures through read-only provider lookups; it does not initiate additional payments. Narration is AI-generated. All payments use PayPal sandbox test money. The hosted judge preview simulates payments. Small synthetic evaluations do not establish production security or universal attack resistance.

The working catalogue is a small owned demo storefront. The project does not claim production autonomous-payment authorization, AP2 compliance or independent customer adoption.

## Submission note

After uploading the revised MP4, paste its new YouTube URL into Devpost's demonstration-video field. The old URL above still points to the earlier cut. The Devpost form itself still needs to be submitted by the project owner.
