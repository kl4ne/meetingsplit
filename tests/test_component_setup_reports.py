"""Durable CPU-only optional Ollama receipt regressions; no vendor I/O."""
from __future__ import annotations
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
import pytest
from PySide6.QtWidgets import QApplication
from desktop import component_setup
from engine.control import Cancellation,JobCancelled


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def report(root):
    return json.loads((root/"Componentes"/"component-setup-report.json").read_text(encoding="utf-8"))


def test_legacy_gpu_request_rejected_with_durable_report(tmp_path,monkeypatch,qapp):
    from desktop import components
    def fail(*args):raise AssertionError("NVIDIA installation must not run")
    monkeypatch.setattr(components,"install_gpu",fail)
    w=component_setup.SetupWorker(tmp_path,True,True,Cancellation())
    w.run()
    result=report(tmp_path)
    assert result["status"]=="failed"
    assert result["stage"]=="cuda_disabled"
    assert result["execution_policy"]=="CPU_ONLY"
    assert result["requested"]=={"cuda":True,"ollama":True}
    assert "prohibits" in result["detail"]


def test_ollama_failure_then_retry_succeeds(tmp_path,monkeypatch,qapp):
    from engine import ollama
    calls=[]
    def fake(*args):
        calls.append(1)
        if len(calls)==1:raise RuntimeError("Synthetic Ollama port in use")
    monkeypatch.setattr(ollama,"setup_ollama",fake)
    for status in ("failed","success"):
        w=component_setup.SetupWorker(tmp_path,False,True,Cancellation())
        w.run()
        result=report(tmp_path)
        assert result["status"]==status
        assert result["execution_policy"]=="CPU_ONLY"
        if status=="failed":
            assert result["stage"]=="ollama_download_and_test"
            assert "Synthetic Ollama" in result["detail"]
        else:
            assert result["ollama_validation_ok"] is True
    assert len(calls)==2


def test_cancelled_optional_cpu_ollama_persists_status(tmp_path,monkeypatch,qapp):
    from engine import ollama
    def cancel(*args):raise JobCancelled("synthetic cancellation")
    monkeypatch.setattr(ollama,"setup_ollama",cancel)
    w=component_setup.SetupWorker(tmp_path,False,True,Cancellation())
    w.run()
    r=report(tmp_path)
    assert r["status"]=="cancelled"
    assert r["release_allowed"] is False


def test_dialog_offers_durable_report_and_no_nvidia_checkbox(tmp_path,qapp):
    d=component_setup.ComponentDialog(str(tmp_path),"es")
    assert hasattr(d,"open_report")
    assert "informe" in d.open_report_button.text().lower()
    assert not hasattr(d,"gpu")
    d.close_or_cancel()
