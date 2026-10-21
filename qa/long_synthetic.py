"""One-hour synthetic EN/ES workload through the real production pipeline.

Inputs must be the two Windows TTS fake meeting samples. No personal recording.
"""
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop.storage import validate_local_folder
from engine.audio import bundled_exe
from engine.job import run_job

root=validate_local_folder(Path(sys.argv[1]))
ffmpeg=bundled_exe('ffmpeg')
pair=root/'synthetic-en-es.wav'
subprocess.run([ffmpeg,'-y','-v','error','-i',str(root/'synthetic-meeting-en.wav'),
    '-i',str(root/'synthetic-meeting-es.wav'),'-filter_complex','[0:a][1:a]concat=n=2:v=0:a=1[a]',
    '-map','[a]','-ar','16000','-ac','1',str(pair)],check=True,timeout=60)
source=root/'synthetic-one-hour.wav'
subprocess.run([ffmpeg,'-y','-v','error','-stream_loop','-1','-i',str(pair),
    '-t','3600','-ar','16000','-ac','1',str(source)],check=True,timeout=120)
config={'file':str(source),'output':str(root),'action':'both','format':'mp3',
    'minutes':10,'overlap':20,'model':'medium','input_language':'auto',
    'report':'both','report_language':'both','local_summary':False,'zip_output':True}
start=time.monotonic()
result=run_job(config,lambda message,pct:print(f'{pct}% {message}',flush=True))
manifest=json.loads((result/'manifest.json').read_text(encoding='utf-8'))
assert manifest['status']=='complete' and manifest['device']=='NVIDIA GPU'
assert len(manifest['exports'])==len(manifest['clips'])>=6
assert manifest['transcription_segments']>100
assert (result/'RESULTADOS_COMPLETOS.zip').is_file()
summary={'synthetic_input_seconds':3600,'elapsed_seconds':round(time.monotonic()-start,2),
    'device':manifest['device'],'model':'medium','clips':len(manifest['clips']),
    'segments':manifest['transcription_segments'],'zip':True,'status':manifest['status'],
    'limits':'Repeated synthetic TTS workload; not a natural meeting accuracy benchmark'}
(root/'long-synthetic-qa.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary),flush=True)
