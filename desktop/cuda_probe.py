"""Exercise the lazy Whisper encoder in an isolated, bounded native process."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import wave


def child(model_name, cache, output):
    result={'ok':False,'validation':'synthetic silence inference only'}
    start=time.monotonic()
    try:
        from desktop.components import activate_gpu
        activate_gpu(Path(cache).parent)
        from engine.transcription import _gpu_runtime_ready
        ready,reason=_gpu_runtime_ready()
        if not ready: raise RuntimeError(reason)
        from faster_whisper import WhisperModel
        import ctranslate2
        model=WhisperModel(model_name,device='cuda',compute_type='int8_float16',download_root=cache)
        with tempfile.TemporaryDirectory(dir=cache,prefix='.cuda-probe-') as temp:
            audio=Path(temp)/'silence.wav'
            with wave.open(str(audio),'wb') as stream:
                stream.setparams((1,2,16000,0,'NONE','not compressed'))
                stream.writeframes(b'\0\0'*16000)
            segments,info=model.transcribe(str(audio),language='en',vad_filter=False,beam_size=1)
            list(segments)  # Must consume generator: construction alone is not a test.
        result.update(ok=True,device='cuda',compute_type='int8_float16',model=model_name,
                      ctranslate2=ctranslate2.__version__,seconds=round(time.monotonic()-start,2))
    except Exception as exc:
        result['error']=str(exc)[:500]
    Path(output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return 0 if result['ok'] else 2


def probe_cuda(model_name: str, cache: Path, timeout=300, cancel=None) -> dict:
    cache.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache,prefix='.probe-report-') as temp:
        dest=Path(temp)/'result.json'; log=Path(temp)/'stderr.log'
        command=[sys.executable]
        if not getattr(sys,'frozen',False): command.append(str(Path(__file__).resolve().parents[1]/'run.py'))
        command += ['--cuda-probe',model_name,str(cache),str(dest)]
        with log.open('wb') as stream:
            process=subprocess.Popen(command,stdout=stream,stderr=stream,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+timeout
            try:
                while process.poll() is None:
                    if cancel: cancel.check()
                    if time.monotonic()>deadline: raise TimeoutError('CUDA probe timed out; CPU fallback remains available')
                    time.sleep(.1)
                if dest.is_file(): return json.loads(dest.read_text(encoding='utf-8'))
                return {'ok':False,'error':f'CUDA native process exited ({process.returncode}); CPU fallback enabled'}
            except TimeoutError as exc:
                return {'ok':False,'error':str(exc)}
            finally:
                if process.poll() is None:
                    process.kill();process.wait(timeout=5)
