"""Package only explicitly reviewed public deliverables, never raw browser recordings."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'submission/render-v2'


def main():
    video=FOLDER/'AgentGate-Cursor-Walkthrough.mp4'
    report=json.loads((FOLDER/'qa-report.json').read_text(encoding='utf-8'))
    assert report['sha256']==hashlib.sha256(video.read_bytes()).hexdigest(),'Run QA on this exact video first.'
    assert report['duration_seconds']<180 and report['decode_errors']==0
    shots=json.loads((FOLDER/'shots.json').read_text(encoding='utf-8'))
    report['cursor_walkthrough']={'clicks':sum(e.get('type')=='click' for shot in shots.values() for e in shot['events']),'recording_viewport':[1440,720],'app_area':[1800,900],'camera':'Event-timed zoom in, hold, zoom out. White pointer and amber click pulses.','new_payments_in_this_recording':0}
    (FOLDER/'QA-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    story=json.loads((ROOT/'submission/storyboard-v2.json').read_text(encoding='utf-8'))
    (FOLDER/'AgentGate-Narration.txt').write_text('\n\n'.join(s['chapter']+'\n'+s['narration'] for s in story['scenes'])+'\n',encoding='utf-8')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vn','-c:a','libmp3lame','-b:a','192k',str(FOLDER/'AgentGate-Narration.mp3')],check=True)
    shutil.copyfile(FOLDER/'stills/thumbnail.png',FOLDER/'AgentGate-Thumbnail.png')
    names=['AgentGate-Cursor-Walkthrough.mp4','AgentGate-Captions.srt','AgentGate-Captions.vtt','AgentGate-Narration.mp3','AgentGate-Narration.txt','AgentGate-Thumbnail.png','QA-report.json']
    package=FOLDER/'upload-package';package.mkdir(exist_ok=True)
    for name in names:shutil.copyfile(FOLDER/name,package/name)
    for name in ['YOUTUBE.md','DEVPOST.md','README.md']:shutil.copyfile(ROOT/'submission'/name,package/name)
    sums=lambda files:'\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name for p in files)+'\n'
    (package/'SHA256SUMS.txt').write_text(sums([package/n for n in names]),encoding='utf-8')
    archive=FOLDER/'AgentGate-Submission-Package.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in names+['YOUTUBE.md','DEVPOST.md','README.md','SHA256SUMS.txt']:z.write(package/name,arcname=name)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and len(z.namelist())==11
    (FOLDER/'SHA256SUMS.txt').write_text(sums([FOLDER/n for n in names]+[archive]),encoding='utf-8')
    print(json.dumps({'video_seconds':report['duration_seconds'],'clicks':report['cursor_walkthrough']['clicks'],'zip_bytes':archive.stat().st_size,'assets':len(names)+2}),flush=True)


if __name__=='__main__':main()
