# AgentGate video production source

The release contains the final 1080p H.264/AAC MP4, English SRT/VTT captions, a PNG thumbnail, narration transcript and QA report. The public YouTube upload is a separate publication step; use [YOUTUBE.md](YOUTUBE.md) for title, description and upload settings, and [DEVPOST.md](DEVPOST.md) for the submission copy.

## Provenance

- All application footage is captured from the actual working app. No network responses or payment outcomes are mocked for the PayPal segment.
- The planning/replanning and owner approval shots use matching actual $80 + $20 model carts in a fresh filming budget. The payment shots use the equivalent buyer-approved submission mission. This is an edited walkthrough across real runs, not a claim that every shot is one uninterrupted browser session.
- The actual fresh PayPal captures are `1WS730284T000071P` ($80) and `90F18819DJ870472M` ($20). Both were independently verified through the provider SDK; the completed mission had $100 spent and $0 reserved. No buyer login, email, password, app secret or owner access key appears in the final footage.
- The opening budget-conflict diagram is labelled illustrative. The failure lab and credential-free judge workspace are simulated. Recorded model evidence is labelled, and failed model tasks remain in the raw evaluation.
- Narration uses the synthetic Microsoft `en-US-GuyNeural` voice through edge-tts. Only the public narration text is sent for synthesis. No copyrighted music is included. Brand diagrams are original HTML/CSS/SVG; application recordings show the actual interface.
- Captions use the TTS service's word timestamps, with reviewed-script punctuation. Camera zooms, cuts and pauses are editorial. Loading/setup footage is removed.

## Reproduce the media

Install FFmpeg/ffprobe, Chrome, Python and Node.js. The app must already run locally, with private owner credentials in `backend/.env` for capture. Real sandbox captures require separate buyer approval; the capture script does not bypass it. The editor also requires a local Segoe UI font on Windows (replace the font paths for other systems).

```text
python -m venv tmp/media-venv
tmp/media-venv/Scripts/python -m pip install -r submission/requirements-media.txt
npm --prefix submission install
node submission/create_cards.cjs
node submission/capture_walkthrough.cjs
tmp/media-venv/Scripts/python submission/generate_voice.py
tmp/media-venv/Scripts/python submission/render_video.py
tmp/media-venv/Scripts/python submission/qa_video.py --transcribe
```

`capture_walkthrough.cjs` uses the private, ignored `tmp/submission-mission.json` to identify a buyer-approved checkout; prepare this from a real owner-reviewed mission. Capture is an operator action, not a generic one-click fresh-clone test. Use `scripts/start_demo.py` for judging without credentials.

Generated browser videos, temporary font copies, speech-model cache, renders and private capture configuration are ignored by Git. The video release contains only the reviewed public deliverables. The source includes storyboard, narration, capture, rendering and QA scripts.
