"""Technical QA plus optional independent speech transcription."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"submission/render"


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--transcribe",action="store_true");args=parser.parse_args()
    video=FOLDER/"AgentGate-Hackathon-Demo.mp4"
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(video)],text=True))
    v=next(s for s in probe["streams"] if s["codec_type"]=="video");a=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    assert (v["width"],v["height"],v["codec_name"])==(1920,1080,"h264")
    assert float(probe["format"]["duration"])<180 and a["codec_name"]=="aac"
    decoded=subprocess.run(["ffmpeg","-v","error","-i",str(video),"-f","null","-"],capture_output=True,text=True)
    assert decoded.returncode==0 and not decoded.stderr.strip(), decoded.stderr
    levels=subprocess.run(["ffmpeg","-hide_banner","-i",str(video),"-af","loudnorm=I=-16:TP=-1.5:LRA=8:print_format=json","-f","null","-"],capture_output=True,text=True)
    block=levels.stderr[levels.stderr.rfind('{'):];loudness=json.JSONDecoder().raw_decode(block)[0]
    assert float(loudness["input_tp"])<=-1 and -18<=float(loudness["input_i"])<=-14
    srt=(FOLDER/"AgentGate-Captions.srt").read_text(encoding="utf-8")
    vtt="WEBVTT\n\n"+"\n".join(line.replace(',','.') if '-->' in line else line for line in srt.splitlines())+"\n"
    (FOLDER/"AgentGate-Captions.vtt").write_text(vtt,encoding="utf-8")
    report={"duration_seconds":float(probe["format"]["duration"]),"video":{"codec":v["codec_name"],"width":v["width"],"height":v["height"],"fps":v["avg_frame_rate"],"pixel_format":v["pix_fmt"]},"audio":{"codec":a["codec_name"],"sample_rate":a["sample_rate"],"integrated_lufs":loudness["input_i"],"true_peak_dbtp":loudness["input_tp"]},"decode_errors":0,"subtitle_cues":srt.count('-->'),"sha256":hashlib.sha256(video.read_bytes()).hexdigest(),"visual_review":"Opening, each chapter, provider evidence and closing sampled from the actual final render."}
    if args.transcribe:
        from faster_whisper import WhisperModel
        model=WhisperModel("tiny.en",device="cpu",compute_type="int8",cpu_threads=4,download_root=str(FOLDER/"asr-model"))
        import numpy as np
        pcm=subprocess.check_output(["ffmpeg","-v","error","-i",str(video),"-ar","16000","-ac","1","-f","f32le","-"])
        segments,info=model.transcribe(np.frombuffer(pcm,dtype=np.float32).copy(),beam_size=5,language="en")
        text=" ".join(s.text.strip() for s in segments)
        (FOLDER/"independent-transcript.txt").write_text(text,encoding="utf-8")
        expected=" ".join(s["narration"] for s in json.loads((ROOT/"submission/storyboard.json").read_text(encoding="utf-8"))["scenes"])
        normal=lambda s:re.findall(r"[a-z0-9]+",s.lower())
        report["independent_asr_similarity"]=round(difflib.SequenceMatcher(None,normal(expected),normal(text),autojunk=False).ratio(),3)
        report["asr_note"]="Small local recognizer; model/product names may differ. Narration and word-timed captions come from the reviewed script."
    (FOLDER/"qa-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":main()
