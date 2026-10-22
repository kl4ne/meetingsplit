"""Optional locally executed Faster-Whisper; never contacts ChatGPT or Gemini."""
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


def load_whisper(model_name: str='medium', *, model_cache:Path|None=None, on_status:Callable[[str],None]=lambda _:None, cancel:Cancellation|None=None, on_fallback:Callable[[str],None]|None=None):
    if model_cache is not None:
        from desktop.components import activate_gpu
        activate_gpu(Path(model_cache).parent)
    try:
        from faster_whisper import WhisperModel
    except ImportError as err:
        raise RuntimeError('Falta faster-whisper. Ejecuta instalar.bat para instalar las dependencias.') from err
    ready, reason = _gpu_runtime_ready()
    if ready and sys.platform == 'win32' and model_cache is not None:
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
    # Expose the initial GPU-to-CPU cause to the caller for persisted job evidence.
    # Old consumers stay compatible and no private data is sent to a server.
    if on_fallback is not None:
        on_fallback(str(reason)[:300])
    on_status(f'GPU CUDA 12 no disponible ({reason}). Se utilizará CPU con modelo small (más rápido, precisión posiblemente menor).')
    cpu_model = 'small' if model_name in ('medium','large-v3') else model_name
    return load_cpu_whisper(cpu_model, model_cache=model_cache), 'CPU'


def transcribe_clip(model, clip: Clip, path: Path, *, language: str='auto', cancel: Cancellation|None=None) -> list[dict]:
    kwargs={
        'beam_size':5,'vad_filter':False,'word_timestamps':True,
        'condition_on_previous_text':False,'task':'transcribe',
    }
    # CPU fallback is slower: make progress practical without increasing RAM.
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
