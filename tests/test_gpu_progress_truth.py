"""Regression: MeetingSplit never activates GPU for Whisper or Ollama.

Tests use synthetic paths/mocks: no GPU, audio, network, external services or Actions.
"""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
from engine import job, transcription, ollama


@pytest.fixture
def synthetic_work(tmp_path, monkeypatch):
    src=tmp_path/'fake.wav'
    src.write_bytes(b'dummy local file')
    monkeypatch.setattr(job,'validate_local_folder',lambda path:Path(path).resolve(strict=True))
    monkeypatch.setattr(job,'probe',lambda path:12)
    monkeypatch.setattr(job,'detect_silences',lambda src,cancel:[])
    monkeypatch.setattr(job,'export_clip',lambda src,out,clip,fmt,cancel:out.write_bytes(b'fake') or {'duration':12})
    monkeypatch.setattr(job,'transcribe_clip',lambda model,clip,path,language,cancel:
                        [{'start':.1,'end':1.2,'text':'Synthetic only','part':1}])
    config={'file':str(src),'output':str(tmp_path),'action':'transcribe',
            'format':'mp3','minutes':5,'overlap':20,'model':'medium',
            'input_language':'en','report':'minutes','report_language':'en',
            'zip_output':False,'local_summary':False}
    return config


def test_whisper_always_loads_cpu_small_even_with_nvidia_present(monkeypatch,tmp_path):
    devices=[]
    class WhisperModel:
        def __init__(self,name,**kw):
            devices.append((name,kw))
    monkeypatch.setitem(sys.modules,'faster_whisper',SimpleNamespace(WhisperModel=WhisperModel))
    def forbidden(*args,**kwargs):
        raise AssertionError('GPU activity must never happen')
    import desktop.components as components
    import desktop.cuda_probe as cuda_probe
    monkeypatch.setattr(components,'activate_gpu',forbidden)
    monkeypatch.setattr(cuda_probe,'probe_cuda',forbidden)
    monkeypatch.setattr(transcription,'_gpu_runtime_ready',forbidden)
    status=[]
    for requested in ('small','medium','large-v3'):
        model,device=transcription.load_whisper(requested,
                model_cache=tmp_path/'Modelos',on_status=status.append)
        assert device=='CPU'
        assert model is not None
    assert [row[0] for row in devices]==['small']*3
    assert all(row[1]['device']=='cpu' and row[1]['compute_type']=='int8'
               for row in devices)
    assert all('CPU' in line for line in status)


def test_job_manifest_cpu_only_and_actual_small(synthetic_work,monkeypatch):
    monkeypatch.setattr(job,'load_whisper',lambda *args,**kw:(object(),'CPU'))
    progress=[]
    root=job.run_job(synthetic_work,lambda text,pct:progress.append(text))
    doc=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    assert doc['execution_policy']=='CPU_ONLY'
    assert doc['device']=='CPU'
    assert doc['model']=='medium'
    assert doc['actual_model']=='small'
    assert doc['status']=='complete'
    assert any('con CPU' in line for line in progress)


def test_job_rejects_non_cpu_engine(synthetic_work,monkeypatch):
    monkeypatch.setattr(job,'load_whisper',lambda *args,**kw:(object(),'NVIDIA GPU'))
    with pytest.raises(RuntimeError,match='CPU-only'):
        job.run_job(synthetic_work,lambda text,pct:None)


def test_ollama_api_request_forces_cpu_including_existing_service(monkeypatch):
    import io
    requests=[]
    def fake_stream(endpoint,route,payload,cancel):
        requests.append((endpoint,route,payload))
        return io.BytesIO(b'{"message":{"content":"# Minute"},"done":true}\n')
    monkeypatch.setattr(ollama,'_stream_open',fake_stream)
    assert ollama.chat([{'role':'user','content':'synthetic'}],endpoint=ollama.DEFAULT_ENDPOINT)=='# Minute'
    assert requests[0][2]['options']['num_gpu']==0
    assert requests[0][0]==ollama.DEFAULT_ENDPOINT


def test_legacy_gpu_installer_is_rejected(tmp_path):
    from desktop.components import install_gpu
    from engine.control import Cancellation
    with pytest.raises(RuntimeError,match='disabled'):
        install_gpu(tmp_path,lambda *_:None,Cancellation())
