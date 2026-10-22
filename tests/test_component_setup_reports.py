"""Persistent optional-components status must survive real Qt worker failure/retry.

Synthetic vendor stubs only; no download, installer, GPU, Ollama or user data.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
import pytest

from desktop import component_setup
from engine.control import Cancellation, JobCancelled


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def report(root):
    return json.loads((root/"Componentes"/"component-setup-report.json").read_text(encoding="utf-8"))


def test_cuda_download_failure_has_durable_stage_and_does_not_start_ollama(tmp_path,monkeypatch,app):
    from desktop import components
    from engine import ollama
    attempted=[]
    def gpu(*args):
        attempted.append("cuda")
        raise RuntimeError("Synthetic vendor verification error")
    monkeypatch.setattr(components, "install_gpu",gpu)
    monkeypatch.setattr(ollama,"setup_ollama",lambda *args: attempted.append("ollama"))
    worker=component_setup.SetupWorker(tmp_path,True,True,Cancellation())
    messages=[]
    worker.completed.connect(messages.append)
    worker.run()
    state=report(tmp_path)
    assert state["status"]=="failed"
    assert state["stage"]=="cuda_download"
    assert "Synthetic vendor verification error" in state["detail"]
    assert state["requested"]=={"cuda":True,"ollama":True}
    assert state["release_allowed"] is False
    assert attempted == ["cuda"]
    assert "component-setup-report.json" in messages[0]


def test_cuda_inference_failure_persists_per_stage_and_cuda_report(tmp_path,monkeypatch,app):
    from desktop import components,cuda_probe
    monkeypatch.setattr(components, "install_gpu",lambda *args: None)
    monkeypatch.setattr(cuda_probe, "probe_cuda",lambda *args,**kwargs: {"ok":False,"error":"GPU not detected"})
    worker=component_setup.SetupWorker(tmp_path,True,False,Cancellation())
    worker.run()
    assert report(tmp_path)["stage"]=="cuda_inference"
    assert report(tmp_path)["status"]=="failed"
    assert json.loads((tmp_path/"Componentes"/"cuda-validation.json").read_text())["ok"] is False


def test_ollama_failure_report_durable_then_retry_succeeds(tmp_path,monkeypatch,app):
    from engine import ollama
    calls=[]
    def mock(*args):
        calls.append(1)
        if len(calls)==1: raise RuntimeError("Synthetic Ollama port occupied")
    monkeypatch.setattr(ollama, "setup_ollama",mock)
    for status in ("failed","success"):
        worker=component_setup.SetupWorker(tmp_path,False,True,Cancellation())
        worker.run()
        state=report(tmp_path)
        assert state["status"]==status
        if status=="failed": assert state["stage"]=="ollama_download_and_test"
        else: assert state["ollama_validation_ok"] is True
    assert len(calls)==2


def test_cancellation_writes_explicit_cancelled_result(tmp_path,monkeypatch,app):
    from desktop import components
    def cancelled(*args): raise JobCancelled("Synthetic cancellation")
    monkeypatch.setattr(components,"install_gpu",cancelled)
    worker=component_setup.SetupWorker(tmp_path,True,False,Cancellation())
    worker.run()
    state=report(tmp_path)
    assert state["status"]=="cancelled"
    assert state["release_allowed"] is False


def test_dialog_exposes_open_report_button(tmp_path,monkeypatch,app):
    dialog=component_setup.ComponentDialog(str(tmp_path),"es")
    assert "informe" in dialog.open_report_button.text().lower()
    assert hasattr(dialog,"open_report")
    dialog.close_or_cancel()
