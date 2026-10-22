"""Regression: an Ollama failure must be discoverable from the five-screen UI.

No UI automation, user audio or Ollama network request is involved.
"""
from pathlib import Path


def test_local_minutes_failure_diagnostic_is_exposed_and_allowlisted():
    root = Path(__file__).resolve().parents[1]
    desktop = (root/"desktop"/"main.py").read_text(encoding="utf-8")
    ui = (root/"ui"/"app.js").read_text(encoding="utf-8")
    job = (root/"engine"/"job.py").read_text(encoding="utf-8")
    name = "MINUTA_NO_GENERADA.txt"
    assert name in job, "The real pipeline must persist its visible error report"
    assert name in desktop, "Qt bridge must advertise and allow opening that report"
    render = ui.split("function renderResults(index){", 1)[1].split("function showResult(",1)[0]
    allowed = render.split("const allowed=new Set(",1)[1].split(");",1)[0]
    assert name in allowed, "JS previously hid the diagnostic returned by the Qt bridge"
    assert "button.textContent=translate(item.label)" in render, "Use textContent for untrusted result labels"
