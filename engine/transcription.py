"""CPU-only Faster-Whisper; no CUDA initialization or remote transcription."""
from __future__ import annotations
from pathlib import Path
import os
import ctypes
import sys
from typing import Callable
from .planning import Clip, assign_text_to_core
from .control import Cancellation


def _gpu_runtime_ready() -> tuple[bool, str]:
    """Avoid broken Windows GPU paths before launching CTranslate2 inference.

    CTranslate2 can construct the GPU model before its lazy generator loads
    cuBLAS/cuDNN. Checking the libraries first prevents missing-DLL failures
    that sometimes terminate the process instead of raising Python errors.
    """
    if sys.platform != 'win32':
        return True, ''
    for dll in ('nvcuda.dll', 'cublasLt64_12.dll', 'cublas64_12.dll',
                'cudnn64_9.dll', 'cudnn_ops64_9.dll', 'cudnn_cnn64_9.dll',
                'cudnn_adv64_9.dll', 'cudnn_graph64_9.dll',
                'cudnn_heuristic64_9.dll', 'cudnn_engines_precompiled64_9.dll',
                'cudnn_engines_runtime_compiled64_9.dll'):
        try:
            # System32 and explicitly registered vendor folders; exclude CWD.
            ctypes.WinDLL(dll, winmode=0x1000)
        except (OSError, AttributeError) as exc:
            return False, f'{dll}: {str(exc)[:100]}'
    return True, ''


def is_cuda_runtime_error(exc: Exception) -> bool:
    """Only fall back for accelerator-related errors; surface other failures."""
    message = str(exc).lower()
    return any(token in message for token in (
        'cuda', 'cublas', 'cudnn', 'cudart', 'cufft',
        'out of memory', 'no kernel image', 'compute capability',
        'failed to load library', 'cannot load library',
    ))


def _model_options(model_cache: Path | None) -> dict:
    options = {}
    if model_cache is not None:
        model_cache = Path(model_cache)
        model_cache.mkdir(parents=True, exist_ok=True)
        options['download_root'] = str(model_cache)
    return options


def load_cpu_whisper(model_name: str='medium', *, model_cache:Path|None=None):
    from faster_whisper import WhisperModel
    return WhisperModel(model_name, device='cpu', compute_type='int8',
                        cpu_threads=min(8, os.cpu_count() or 4), **_model_options(model_cache))


def load_whisper(model_name: str='small', *, model_cache:Path|None=None,
                 on_status:Callable[[str],None]=lambda _:None,
                 cancel:Cancellation|None=None,
                 on_fallback:Callable[[str],None]|None=None):
    """CPU-only policy: never detect/initialize CUDA, even on an NVIDIA PC.

    Retain the former signature for compatibility with internal call sites.
    Medium/large-v3 requests from older saved UI state use CPU-small, avoiding
    lengthy high-memory CPU inference while preserving the chosen model in
    the job's 'model' and the actual model in 'actual_model'.
    """
    if cancel: cancel.check()
    cpu_model = 'small' if model_name in ('medium','large-v3') else model_name
    on_status('Modo CPU permanente. Preparando Whisper '+cpu_model+' (sin NVIDIA/CUDA).')
    model=load_cpu_whisper(cpu_model,model_cache=model_cache)
    if cancel: cancel.check()
    return model,'CPU'

def transcribe_clip(model, clip: Clip, path: Path, *, language: str='auto', cancel: Cancellation|None=None) -> list[dict]:
    kwargs={
        'beam_size':5,'vad_filter':False,'word_timestamps':True,
        'condition_on_previous_text':False,'task':'transcribe',
    }
    # Native CTranslate2 CPU device: keep decoding bounded on ordinary laptops.
    if getattr(getattr(model, 'model', None), 'device', None) == 'cpu':
        kwargs['beam_size'] = 2
        kwargs['word_timestamps'] = False
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
