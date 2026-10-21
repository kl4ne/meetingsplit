"""Windows isolated QA for the REAL optional-components Qt dialog, with fake vendor I/O.

Qt widgets/worker thread are real. No CUDA/Ollama bytes, hardware, services,
registry edits or user audio are required. These do not prove live downloads.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from desktop import component_setup


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _dialog(tmp_path, monkeypatch, language="en"):
    monkeypatch.setattr(component_setup, "validate_local_folder", lambda root: Path(root))
    import shutil
    monkeypatch.setattr(shutil, "disk_usage", lambda _: SimpleNamespace(free=60 * 1024**3))
    dialog = component_setup.ComponentDialog(str(tmp_path), language)
    assert dialog.notices_present, "Actual optional-component license documentation must be packaged"
    return dialog


def _pump(qapp, predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return
        time.sleep(.02)
    raise AssertionError("Qt dialog/worker did not finish within QA deadline")


@pytest.mark.parametrize("lang", ["en", "es"])
def test_opt_in_and_license_consent_precede_any_worker(qapp, tmp_path, monkeypatch, lang):
    dialog = _dialog(tmp_path, monkeypatch, lang)
    assert not dialog.gpu.isChecked()
    assert not dialog.ollama.isChecked()
    assert not dialog.terms.isChecked()
    assert dialog.thread is None
    dialog.start()
    assert dialog.thread is None
    dialog.gpu.setChecked(True)
    dialog.start()
    assert dialog.thread is None
    assert ("Selecciona" if lang == "es" else "Choose") in dialog.status.text()
    dialog.close_or_cancel()
    assert dialog.result() == QDialog.DialogCode.Accepted


@pytest.mark.parametrize("lang", ["en", "es"])
def test_disk_full_blocks_worker_in_actual_dialog(qapp, tmp_path, monkeypatch, lang):
    dialog = _dialog(tmp_path, monkeypatch, lang)
    import shutil
    monkeypatch.setattr(shutil, "disk_usage", lambda _: SimpleNamespace(free=1))
    dialog.ollama.setChecked(True)
    dialog.terms.setChecked(True)
    dialog.start()
    assert dialog.thread is None
    assert "12 GiB" in dialog.status.text()
    assert dialog.prepare.isEnabled()
    dialog.close_or_cancel()


def test_actual_qthread_cancel_then_retry_preserves_dialog(qapp, tmp_path, monkeypatch):
    dialog = _dialog(tmp_path, monkeypatch)
    from desktop import components, cuda_probe
    from engine.control import JobCancelled
    calls = []

    def fake_gpu(root, progress, cancel):
        calls.append("gpu")
        (root / "Componentes").mkdir(exist_ok=True)
        if len(calls) == 1:
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                cancel.check()
                time.sleep(.01)
            raise AssertionError("Cancel did not interrupt vendor operation")
        cancel.check()
        progress("Synthetic GPU prepared; no network called")

    monkeypatch.setattr(components, "install_gpu", fake_gpu)
    monkeypatch.setattr(cuda_probe, "probe_cuda", lambda *a, **kw: {"ok": True, "validation": "QA stub only"})
    dialog.gpu.setChecked(True)
    dialog.terms.setChecked(True)
    dialog.start()
    assert dialog.thread is not None
    assert not dialog.prepare.isEnabled()
    dialog.close_or_cancel()  # cancel request while Qt worker owns the background task
    assert dialog.control.event.is_set()
    _pump(qapp, lambda: dialog.thread is None)
    assert dialog.prepare.isEnabled()
    assert "Cancelled." in dialog.status.text()
    assert calls == ["gpu"]

    # User may reattempt without restarting or deleting their selected root.
    dialog.start()
    _pump(qapp, lambda: dialog.thread is None)
    assert calls == ["gpu", "gpu"]
    assert "Components prepared." in dialog.status.text()
    report = tmp_path / "Componentes" / "cuda-validation.json"
    assert report.is_file()
    assert "QA stub only" in report.read_text(encoding="utf-8")
    dialog.close_or_cancel()
