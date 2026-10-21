"""Offline Windows portable-executable readiness report.

Run `MeetingSplit.exe --self-check` or `python run.py --self-check`.
Does NOT load a Whisper model, access a meeting, or contact a network.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import platform
import sys


def run_checks() -> tuple[dict, int]:
    checks: dict[str,dict] = {}
    def record(name: str, ok: bool, detail: str, required: bool = True):
        checks[name] = {'ok': bool(ok), 'detail': str(detail), 'required':required}

    record('platform',os.name == 'nt',f'{platform.system()} {platform.release()} / {platform.machine()}',False)
    try:
        from PySide6.QtCore import qVersion
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWebChannel import QWebChannel
        record('qt_webengine',bool(QWebEngineView and QWebChannel),f'Qt {qVersion()}')
    except Exception as e:
        record('qt_webengine',False,f'{type(e).__name__}: {e}'[:240])
    try:
        from engine.audio import bundled_exe, probe
        import subprocess
        for app in ('ffmpeg','ffprobe'):
            path=bundled_exe(app)
            cmd=[path,'-version']
            flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
            outcome=subprocess.run(cmd,capture_output=True,text=True,timeout=10,**flags)
            record(app,outcome.returncode==0,f'{Path(path).name}: {(outcome.stdout or outcome.stderr).splitlines()[0][:130]}')
    except Exception as e:
        for app in ('ffmpeg','ffprobe'):
            if app not in checks:record(app,False,f'{type(e).__name__}: {e}'[:200])
    try:
        from faster_whisper import WhisperModel
        import ctranslate2
        record('whisper',True,f'Faster-Whisper present; CTranslate2 {ctranslate2.__version__}')
        try:
            from engine.transcription import _gpu_runtime_ready
            ready,reason=_gpu_runtime_ready()
            if not ready:
                record('cuda',False,'CUDA libraries unavailable; CPU fallback enabled: '+reason[:130],False)
            else:
                formats=sorted(ctranslate2.get_supported_compute_types('cuda'))
                record('cuda',bool(formats),'GPU compute types: '+', '.join(formats),False)
        except Exception as e:
            record('cuda',False,'CUDA unavailable; CPU fallback expected: '+str(e)[:120],False)
    except Exception as e:
        record('whisper',False,f'{type(e).__name__}: {e}'[:240])
        record('cuda',False,'Not tested because Faster-Whisper is unavailable',False)
    report={
        'product':'MeetingSplit','version':'0.8.5','offline':True,
        'python':platform.python_version(),
        'packaged':bool(getattr(sys,'frozen',False)),
        'checks':checks,
    }
    return report, 0 if all(row['ok'] for row in checks.values() if row['required']) else 2


def main(output_path: str | None = None):
    report,code=run_checks()
    encoded=json.dumps(report,ensure_ascii=False,indent=2)
    if output_path:
        # Writing a tiny diagnostic requires a caller-selected explicit location.
        Path(output_path).write_text(encoded+'\n',encoding='utf-8')
    else:
        print(encoded)
    return code

if __name__=='__main__':
    raise SystemExit(main())
