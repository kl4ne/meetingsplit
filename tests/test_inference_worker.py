from types import SimpleNamespace
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
