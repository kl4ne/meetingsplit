"""Offline fault injection for optional-component preparation before final installer QA.

No downloads, model inference, registry edits or installer launches occur here.
"""
from __future__ import annotations
import hashlib
import io
from pathlib import Path
from types import SimpleNamespace

import pytest
from desktop import components
from engine import ollama
from engine.control import Cancellation, JobCancelled


def test_interrupted_vendor_download_discards_unverified_partial(tmp_path, monkeypatch):
    class Opener:
        def open(self, *_args, **_kwargs):
            return io.BytesIO(b'abc')
    monkeypatch.setattr(components, 'build_opener', lambda *args: Opener())
    package=components.Package('synthetic','https://developer.download.nvidia.com/synthetic.zip',
                               hashlib.sha256(b'abc').hexdigest(),3)
    task=Cancellation()
    with pytest.raises(JobCancelled):
        components.download(package,tmp_path,lambda _status: task.cancel(),task)
    assert not (tmp_path/'synthetic.zip').exists()
    assert not (tmp_path/'synthetic.partial').exists()
    assert not list(tmp_path.iterdir())


def test_vendor_download_network_timeout_has_no_installable_archive(tmp_path,monkeypatch):
    class Opener:
        def open(self,*_args,**_kwargs):
            raise TimeoutError('Simulated stalled connection')
    monkeypatch.setattr(components,'build_opener',lambda *args:Opener())
    package=components.Package('synthetic','https://developer.download.nvidia.com/synthetic.zip','0'*64,3)
    with pytest.raises(TimeoutError,match='stalled'):
        components.download(package,tmp_path,lambda _status:None,Cancellation())
    assert not list(tmp_path.iterdir())


def test_low_disk_space_blocks_runtime_install_before_download(tmp_path,monkeypatch):
    monkeypatch.setattr(components,'validate_local_folder',lambda p:Path(p))
    monkeypatch.setattr(components.shutil,'disk_usage',lambda _root:SimpleNamespace(free=10))
    monkeypatch.setattr(components,'download',lambda *_a,**_kw:pytest.fail('No network expected'))
    package=components.Package('synthetic','https://developer.download.nvidia.com/synthetic.zip','0'*64,10)
    with pytest.raises(OSError,match='free'):
        components.install_package(package,tmp_path,lambda _status:None,Cancellation())
    assert not (tmp_path/'Componentes'/'synthetic').exists()


def test_occupied_managed_ollama_port_refuses_to_start_server(tmp_path,monkeypatch):
    import socket
    monkeypatch.setattr(ollama,'validate_local_folder',lambda p:Path(p))
    monkeypatch.setattr(ollama,'reusable_existing',lambda:False)
    exe=tmp_path/'Componentes'/'ollama-0.40.6'/'ollama.exe'
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b'test only')
    class FakeSocket:
        def __enter__(self):return self
        def __exit__(self,*_args):return None
        def connect_ex(self,_addr):return 0
    monkeypatch.setattr(socket,'socket',lambda *args,**kwargs:FakeSocket())
    with pytest.raises(RuntimeError,match='busy'):
        with ollama.LocalService(tmp_path):
            pytest.fail('Unexpected server started')


def test_verified_existing_local_ollama_skips_duplicate_managed_server(tmp_path,monkeypatch):
    monkeypatch.setattr(ollama,'validate_local_folder',lambda p:Path(p))
    monkeypatch.setattr(ollama,'reusable_existing',lambda:True)
    with ollama.LocalService(tmp_path) as service:
        assert service.endpoint==ollama.DEFAULT_ENDPOINT
        assert service.process is None