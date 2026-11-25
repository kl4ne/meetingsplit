"""One persistent Whisper process per job, with bounded file-based IPC.

File IPC works in console-free PyInstaller builds. No recording text goes over
the network. The parent owns the temporary directory and the worker lifecycle.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import threading

from .planning import Clip
from .control import Cancellation, JobCancelled


class NativeInferenceError(RuntimeError):
    pass


def _atomic(path, data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    temp.replace(path)


def _watch_owner(root: Path, owner_pid: int):
    """Watch the actual application PID, not the Windows venv launcher PID."""
    handle=None
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
        kernel.WaitForSingleObject.restype=wintypes.DWORD
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x00100000,False,owner_pid)  # SYNCHRONIZE
        if not handle:
            os._exit(3)
    try:
        while True:
            if (root/'stop').exists():
                os._exit(0)
            if handle is not None:
                status=kernel.WaitForSingleObject(handle,100)
                if status!=258:  # signaled or invalid handle
                    os._exit(0 if status==0 else 3)
            else:
                # Non-Windows source launch is direct; reparenting means the
                # owner is gone. Do not rely on a reusable PID alone.
                if os.getppid()!=owner_pid:
                    os._exit(0)
                time.sleep(.1)
    finally:
        if handle is not None:
            kernel.CloseHandle(handle)


def child(directory, owner_pid):
    root=Path(directory)
    threading.Thread(target=_watch_owner,args=(root,int(owner_pid)),daemon=True).start()
    from .transcription import load_whisper,load_cpu_whisper,transcribe_clip
    model=None
    while True:
        request=root/'request.json'
        if not request.is_file():
            time.sleep(.1)
            continue
        command=json.loads(request.read_text(encoding='utf-8'))
        request.unlink()
        try:
            if command['op']=='ping':
                result={'pid':os.getpid(),'protocol':1}
            elif command['op']=='load':
                cache=Path(command['cache'])
                name=command['model']
                if command['cpu']:
                    model=load_cpu_whisper(name,model_cache=cache)
                    device='CPU'
                else:
                    model,device=load_whisper(name,model_cache=cache,
                        preserve_quality=command['preserve_quality'],probe_runtime=False)
                result={'device':device}
            elif command['op']=='clip':
                if model is None: raise RuntimeError('Whisper not loaded')
                result={'rows':transcribe_clip(model,Clip(**command['clip']),
                    Path(command['path']),language=command['language'],
                    preserve_quality=command['preserve_quality'])}
            else:
                raise ValueError('Unknown inference operation')
            _atomic(root/'response.json',{'ok':True,**result})
        except Exception as exc:
            _atomic(root/'response.json',{'ok':False,'error':str(exc)[:800]})


class InferenceWorker:
    def __init__(self, folder: Path, cache: Path, cancel: Cancellation, preserve_quality=False):
        self.temp=tempfile.TemporaryDirectory(prefix='.inference-',dir=folder)
        self.root=Path(self.temp.name)
        self.cancel=cancel
        self.cache=cache
        self.preserve_quality=preserve_quality
        self.process=None
        command=[sys.executable]
        if not getattr(sys,'frozen',False):
            command.append(str(Path(__file__).resolve().parents[1]/'run.py'))
        command+=['--inference-worker',str(self.root),str(os.getpid())]
        try:
            self.process=subprocess.Popen(command,stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except BaseException:
            self.temp.cleanup()
            raise

    def exchange(self, command, timeout=3600):
        self.cancel.check()
        _atomic(self.root/'request.json',command)
        result=self.root/'response.json'
        deadline=time.monotonic()+timeout
        while True:
            self.cancel.check()
            if result.is_file():
                data=json.loads(result.read_text(encoding='utf-8'))
                result.unlink()
                if not data.get('ok'): raise RuntimeError(data.get('error','Inference failed'))
                return data
            if self.process.poll() is not None:
                raise NativeInferenceError(f'Native inference worker exited ({self.process.returncode})')
            if time.monotonic()>deadline:
                raise NativeInferenceError('Native inference worker timed out')
            time.sleep(.1)

    def ping(self):
        return self.exchange({'op':'ping'},timeout=20)

    def load(self, model, cpu=False):
        return self.exchange({'op':'load','cache':str(self.cache),'model':model,
            'cpu':cpu,'preserve_quality':self.preserve_quality})['device']

    def transcribe(self, clip, path, language):
        return self.exchange({'op':'clip','clip':clip.to_dict(),'path':str(path),
            'language':language,'preserve_quality':self.preserve_quality})['rows']

    def close(self):
        try:
            if self.process is not None and self.process.poll() is None:
                # The worker may be behind a Python launcher; request exit
                # through the private IPC directory, not by killing only the
                # launcher's PID. The watchdog also handles parent death.
                (self.root/'stop').touch()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    if os.name=='nt':
                        taskkill=Path(os.environ.get('WINDIR',r'C:\Windows'))/'System32'/'taskkill.exe'
                        try:
                            subprocess.run([str(taskkill),'/PID',str(self.process.pid),'/T','/F'],
                                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                        except (OSError,subprocess.TimeoutExpired):
                            pass
                    if self.process.poll() is None:
                        self.process.kill()
                    self.process.wait(timeout=5)
        finally:
            self.temp.cleanup()
