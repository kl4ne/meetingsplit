"""Optional locally executed Faster-Whisper; never contacts ChatGPT or Gemini."""
from __future__ import annotations
from pathlib import Path
from typing import Callable
from .planning import Clip, assign_text_to_core
from .control import Cancellation


def load_whisper(model_name: str='medium', *, model_cache:Path|None=None, on_status:Callable[[str],None]=lambda _:None):
    try:
        from faster_whisper import WhisperModel
    except ImportError as err:
        raise RuntimeError('Falta faster-whisper. Ejecuta instalar.bat para instalar las dependencias.') from err
    options={}
    if model_cache is not None:
        model_cache=Path(model_cache)
        model_cache.mkdir(parents=True,exist_ok=True)
        options['download_root']=str(model_cache)
    try:
        on_status('Preparando aceleración NVIDIA (CUDA)...')
        return WhisperModel(model_name,device='cuda',compute_type='int8_float16',**options), 'NVIDIA GPU'
    except Exception as exc:
        on_status(f'CUDA no disponible ({str(exc)[:100]}). Usando CPU en modo seguro.')
        return WhisperModel(model_name,device='cpu',compute_type='int8',**options), 'CPU'


def transcribe_clip(model, clip: Clip, path: Path, *, language: str='auto', cancel: Cancellation|None=None) -> list[dict]:
    kwargs={
        'beam_size':5,'vad_filter':False,'word_timestamps':True,
        'condition_on_previous_text':False,'task':'transcribe',
    }
    if language=='auto':
        kwargs.update(language=None,multilingual=True)
    elif language in ('es','en'):
        kwargs['language']=language
    else:
        raise ValueError('Idioma de entrada no válido')
    segments, _=model.transcribe(str(path), **kwargs)
    lines=[]
    for seg in segments:
        if cancel:cancel.check()
        words=getattr(seg,'words',None) or []
        if words:
            chosen=[w for w in words if assign_text_to_core(
                clip.export_start+float(w.start),clip.export_start+float(w.end),
                clip.core_start,clip.core_end)]
            if not chosen: continue
            text=''.join(w.word for w in chosen).strip()
            t0=clip.export_start+float(chosen[0].start)
            t1=clip.export_start+float(chosen[-1].end)
        else:
            t0=clip.export_start+float(seg.start)
            t1=clip.export_start+float(seg.end)
            if not assign_text_to_core(t0,t1,clip.core_start,clip.core_end):continue
            text=seg.text.strip()
        if text:
            lines.append({'start':round(t0,2),'end':round(t1,2),'text':text,
                          'part':clip.number})
    return lines


def hhmmss(seconds: float) -> str:
    n=int(seconds)
    return f'{n//3600:02}:{(n%3600)//60:02}:{n%60:02}'


def format_transcript(rows: list[dict]) -> str:
    return '\n'.join(f'[{hhmmss(x["start"])}] {x["text"]}' for x in rows)+'\n'
