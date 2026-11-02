"""Render actual browser recordings with narration, timed captions, and zooms."""
import json
import argparse
import math
import html
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "submission/render"


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], text=True))


def stamp(seconds, ass=False):
    h=int(seconds//3600);m=int(seconds%3600//60);s=seconds%60
    return f"{h}:{m:02d}:{s:05.2f}" if ass else f"{h:02d}:{m:02d}:{s:06.3f}".replace(".",",")


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--reuse",action="store_true",help="Reuse existing unchanged scene renders.");args=parser.parse_args()
    story=json.loads((ROOT/"submission/storyboard.json").read_text(encoding="utf-8"))
    shots=json.loads((FOLDER/"shots.json").read_text(encoding="utf-8"))
    fonts=FOLDER/"fonts";fonts.mkdir(exist_ok=True)
    for name,file in [("regular","segoeui.ttf"),("semibold","seguisb.ttf")]:
        source=Path("C:/Windows/Fonts")/file
        if source.exists():shutil.copyfile(source,fonts/(name+".ttf"))
    final_cues=[];offset=0;timeline=[]
    for index,scene in enumerate(story["scenes"]):
        sid=scene["id"];audio=FOLDER/"audio-final"/(sid+".mp3");length=duration(audio)+0.7
        metadata=[json.loads(line) for line in audio.with_suffix(".jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        words=[w for w in metadata if w["type"]=="WordBoundary"]
        original_words=scene["narration"].split();cursor=0
        normalized=lambda value:re.sub(r"[^a-z0-9]","",html.unescape(value).lower())
        for word in words:
            for candidate in range(cursor,min(cursor+3,len(original_words))):
                if normalized(word["text"])==normalized(original_words[candidate]):
                    word["text"]=original_words[candidate];cursor=candidate+1;break
        cues=[];batch=[]
        for word in words:
            batch.append(word)
            if len(batch)>=9 or sum(len(w["text"])+1 for w in batch)>60:
                cues.append((batch[0]["offset"]/1e7+0.15,(batch[-1]["offset"]+batch[-1]["duration"])/1e7+0.3," ".join(html.unescape(w["text"]) for w in batch)));batch=[]
        if batch:cues.append((batch[0]["offset"]/1e7+0.15,(batch[-1]["offset"]+batch[-1]["duration"])/1e7+0.25," ".join(html.unescape(w["text"]) for w in batch)))
        srt=FOLDER/(sid+".srt")
        srt.write_text("\n\n".join(f"{i+1}\n{stamp(a)} --> {stamp(min(b,length))}\n{text}" for i,(a,b,text) in enumerate(cues))+"\n",encoding="utf-8")
        ass=srt.with_suffix(".ass")
        header="[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Segoe UI,34,&H00FFFFFF,&H00FFFFFF,&H00462B17,&H00462B17,0,0,0,0,100,100,0,0,3,2,0,2,150,150,25,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        ass.write_text(header+"\n".join(f"Dialogue: 0,{stamp(a,True)},{stamp(min(b,length),True)},Default,,0,0,0,,{text}" for a,b,text in cues),encoding="utf-8")
        final_cues.extend((a+offset,min(b,length)+offset,text) for a,b,text in cues)
        chapter=FOLDER/(sid+"-chapter.txt");chapter.write_text(f"{index+1:02d}  {scene['chapter']}",encoding="utf-8")
        output=FOLDER/(sid+".mp4")
        common=["ffmpeg","-hide_banner","-loglevel","error","-y","-threads","4","-filter_complex_threads","2"]
        audio_index=1
        if index in (0,7):
            source=FOLDER/"stills"/("01-problem.png" if index==0 else "08-outro.png")
            inputs=["-loop","1","-framerate","30","-i",str(source)]
            image=f"[0:v]scale=1920:1080,zoompan=z='1.0+0.035*sin(PI*on/{int(length*30)})':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps=30,setsar=1[screen]"
        else:
            shot=shots[scene.get("shot",sid)];raw=ROOT/shot["path"];raw_len=shot["end"]-shot["start"]
            inputs=["-ss",str(shot["start"]),"-t",str(raw_len),"-i",str(raw)]
            image=f"[0:v]setpts={length/raw_len:.8f}*(PTS-STARTPTS),fps=30,scale=2400:1500,zoompan=z='1.0+0.18*sin(PI*on/{int(length*30)})':x='(iw-iw/zoom)*0.88':y='(ih-ih/zoom)*0.45':d=1:s=1520x950:fps=30,pad=1920:1080:200:65:color=0xf3f6fb,setsar=1[screen]"
        if sid=="04-approval":
            # Hold the actual pre-approval frame while explaining that planning
            # has not reserved funds, then play the real owner approval action.
            shot=shots[scene.get("shot",sid)];raw=ROOT/shot["path"];raw_len=shot["end"]-shot["start"];hold=6.0
            inputs=["-loop","1","-framerate","30","-t",str(hold),"-i",str(FOLDER/"stills/02-mission.png"),"-ss",str(shot["start"]),"-t",str(raw_len),"-i",str(raw)]
            audio_index=2
            image=f"[0:v]trim=duration={hold},setpts=PTS-STARTPTS,fps=30[before];[1:v]setpts={(length-hold)/raw_len:.8f}*(PTS-STARTPTS),fps=30[approval];[before][approval]concat=n=2:v=1:a=0,scale=2400:1500,zoompan=z='1.0+0.18*sin(PI*on/{int(length*30)})':x='(iw-iw/zoom)*0.88':y='(ih-ih/zoom)*0.45':d=1:s=1520x950:fps=30,pad=1920:1080:200:65:color=0xf3f6fb,setsar=1[screen]"
        # Text files avoid shell quoting and keep the narration out of command strings.
        subtitle=ass.relative_to(ROOT).as_posix();chapter_path=chapter.relative_to(ROOT).as_posix()
        style="FontName=Segoe UI,FontSize=25,PrimaryColour=&H00FFFFFF,OutlineColour=&H00462B17,BackColour=&H00462B17,BorderStyle=3,Outline=2,Shadow=0,MarginV=18,MarginL=150,MarginR=150,Alignment=2"
        filters=image+f";[screen]drawbox=x=0:y=0:w=1920:h=58:color=0x172b46:t=fill,drawtext=fontfile=submission/render/fonts/semibold.ttf:textfile='{chapter_path}':fontsize=25:fontcolor=white:x=50:y=13,drawtext=fontfile=submission/render/fonts/regular.ttf:text='AgentGate':fontsize=24:fontcolor=0xbfd4f4:x=1740:y=13,drawbox=x=0:y=963:w=1920:h=117:color=0x172b46@0.96:t=fill,subtitles=filename='{subtitle}':fontsdir=submission/render/fonts,fade=t=in:st=0:d=0.25,fade=t=out:st={length-0.25}:d=0.25[v];[{audio_index}:a]adelay=150|150,apad=pad_dur=1,atrim=duration={length},asetpts=PTS-STARTPTS[a]"
        cmd=common+inputs+["-i",str(audio),"-filter_complex",filters,"-map","[v]","-map","[a]","-t",str(length),"-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart",str(output)]
        if not args.reuse or not output.exists():
            subprocess.run(cmd,cwd=ROOT,check=True)
        timeline.append({"scene":sid,"start":round(offset,3),"end":round(offset+length,3),"narration":scene["narration"]});offset+=duration(output)
        print(f"Rendered {sid}: {length:.2f}s",flush=True)
    assert offset<180,f"Video exceeds limit: {offset}"
    (FOLDER/"concat.txt").write_text("\n".join("file '"+s["id"]+".mp4'" for s in story["scenes"]),encoding="utf-8")
    final=FOLDER/"AgentGate-Hackathon-Demo.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(FOLDER/"concat.txt"),"-c:v","libx264","-preset","veryfast","-crf","18","-r","30","-fps_mode","cfr","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","48000","-af","aresample=async=1:first_pts=0,loudnorm=I=-16:TP=-1.5:LRA=8,aresample=48000,asetpts=N/SR/TB","-movflags","+faststart",str(final)],cwd=ROOT,check=True)
    srt_text="\n\n".join(f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{text}" for i,(a,b,text) in enumerate(final_cues))+"\n"
    (FOLDER/"AgentGate-Captions.srt").write_text(srt_text,encoding="utf-8")
    (FOLDER/"AgentGate-Captions.vtt").write_text("WEBVTT\n\n"+"\n\n".join(f"{stamp(a).replace(chr(44),chr(46))} --> {stamp(b).replace(chr(44),chr(46))}\n{text}" for a,b,text in final_cues)+"\n",encoding="utf-8")
    (FOLDER/"timeline.json").write_text(json.dumps(timeline,indent=2),encoding="utf-8")
    print(json.dumps({"file":str(final),"duration_seconds":duration(final),"size_mb":round(final.stat().st_size/1e6,2)}),flush=True)


if __name__=="__main__":main()
