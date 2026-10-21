"""Regression tests for ASUS findings: D: storage detection and missing CUDA DLL."""
import sys
from types import SimpleNamespace

from desktop.storage import classify_storage, _windows_bus_type
from engine import transcription


def test_windows_bus_check_uses_storage_and_cim_and_rejects_usb(monkeypatch):
    calls = []
    def cmd_run(args, **kwargs):
        calls.append(args)
        # Real output from the PowerShell script's classification stage
        return SimpleNamespace(returncode=0, stdout='USB\n')
    monkeypatch.setattr('desktop.storage.subprocess.run', cmd_run)
    assert _windows_bus_type('J') == 'USB'
    assert not classify_storage(3, _windows_bus_type('J'))[0]
    script=calls[0][-1]
    assert 'Get-Partition' in script and 'Get-CimInstance' in script
    assert 'Get-CimAssociatedInstance' in script
    assert "DriveLetter 'J'" in script


def test_windows_bus_fallback_accepts_nvme_disk(monkeypatch):
    def cmd_run(args, **kwargs):
        return SimpleNamespace(returncode=0, stdout='NVMe\n')
    monkeypatch.setattr('desktop.storage.subprocess.run', cmd_run)
    assert _windows_bus_type('D') == 'NVMe'
    assert classify_storage(3, _windows_bus_type('D'))[0]
    assert _windows_bus_type('D:;echo hi') == ''  # input never injected into powershell


def test_cudnn_cublas_missing_before_gpu_model_load_falls_back_to_cpu(monkeypatch):
    events = []
    class WhisperModel:
        def __init__(self, *args, **kwargs):
            events.append(kwargs['device'])
    monkeypatch.setitem(sys.modules, 'faster_whisper', SimpleNamespace(WhisperModel=WhisperModel))
    monkeypatch.setattr(transcription, '_gpu_runtime_ready', lambda: (False, 'cublas64_12.dll missing'))
    model, device=transcription.load_whisper('small',on_status=events.append)
    assert isinstance(model,WhisperModel)
    assert device == 'CPU' and events[-1] == 'cpu'
    assert 'cublas64_12.dll' in events[0]
    assert 'cuda' not in events  # No GPU construction attempted


def test_cuda_fallback_predicate_only_matches_accelerator_errors():
    assert transcription.is_cuda_runtime_error(RuntimeError('Library cublas64_12.dll is not found'))
    assert transcription.is_cuda_runtime_error(RuntimeError('CUDNN_STATUS_EXECUTION_FAILED'))
    assert not transcription.is_cuda_runtime_error(ValueError('Audio source unreadable'))
