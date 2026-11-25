from types import SimpleNamespace
import os
import pytest
from engine import inference_worker as worker
from engine.control import Cancellation, JobCancelled


def test_native_exit_is_reported_without_crashing_parent(tmp_path,monkeypatch):
    proc=SimpleNamespace(poll=lambda:7,returncode=7)
    monkeypatch.setattr(worker.subprocess,'Popen',lambda *a,**k:proc)
    w=worker.InferenceWorker(tmp_path,tmp_path/'cache',Cancellation())
    try:
        with pytest.raises(worker.NativeInferenceError,match='exited'):
            w.load('small')
    finally:
        w.close()
    assert not list(tmp_path.iterdir())


def test_cancel_before_inference_request(tmp_path,monkeypatch):
    proc=SimpleNamespace(poll=lambda:0)
    monkeypatch.setattr(worker.subprocess,'Popen',lambda *a,**k:proc)
    task=Cancellation()
    w=worker.InferenceWorker(tmp_path,tmp_path/'cache',task)
    task.cancel()
    try:
        with pytest.raises(JobCancelled):
            w.load('small')
        assert not (w.root/'request.json').exists()
    finally:
        w.close()


def test_real_worker_ipc_and_cleanup(tmp_path):
    # Real child process and file protocol, no native model or network.
    task=Cancellation()
    w=worker.InferenceWorker(tmp_path,tmp_path/'cache',task)
    try:
        response=w.ping()
        pid=response['pid']
        # Windows virtual environments can launch a second Python process.
        assert type(pid) is int and pid>0 and pid!=os.getpid() and response['protocol']==1
        with pytest.raises(RuntimeError,match='Unknown inference operation'):
            w.exchange({'op':'unknown'},timeout=20)
        assert w.ping()['pid']==pid
    finally:
        w.close()
    assert w.process.poll() is not None
    assert not list(tmp_path.iterdir())


@pytest.mark.skipif(os.name!='nt',reason='Windows process-handle lifecycle test')
def test_real_windows_worker_exits_even_behind_launcher(tmp_path):
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    w=worker.InferenceWorker(tmp_path,tmp_path/'cache',Cancellation())
    handle=None
    try:
        pid=w.ping()['pid']
        handle=kernel.OpenProcess(0x00100000,False,pid)
        assert handle
        assert kernel.WaitForSingleObject(handle,0)==258
        w.close()
        assert kernel.WaitForSingleObject(handle,5000)==0
    finally:
        w.close()
        if handle: kernel.CloseHandle(handle)
