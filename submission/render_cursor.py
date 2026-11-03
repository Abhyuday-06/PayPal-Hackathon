"""Edit real UI footage with pointer-led, click-timed zooms and reviewed narration."""
import argparse
import html
import json
from pathlib import Path
import re
import subprocess
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from render_video import duration, stamp

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'submission/render-v2'


def camera(events, length, raw_length):
    """Smooth independent zoom-in/hold/zoom-out pulses; never a whole-scene pan."""
    focuses=[e for e in events if e.get('type')!='click']
    pulses=[]
    for i,event in enumerate(focuses):
        start=max(0,event['time']*length/raw_length-.15)
        next_start=focuses[i+1]['time']*length/raw_length-.3 if i+1<len(focuses) else length-.2
        end=min(start+event['duration']*length/raw_length,next_start,length-.2)
        if end-start<1.1:continue
        a=start*30;b=end*30;r=min(.65,(end-start)/3)*30
        weight=f"if(between(on,{a:.3f},{b:.3f}),if(lt(on,{a+r:.3f}),(1-cos(PI*(on-{a:.3f})/{r:.3f}))/2,if(gt(on,{b-r:.3f}),(1-cos(PI*({b:.3f}-on)/{r:.3f}))/2,1)),0)"
        pulses.append((event,weight))
    zoom='1'+''.join(f"+{e['zoom']-1:.4f}*({w})" for e,w in pulses)
    cx='.5'+''.join(f"+{e['x']/1440-.5:.5f}*({w})" for e,w in pulses)
    cy='.5'+''.join(f"+{e['y']/720-.5:.5f}*({w})" for e,w in pulses)
    return f"zoompan=z='{zoom}':x='max(0,min(iw-iw/zoom,iw*({cx})-iw/(2*zoom)))':y='max(0,min(ih-ih/zoom,ih*({cy})-ih/(2*zoom)))':d=1:s=1800x900:fps=30"


def captions(scene,audio,length):
    words=[json.loads(line) for line in audio.with_suffix('.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    words=[w for w in words if w['type']=='WordBoundary']
    original=scene['narration'].split();cursor=0
    normalize=lambda s:re.sub('[^a-z0-9]','',html.unescape(s).lower())
    for w in words:
        for j in range(cursor,min(cursor+3,len(original))):
            if normalize(w['text'])==normalize(original[j]):w['text']=original[j];cursor=j+1;break
    cues=[];batch=[]
    for w in words:
        batch.append(w)
        if len(batch)>=9 or sum(len(x['text'])+1 for x in batch)>60:
            cues.append((batch[0]['offset']/1e7+.15,min(length,(batch[-1]['offset']+batch[-1]['duration'])/1e7+.3),' '.join(html.unescape(x['text']) for x in batch)));batch=[]
    if batch:cues.append((batch[0]['offset']/1e7+.15,min(length,(batch[-1]['offset']+batch[-1]['duration'])/1e7+.25),' '.join(html.unescape(x['text']) for x in batch)))
    return [(a,min(b,cues[i+1][0]-.02) if i+1<len(cues) else b,t) for i,(a,b,t) in enumerate(cues)]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reuse',action='store_true');args=parser.parse_args()
    story=json.loads((ROOT/'submission/storyboard-v2.json').read_text(encoding='utf-8'))
    shots=json.loads((FOLDER/'shots.json').read_text(encoding='utf-8'))
    fonts=FOLDER/'fonts';fonts.mkdir(exist_ok=True)
    # Static instances keep FFmpeg and libass from selecting a variable font's thin face.
    variable=fonts/'PublicSans.ttf'
    if variable.exists():variable.unlink()
    for name,weight in [('Regular',400),('Semibold',600)]:
        font=TTFont(ROOT/'frontend/public/fonts/PublicSans.ttf')
        instantiateVariableFont(font,{'wght':weight},inplace=True,updateFontNames=True).save(fonts/(name+'.ttf'))
    timeline=[];all_cues=[];offset=0
    for i,scene in enumerate(story['scenes']):
        sid=scene['id'];audio=FOLDER/'audio-final'/(sid+'.mp3');length=duration(audio)+.7
        cues=captions(scene,audio,length);all_cues.extend((a+offset,b+offset,t) for a,b,t in cues)
        ass=FOLDER/(sid+'.ass')
        header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Public Sans,34,&H00FFFFFF,&H00FFFFFF,&H00333D12,&H00333D12,0,0,0,0,100,100,0,0,1,0,0,2,110,110,30,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
        ass.write_text(header+'\n'.join(f'Dialogue: 0,{stamp(a,True)},{stamp(b,True)},Default,,0,0,0,,{text}' for a,b,text in cues),encoding='utf-8')
        chapter=FOLDER/(sid+'-chapter.txt');chapter.write_text(f"{i+1:02d}   {scene['chapter']}",encoding='utf-8')
        if i in (0,7):
            source=FOLDER/'stills'/('01-problem.png' if i==0 else '08-outro.png')
            inputs=['-loop','1','-framerate','30','-i',str(source)]
            image='[0:v]scale=1920:1080,setsar=1[screen]'
        else:
            shot=shots[scene.get('shot',sid)];raw_length=shot['end']-shot['start']
            assert shot['viewport']=={'width':1440,'height':720},'Record the wide viewport before rendering.'
            inputs=['-ss',str(shot['start']),'-t',str(raw_length),'-i',str(ROOT/shot['path'])]
            image=f"[0:v]setpts={length/raw_length:.9f}*(PTS-STARTPTS),fps=30,scale=2880:1440:flags=lanczos,{camera(shot['events'],length,raw_length)},pad=1920:1080:60:60:color=0xe4ece5,setsar=1[screen]"
        font='submission/render-v2/fonts/Semibold.ttf';chapter_path=chapter.relative_to(ROOT).as_posix();subtitle=ass.relative_to(ROOT).as_posix()
        # Camera remains inside the app area. Captions never cover app content.
        filters=image+f";[screen]drawbox=x=0:y=0:w=1920:h=60:color=0x123d33:t=fill,drawtext=fontfile={font}:textfile='{chapter_path}':fontsize=25:fontcolor=white:x=55:y=14,drawtext=fontfile={font}:text='AgentGate':fontsize=24:fontcolor=0xd1e9dc:x=1735:y=14,drawbox=x=0:y=960:w=1920:h=120:color=0x123d33:t=fill,drawbox=x=0:y=960:w={240*(i+1)}:h=3:color=0xe8a126:t=fill,subtitles=filename='{subtitle}':fontsdir=submission/render-v2/fonts,fade=t=in:st=0:d=0.18,fade=t=out:st={length-.18:.5f}:d=0.18[v];[1:a]adelay=150|150,apad=pad_dur=1,atrim=duration={length},asetpts=PTS-STARTPTS[a]"
        output=FOLDER/(sid+'.mp4')
        if not args.reuse or not output.exists():
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-threads','4','-filter_complex_threads','2']+inputs+['-i',str(audio),'-filter_complex',filters,'-map','[v]','-map','[a]','-t',str(length),'-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)],cwd=ROOT,check=True)
        actual=duration(output);timeline.append({'scene':sid,'start':round(offset,3),'end':round(offset+actual,3),'narration':scene['narration']});offset+=actual;print(f'Rendered {sid}: {actual:.2f}s',flush=True)
    assert offset<180
    (FOLDER/'concat.txt').write_text('\n'.join("file '"+s['id']+".mp4'" for s in story['scenes']),encoding='utf-8')
    final=FOLDER/'AgentGate-Cursor-Walkthrough.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(FOLDER/'concat.txt'),'-c:v','libx264','-preset','veryfast','-crf','17','-r','30','-fps_mode','cfr','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-af','aresample=async=1:first_pts=0,loudnorm=I=-16:TP=-1.5:LRA=8,aresample=48000,asetpts=N/SR/TB','-movflags','+faststart',str(final)],cwd=ROOT,check=True)
    srt='\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{text}' for i,(a,b,text) in enumerate(all_cues))+'\n'
    (FOLDER/'AgentGate-Captions.srt').write_text(srt,encoding='utf-8')
    (FOLDER/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')
    print(json.dumps({'file':str(final),'duration_seconds':duration(final),'size_mb':round(final.stat().st_size/1e6,2)}),flush=True)


if __name__=='__main__':main()
