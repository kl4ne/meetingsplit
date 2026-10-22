"""Explicit internal QA entry point for the frozen app, using synthetic files only.

Never part of normal startup or automatic installer actions. Requires a caller-
selected internal test folder containing the two Windows-generated fake meetings,
prepared optional components and cached models. Does not install components.
"""
from __future__ import annotations
import gc
import json
from pathlib import Path
import time
from desktop.storage import validate_local_folder


def main(root_path, output_path):
    root=validate_local_folder(Path(root_path))
    output=Path(output_path)
    validate_local_folder(output.parent)
    report={'ok':False,'synthetic_only':True,'stages':[]}
    def save():
        temporary=output.with_suffix('.partial')
        temporary.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        temporary.replace(output)
    save()
    try:
        from engine.transcription import load_whisper,transcribe_clip
        from engine.audio import probe
        from engine.planning import Clip
        for language in ('en','es'):
            if not (root/f'synthetic-meeting-{language}.wav').is_file():
                raise ValueError('Required synthetic TTS fixture missing: '+language)
        model,device=load_whisper('medium',model_cache=root/'Modelos')
        if device!='CPU': raise RuntimeError('CPU-only acceptance entered an unexpected accelerator mode')
        for language in ('en','es'):
            audio=root/f'synthetic-meeting-{language}.wav'
            duration=probe(audio);start=time.monotonic()
            rows=transcribe_clip(model,Clip(1,0,duration,0,duration),audio,language=language)
            if not rows: raise RuntimeError('CPU Whisper did not transcribe synthetic speech')
            report['stages'].append({'stage':'cpu-speech','language':language,'device':device,
                'seconds':round(time.monotonic()-start,2),'rows':rows})
            save()
        model=None;gc.collect()
        from engine.ollama import LocalService,MODEL
        from engine.summarize import summarize_local
        source='[00:00:01] Ana will send the draft on Friday.\n[00:00:06] Luis agreed to review it on Monday.'
        with LocalService(root) as service:
            service.ensure_model()
            for language in ('en','es'):
                start=time.monotonic()
                result=summarize_local(source,'minutes',language,MODEL,endpoint=service.endpoint)
                if not all(name in result for name in ('Ana','Luis')):
                    raise RuntimeError('Frozen minutes omitted required names')
                report['stages'].append({'stage':'ollama-minutes','language':language,
                    'seconds':round(time.monotonic()-start,2),'text':result,'factual_review_required':True})
                save()
        report['ok']=True;save();return 0
    except Exception as exc:
        report['error']=str(exc)[:700];save();return 2
