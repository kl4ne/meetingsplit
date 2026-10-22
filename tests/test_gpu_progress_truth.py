"""Verify factual GPU/CPU progress and persisted fallback evidence.

No GPU/FFmpeg/Ollama/network used; mock WAV probing, segment export and model.
"""
from __future__ import annotations
import json
from pathlib import Path

import pytest
from engine import job, transcription


@pytest.fixture
def fake_audio(tmp_path, monkeypatch):
    source = tmp_path / "synthetic.wav"
    source.write_bytes(b"fake WAV payload, never fed to decoder")
    monkeypatch.setattr(job, "validate_local_folder",
                        lambda folder: Path(folder).resolve(strict=True))
    monkeypatch.setattr(job, "probe", lambda src: 12)
    monkeypatch.setattr(job, "detect_silences", lambda src, cancel: [])

    def fake_export(src, output, clip, fmt, cancel):
        output.write_bytes(b"synthetic dummy clip")
        return {"duration": 12}
    monkeypatch.setattr(job, "export_clip", fake_export)
    monkeypatch.setattr(job, "transcribe_clip",
                        lambda model, clip, path, language, cancel:
                        [{"start": .4, "end": 1.2, "text": "Synthetic test", "part": 1}])
    config = {
        "file": str(source), "output": str(tmp_path), "action": "transcribe",
        "format": "mp3", "minutes": 5, "overlap": 20,
        "model": "medium", "input_language": "en", "report": "minutes",
        "report_language": "en", "zip_output": False, "local_summary": False,
    }
    return config


def test_gpu_mode_never_displays_cpu_warning(fake_audio, monkeypatch):
    monkeypatch.setattr(job, "load_whisper",
                        lambda *args, **kwargs: (object(), "NVIDIA GPU"))
    messages = []
    folder = job.run_job(fake_audio, lambda text, percent: messages.append(text))
    result = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert result["status"] == "complete"
    assert result["device"] == "NVIDIA GPU"
    assert any("Aceleración NVIDIA GPU seleccionada" in s for s in messages)
    assert not any("En CPU el primer fragmento" in s for s in messages)
    assert "gpu_fallback" not in result


def test_initial_cuda_fallback_records_actual_reason(fake_audio, monkeypatch):
    def fake_gpu(model_name, *, on_fallback, **kwargs):
        on_fallback("cudnn64_9.dll missing during medium probe")
        return object(), "CPU"
    monkeypatch.setattr(job, "load_whisper", fake_gpu)
    messages = []
    folder = job.run_job(fake_audio, lambda text, percent: messages.append(text))
    result = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert result["status"] == "complete"
    assert result["device"] == "CPU"
    assert result["actual_model"] == "small"
    assert result["gpu_fallback"]["stage"] == "model_initialization_or_probe"
    assert "cudnn64_9.dll" in result["gpu_fallback"]["reason"]
    assert any("En CPU el primer fragmento" in s for s in messages)
    assert not any("Aceleración NVIDIA GPU seleccionada" in s for s in messages)


def test_actual_load_whisper_fallback_callback_is_optional_and_compatible(monkeypatch):
    from types import SimpleNamespace
    import sys
    monkeypatch.setattr(transcription, "_gpu_runtime_ready",
                        lambda: (False, "nvcuda.dll unavailable"))
    class WhisperModel:
        def __init__(self, *args, **kwargs):
            pass
    monkeypatch.setitem(sys.modules,"faster_whisper",
                        SimpleNamespace(WhisperModel=WhisperModel))
    reasons=[]
    _model, device = transcription.load_whisper("medium",
                                                 on_fallback=reasons.append)
    assert device == "CPU"
    assert reasons == ["nvcuda.dll unavailable"]
    _model, device = transcription.load_whisper("medium")
    assert device == "CPU"


def test_lazy_cuda_failure_records_stage_and_switches_progress_to_cpu(fake_audio, monkeypatch):
    gpu=object()
    cpu=object()
    monkeypatch.setattr(job,"load_whisper",lambda *a,**kw:(gpu,"NVIDIA GPU"))
    monkeypatch.setattr(job,"load_cpu_whisper",lambda *a,**kw:cpu)
    def fake_transcribe(model, clip, path, language, cancel):
        if model is gpu:
            raise RuntimeError("CUDNN_STATUS_EXECUTION_FAILED on synthetic")
        return [{"start":.2,"end":1.4,"text":"Recovered by CPU","part":1}]
    monkeypatch.setattr(job,"transcribe_clip",fake_transcribe)
    messages=[]
    folder=job.run_job(fake_audio,lambda text,pct:messages.append(text))
    result=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    assert result["device"]=="CPU"
    assert result["status"]=="complete"
    assert result["gpu_fallback"]["stage"]=="live_transcription"
    assert "CUDNN_STATUS" in result["gpu_fallback"]["reason"]
    assert any("Aceleración NVIDIA GPU seleccionada" in s for s in messages)
    assert any("Reintentando con CPU" in s for s in messages)
