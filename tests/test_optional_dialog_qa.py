"""Windows Qt dialog regression: only optional Ollama CPU is visible.

Real widgets/threads, fake Ollama I/O. Never downloads any runtime or GPU data.
"""
from __future__ import annotations
import os
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
import pytest
from PySide6.QtWidgets import QApplication,QDialog
from desktop import component_setup


@pytest.fixture(scope="module")
def qapp():
    app=QApplication.instance() or QApplication([])
    yield app


def _dialog(tmp_path,monkeypatch,language="en"):
    monkeypatch.setattr(component_setup,"validate_local_folder",lambda path:Path(path))
    import shutil
    monkeypatch.setattr(shutil,"disk_usage",lambda _root:SimpleNamespace(free=60*1024**3))
    dialog=component_setup.ComponentDialog(str(tmp_path),language)
    assert dialog.notices_present
    return dialog


def _pump(qapp,predicate,timeout=8):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        qapp.processEvents()
        if predicate():return
        time.sleep(.02)
    raise AssertionError("Qt CPU-only Ollama worker did not terminate")


@pytest.mark.parametrize("lang",["en","es"])
def test_only_ollama_cpu_requires_consent(qapp,tmp_path,monkeypatch,lang):
    d=_dialog(tmp_path,monkeypatch,lang)
    assert not hasattr(d,"gpu"),"NVIDIA checkbox must not exist"
    assert not d.ollama.isChecked() and not d.terms.isChecked()
    d.start()
    assert d.thread is None
    d.ollama.setChecked(True)
    d.start()
    assert d.thread is None
    d.close_or_cancel()
    assert d.result()==QDialog.DialogCode.Accepted


def test_disk_shortage_prevents_optional_ollama(qapp,tmp_path,monkeypatch):
    d=_dialog(tmp_path,monkeypatch)
    import shutil
    monkeypatch.setattr(shutil,"disk_usage",lambda _root:SimpleNamespace(free=1))
    d.ollama.setChecked(True)
    d.terms.setChecked(True)
    d.start()
    assert d.thread is None and d.prepare.isEnabled()
    assert "12 GiB" in d.status.text()
    d.close_or_cancel()


def test_real_qthread_cancel_and_retry_ollama_without_cuda(qapp,tmp_path,monkeypatch):
    d=_dialog(tmp_path,monkeypatch)
    from engine import ollama
    from desktop import components
    count=[]
    def forbidden_gpu(*args,**kw):raise AssertionError("CUDA called in CPU-only mode")
    monkeypatch.setattr(components,"install_gpu",forbidden_gpu)
    def fake_ollama(root,progress,cancel):
        count.append("ollama")
        if len(count)==1:
            stop=time.monotonic()+4
            while time.monotonic()<stop:
                cancel.check()
                time.sleep(.01)
        else:progress("Synthetic CPU Ollama complete")
    monkeypatch.setattr(ollama,"setup_ollama",fake_ollama)
    d.ollama.setChecked(True)
    d.terms.setChecked(True)
    d.start()
    assert d.thread is not None and not d.prepare.isEnabled()
    d.close_or_cancel()
    assert d.control.event.is_set()
    _pump(qapp,lambda:d.thread is None)
    assert "Cancelled." in d.status.text()
    assert d.prepare.isEnabled()
    d.start()
    _pump(qapp,lambda:d.thread is None)
    assert len(count)==2
    assert "Ollama CPU prepared" in d.status.text()
    assert (tmp_path/"Componentes"/"component-setup-report.json").is_file()
    d.close_or_cancel()
