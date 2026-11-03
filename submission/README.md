# AgentGate video production source

The v1.1.0 release contains the revised cursor walkthrough: larger Public Sans typography, a forest/teal interface, visible pointer movement, click pulses, and zoom-in/hold/zoom-out moves that follow the actions. It includes the final 1080p H.264/AAC MP4, English SRT/VTT captions, a PNG thumbnail, narration transcript and QA report. The public YouTube upload is a separate publication step; use [YOUTUBE.md](YOUTUBE.md) for title, description and upload settings, and [DEVPOST.md](DEVPOST.md) for the submission copy.

## Provenance

- All application footage is captured from the actual working app. No network responses or payment outcomes are mocked for the PayPal segment.
- The planning and owner approval shots use actual $80 + $20 model carts in a fresh filming budget. The replanning trace and payment evidence come from the matching, completed submission mission. This is an edited walkthrough across real runs, not a claim that every shot is one uninterrupted browser session.
- The existing confirmed PayPal captures are `1WS730284T000071P` ($80) and `90F18819DJ870472M` ($20). Both were independently verified through the provider SDK; the completed mission had $100 spent and $0 reserved. The revised payment footage performs fresh read-only verification of those existing captures, without initiating new orders or payments. No buyer login, email, password, app secret or owner access key appears in the final footage.
- The opening budget-conflict diagram is labelled illustrative. The failure lab and credential-free judge workspace are simulated. Recorded model evidence is labelled, and failed model tasks remain in the raw evaluation.
- Narration uses the synthetic Microsoft `en-US-GuyNeural` voice through edge-tts. Only the public narration text is sent for synthesis. No copyrighted music is included. Brand diagrams are original HTML/CSS/SVG; application recordings show the actual interface.
- Captions use the TTS service's word timestamps, with reviewed-script punctuation. Camera zooms, cuts and pauses are editorial. Loading/setup footage is removed.

## Reproduce the media

Install FFmpeg/ffprobe, Chrome, Python and Node.js. The app must already run locally, with private owner credentials in `backend/.env` for capture. Real sandbox captures require separate buyer approval; the capture script does not bypass it. The revised editor uses the bundled, openly licensed Public Sans font.

```text
python -m venv tmp/media-venv
tmp/media-venv/Scripts/python -m pip install -r submission/requirements-media.txt
npm --prefix submission install
node submission/create_cards.cjs --cursor
node submission/capture_cursor.cjs
tmp/media-venv/Scripts/python submission/generate_voice.py --cursor
tmp/media-venv/Scripts/python submission/render_cursor.py
tmp/media-venv/Scripts/python submission/qa_video.py --cursor --transcribe
tmp/media-venv/Scripts/python submission/package_release.py
```

`capture_cursor.cjs` uses the private, ignored `tmp/submission-mission.json` to identify an already captured checkout; prepare this from a real owner-reviewed mission. It records new planning/approval actions and read-only provider verification. The pointer overlay is a recording annotation and is not shipped in the product. Capturing footage is an operator action, not a generic one-click fresh-clone test. Use `scripts/start_demo.py` for judging without credentials.

Generated browser videos, temporary font copies, speech-model cache, renders and private capture configuration are ignored by Git. The video release contains only the reviewed public deliverables. The source includes storyboard, narration, capture, rendering and QA scripts.

The original production scripts and storyboard remain for the v1.0.0 edition. Revised artifacts are written to ignored `submission/render-v2/`; the new narration is in `storyboard-v2.json`. Filming run identity is held only in ignored `tmp/cursor-filming.json`. Remove that private marker and the corresponding shot metadata to prepare an entirely new recording, after releasing any filming reservations.
