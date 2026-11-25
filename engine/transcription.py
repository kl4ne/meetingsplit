"""Optional locally executed Faster-Whisper; never contacts ChatGPT or Gemini."""
from __future__ import annotations
from pathlib import Path
import math
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


def load_whisper(model_name: str='medium', *, model_cache:Path|None=None, on_status:Callable[[str],None]=lambda _:None, cancel:Cancellation|None=None, preserve_quality=False, probe_runtime=True):
    if model_cache is not None:
        from desktop.components import activate_gpu
        try:
            activate_gpu(Path(model_cache).parent)
        except (OSError, ValueError) as exc:
            on_status('Optional GPU component verification failed; using CPU: '+str(exc))
            return load_cpu_whisper('small' if not preserve_quality and model_name in ('medium','large-v3') else model_name,
                                    model_cache=model_cache), 'CPU'
    try:
        from faster_whisper import WhisperModel
    except ImportError as err:
        raise RuntimeError('Falta faster-whisper. Ejecuta instalar.bat para instalar las dependencias.') from err
    ready, reason = _gpu_runtime_ready()
    if ready and probe_runtime and sys.platform == 'win32' and model_cache is not None:
        # cuDNN lazily initializes on inference and may abort the native process.
        # Probe in a disposable child so a missing dependency cannot kill the UI.
        from desktop.cuda_probe import probe_cuda
        on_status('Comprobando inferencia CUDA en proceso aislado...')
        report=probe_cuda(model_name,Path(model_cache),cancel=cancel)
        ready=report.get('ok',False)
        reason=report.get('error','CUDA probe failed')
    if ready:
        try:
            on_status('Preparando aceleración NVIDIA (CUDA)...')
            return WhisperModel(model_name, device='cuda', compute_type='int8_float16',
                                **_model_options(model_cache)), 'NVIDIA GPU'
        except Exception as exc:
            if not is_cuda_runtime_error(exc):
                raise
            reason = str(exc)[:130]
    cpu_model = 'small' if not preserve_quality and model_name in ('medium','large-v3') else model_name
    on_status(f'GPU CUDA 12 no disponible ({reason}). CPU: {cpu_model}.')
    return load_cpu_whisper(cpu_model, model_cache=model_cache), 'CPU'


def transcribe_clip(model, clip: Clip, path: Path, *, language: str='auto', cancel: Cancellation|None=None, preserve_quality=False) -> list[dict]:
    kwargs={
        'beam_size':5,'vad_filter':True,'word_timestamps':True,
        'vad_parameters':{'min_silence_duration_ms':600,'speech_pad_ms':250},
        'condition_on_previous_text':False,'task':'transcribe',
    }
    # CPU fallback is slower: make progress practical without increasing RAM.
    if not preserve_quality and getattr(getattr(model, 'model', None), 'device', None) == 'cpu':
        kwargs['beam_size'] = 2
    if language=='auto':
        kwargs.update(language=None,multilingual=True)
    elif language in ('es','en'):
        kwargs['language']=language
    else:
        raise ValueError('Idioma de entrada no válido')
    segments, _=model.transcribe(str(path), **kwargs)
    def bounded_times(start, end):
        start=clip.export_start+float(start)
        end=clip.export_start+float(end)
        if not (math.isfinite(start) and math.isfinite(end)):
            return None
        start=max(clip.export_start,start)
        end=min(clip.export_end,end)
        return (start,end) if start<end else None

    lines=[]
    for seg in segments:
        if cancel:cancel.check()
        words=getattr(seg,'words',None) or []
        if words:
            chosen=[]
            for word in words:
                times=bounded_times(word.start,word.end)
                if times and assign_text_to_core(*times,clip.core_start,clip.core_end):
                    chosen.append((times,word.word))
            if not chosen: continue
            text=''.join(word for _,word in chosen).strip()
            t0=min(times[0] for times,_ in chosen)
            t1=max(times[1] for times,_ in chosen)
        else:
            times=bounded_times(seg.start,seg.end)
            if not times or not assign_text_to_core(*times,clip.core_start,clip.core_end):
                continue
            t0,t1=times
            text=seg.text.strip()
        if text:
            lines.append({'start':round(t0,6),'end':round(t1,6),'text':text,
                          'part':clip.number})
    return lines


def hhmmss(seconds: float) -> str:
    n=int(seconds)
    return f'{n//3600:02}:{(n%3600)//60:02}:{n%60:02}'


def format_transcript(rows: list[dict]) -> str:
    return '\n'.join(f'[{hhmmss(x["start"])}] {x["text"]}' for x in rows)+'\n'
