"""Explicit development-only ASUS test on the two Windows-generated fake meetings.

No personal audio is accepted. Generate synthetic-meeting-en/es.wav with Windows
SpeechSynthesizer inside a selected internal test folder before running this.
"""
import argparse
import gc
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop.storage import validate_local_folder
from engine.transcription import load_whisper, load_cpu_whisper, transcribe_clip
from engine.audio import probe
from engine.planning import Clip


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--model',choices=('small','medium'),default='small')
    parser.add_argument('--cpu',action='store_true')
    parser.add_argument('--missing-gpu',action='store_true',help='Separate process with no application GPU component folder')
    args=parser.parse_args()
    root=validate_local_folder(args.root)
    if args.missing_gpu:
        snapshots=list((root/'Modelos'/'models--Systran--faster-whisper-small'/'snapshots').glob('*'))
        if not snapshots: raise RuntimeError('Prepare the small model in the isolated test cache first')
        fallback=root/'without-gpu-components';fallback.mkdir(exist_ok=True)
        model,device=load_whisper(str(snapshots[0]),model_cache=fallback/'Modelos',on_status=lambda m:print(m,flush=True))
        if device!='CPU': raise RuntimeError('Missing-GPU test did not enter CPU fallback')
    elif args.cpu:
        model=load_cpu_whisper(args.model,model_cache=root/'Modelos');device='CPU'
    else:
        model,device=load_whisper(args.model,model_cache=root/'Modelos',on_status=lambda m:print(m,flush=True))
        if device!='NVIDIA GPU': raise RuntimeError('GPU acceptance failed: fell back to CPU')
    results={'device':device,'model':args.model,'input':'Windows TTS synthetic meetings only','tests':[]}
    for language in ('en','es'):
        audio=root/f'synthetic-meeting-{language}.wav'
        duration=probe(audio);start=time.monotonic()
        rows=transcribe_clip(model,Clip(1,0,duration,0,duration),audio,language=language)
        if not rows: raise RuntimeError('No speech was transcribed')
        row={'language':language,'audio_seconds':duration,
             'inference_seconds':round(time.monotonic()-start,2),'segments':rows}
        results['tests'].append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    filename=('missing-gpu-cpu' if args.missing_gpu else 'cpu' if args.cpu else 'gpu')+'-speech-'+args.model+'.json'
    (root/filename).write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    model=None;gc.collect()


if __name__=='__main__': main()
