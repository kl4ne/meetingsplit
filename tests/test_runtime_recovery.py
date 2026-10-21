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
    assert 'Get-Partition' in script and 'Get-Disk' in script
    assert calls[0][-1].count('Get-Partition') == 1
    assert 'Get-Disk' in script
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


def test_native_bus_identification_skips_slow_shell(monkeypatch):
    import desktop.storage as storage
    monkeypatch.setattr(storage, '_native_windows_bus_type', lambda letter: 'USB' if letter == 'J' else 'NVMe')
    monkeypatch.setattr(storage.subprocess, 'run', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('slow shell invoked')))
    assert storage._windows_bus_type('D') == 'NVMe'
    assert storage._windows_bus_type('J') == 'USB'
    assert not storage.classify_storage(3, storage._windows_bus_type('J'))[0]


def test_failed_native_bus_query_has_four_second_limit(monkeypatch):
    import desktop.storage as storage
    captured = []
    monkeypatch.setattr(storage, '_native_windows_bus_type', lambda _: '')
    def fake_shell(args, **kwargs):
        captured.append(kwargs['timeout'])
        return SimpleNamespace(returncode=0, stdout='NVMe\n')
    monkeypatch.setattr(storage.subprocess, 'run', fake_shell)
    assert storage._windows_bus_type('D') == 'NVMe'
    assert captured == [4]


def test_cpu_fallback_uses_small_for_medium_model(monkeypatch):
    monkeypatch.setattr(transcription, '_gpu_runtime_ready', lambda: (False, 'cublas64_12.dll not found'))
    constructed = []
    class WhisperModel:
        def __init__(self, model_name, **kwargs):
            constructed.append((model_name, kwargs))
    monkeypatch.setitem(sys.modules, 'faster_whisper', SimpleNamespace(WhisperModel=WhisperModel))
    reports=[]
    _, device = transcription.load_whisper('medium', on_status=reports.append)
    assert device == 'CPU'
    assert constructed[0][0] == 'small'
    assert constructed[0][1]['compute_type'] == 'int8'
    assert 1 <= constructed[0][1]['cpu_threads'] <= 8
    assert 'small' in reports[-1]
