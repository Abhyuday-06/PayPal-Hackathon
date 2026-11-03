"""Generate scene narration; no product credentials are read or sent."""
import asyncio
import argparse
import json
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parent


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--cursor",action="store_true",help="Generate the revised cursor walkthrough narration.")
    args=parser.parse_args()
    story = json.loads((ROOT / ("storyboard-v2.json" if args.cursor else "storyboard.json")).read_text(encoding="utf-8"))
    folder = ROOT / ("render-v2/audio-final" if args.cursor else "render/audio-final")
    folder.mkdir(parents=True, exist_ok=True)
    for scene in story["scenes"]:
        target = folder / (scene["id"] + ".mp3")
        if target.exists() and target.stat().st_size > 1000:
            continue
        for attempt in range(3):
            try:
                await edge_tts.Communicate(scene["narration"], story["voice"], rate=story["rate"], boundary="WordBoundary").save(str(target), str(target.with_suffix(".jsonl")))
                print(scene["id"], flush=True)
                break
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
