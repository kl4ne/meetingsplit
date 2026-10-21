"""Offline receipt-state regressions for the optional Ollama setup wizard."""
import json
from pathlib import Path
import pytest
from desktop import components
from engine import ollama
from engine.control import Cancellation, JobCancelled


def setup_test_root(tmp_path,monkeypatch):
    monkeypatch.setattr(ollama,'validate_local_folder',lambda p:Path(p))
    monkeypatch.setattr(ollama,'reusable_existing',lambda:False)
    return tmp_path


def read_receipt(root):
    return json.loads((root/'Componentes'/'ollama-validation.json').read_text(encoding='utf-8'))


def test_failed_optional_download_records_failure_instead_of_stale_testing(tmp_path,monkeypatch):
    root=setup_test_root(tmp_path,monkeypatch)
    def no_network(*args,**kwargs):
        raise TimeoutError('Synthetic download interruption')
    monkeypatch.setattr(components,'install_package',no_network)
    with pytest.raises(TimeoutError,match='interruption'):
        ollama.setup_ollama(root,lambda _:None,Cancellation())
    report=read_receipt(root)
    assert report['ok'] is False and report['status']=='failed'
    assert 'Synthetic download interruption' in report['error']
    assert not (root/'Componentes'/'ollama-smoke-minutes.md').exists()


def test_cancelled_component_setup_records_cancelled_state(tmp_path,monkeypatch):
    root=setup_test_root(tmp_path,monkeypatch)
    def cancelled(*args,**kwargs):
        raise JobCancelled('Synthetic cancellation')
    monkeypatch.setattr(components,'install_package',cancelled)
    with pytest.raises(JobCancelled):
        ollama.setup_ollama(root,lambda _:None,Cancellation())
    report=read_receipt(root)
    assert report['ok'] is False and report['status']=='cancelled'
    assert 'error' not in report


def test_completed_optional_setup_records_validated_model(tmp_path,monkeypatch):
    root=setup_test_root(tmp_path,monkeypatch)
    monkeypatch.setattr(ollama,'reusable_existing',lambda:True)
    monkeypatch.setattr(components,'install_package',lambda *_a,**_k:pytest.fail('Should reuse model'))
    class Local:
        endpoint=ollama.DEFAULT_ENDPOINT
        def __enter__(self):return self
        def __exit__(self,*_a):return None
        def ensure_model(self,allow_download=False):return {'digest':'sha256:synthetic'}
    monkeypatch.setattr(ollama,'LocalService',lambda *_a,**_k:Local())
    monkeypatch.setattr(ollama,'request_json',lambda *_a,**_k:{'license':'Apache-2.0'})
    import engine.summarize as summarize
    monkeypatch.setattr(summarize,'summarize_local',lambda *_a,**_k:'# Verified synthetic minutes')
    ollama.setup_ollama(root,lambda _:None,Cancellation())
    report=read_receipt(root)
    assert report['ok'] is True and report['status']=='complete'
    assert report['digest']=='sha256:synthetic'
    assert (root/'Componentes'/'ollama-smoke-minutes.md').read_text()=='# Verified synthetic minutes'