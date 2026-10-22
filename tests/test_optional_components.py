"""Security, cancellation and installer regressions for optional vendor components."""
import io
import json
from pathlib import Path
from zipfile import ZipFile
import pytest
from desktop import components
from engine import ollama
from engine.control import Cancellation, JobCancelled


@pytest.mark.parametrize('name',['../escape.dll','/absolute.dll','C:/escape.dll',
    '..\\escape.dll','dir/nul.dll','dir/file.dll:stream','dir./file.dll'])
def test_component_zip_cannot_escape_or_create_windows_special_files(tmp_path,name):
    archive=tmp_path/'bad.zip'
    # ZipFile normalizes backslashes on Windows when constructing ZipInfo;
    # emulate an archive made on another OS where the raw name is retained.
    from zipfile import ZipInfo
    info=ZipInfo('entry');info.filename=name
    with ZipFile(archive,'w') as z: z.writestr(info,b'bad')
    target=tmp_path/'stage';target.mkdir()
    with pytest.raises(ValueError): components.extract_verified(archive,target,Cancellation())
    assert not list(target.iterdir())


def test_zip_rejects_case_insensitive_duplicate_paths(tmp_path):
    archive=tmp_path/'bad.zip'
    with ZipFile(archive,'w') as z:
        z.writestr('bin/a.dll',b'one');z.writestr('bin/A.dll',b'two')
    target=tmp_path/'stage';target.mkdir()
    with pytest.raises(ValueError): components.extract_verified(archive,target,Cancellation())
    assert not list(target.iterdir())


def test_cancel_prevents_archive_file_writes(tmp_path):
    archive=tmp_path/'good.zip'
    with ZipFile(archive,'w') as z: z.writestr('bin/test.dll',b'test')
    target=tmp_path/'stage';target.mkdir()
    cancel=Cancellation();cancel.cancel()
    with pytest.raises(JobCancelled): components.extract_verified(archive,target,cancel)
    assert not list(target.iterdir())


def test_failed_hash_never_becomes_an_installable_archive(tmp_path,monkeypatch):
    class Opener:
        def open(self,*args,**kwargs): return io.BytesIO(b'evil')
    monkeypatch.setattr(components,'build_opener',lambda *args:Opener())
    p=components.Package('test','https://developer.download.nvidia.com/test.zip','0'*64,4)
    with pytest.raises(ValueError,match='integrity'): components.download(p,tmp_path,lambda _:None,Cancellation())
    assert not list(tmp_path.iterdir())


def test_vendor_redirects_reject_untrusted_hosts_and_http():
    redirect=components.VendorRedirects()
    for url in ('http://github.com/file','https://github.com.evil.test/file','https://evil.test/file'):
        with pytest.raises(ValueError): redirect.redirect_request(None,None,302,'',{},url)


def test_local_client_cannot_use_remote_urls_or_follow_redirects():
    with pytest.raises(ValueError): ollama._open('http://evil.test','/api/chat',{})
    with pytest.raises(ValueError): ollama.NoRedirect().redirect_request(None,None,302,'',{},'http://evil.test')
    with pytest.raises(ValueError): ollama.chat([],model='qwen3:4b-cloud')


def test_local_client_explicitly_disables_environment_proxies(monkeypatch):
    handlers=[]
    class Opener:
        def open(self,req,timeout):
            assert req.full_url=='http://127.0.0.1:11434/api/version'
            return io.BytesIO(b'{"version":"0.40.6"}')
    def build(*args): handlers.extend(args);return Opener()
    monkeypatch.setattr(ollama,'build_opener',build)
    assert ollama.request_json(ollama.DEFAULT_ENDPOINT,'/api/version')['version']=='0.40.6'
    assert handlers[0].proxies=={}


def test_stream_error_and_truncated_generation_are_not_reported_success(monkeypatch):
    monkeypatch.setattr(ollama,'_stream_open',lambda *args,**kwargs:io.BytesIO(b'{"error":"model unavailable"}\n'))
    with pytest.raises(RuntimeError,match='model unavailable'): ollama.chat([])
    monkeypatch.setattr(ollama,'_stream_open',lambda *args,**kwargs:io.BytesIO(b'{"message":{"content":"partial"}}\n'))
    with pytest.raises(RuntimeError,match='incomplete'): ollama.chat([])


def test_cancel_stops_chat_before_consuming_stream(monkeypatch):
    monkeypatch.setattr(ollama,'_stream_open',lambda *args,**kwargs:io.BytesIO(b'{"done":true}\n'))
    control=Cancellation();control.cancel()
    with pytest.raises(JobCancelled): ollama.chat([],cancel=control)


def test_existing_service_without_model_is_never_pulled_into(tmp_path,monkeypatch):
    monkeypatch.setattr(ollama,'validate_local_folder',lambda p:p)
    service=ollama.LocalService(tmp_path)
    monkeypatch.setattr(ollama,'existing_status',lambda *args:{'available':True,'model':None})
    with pytest.raises(RuntimeError,match='missing'): service.ensure_model(allow_download=True)


def test_existing_ollama_on_unverified_storage_is_not_reused(tmp_path,monkeypatch):
    weights=tmp_path/'model.gguf';weights.write_bytes(b'fake model')
    monkeypatch.setattr(ollama,'existing_status',lambda *args:{'model':{'name':ollama.MODEL}})
    monkeypatch.setattr(ollama,'request_json',lambda *args,**kwargs:{'modelfile':'FROM '+str(weights)})
    def reject(folder): raise ValueError('USB storage')
    monkeypatch.setattr(ollama,'validate_local_folder',reject)
    assert not ollama.reusable_existing()


def test_remote_ollama_alias_is_not_considered_a_local_model(monkeypatch):
    def request(endpoint,route,*args):
        if route=='/api/version': return {'version':'0.40.6'}
        return {'models':[{'name':ollama.MODEL,'remote_host':'https://remote.example','remote_model':'qwen3'}]}
    monkeypatch.setattr(ollama,'request_json',request)
    assert ollama.existing_status()['model'] is None


def test_optional_installer_does_not_bundle_large_runtime_or_opt_in_silently():
    root=Path(__file__).resolve().parents[1]
    setup=(root/'scripts/MeetingSplit.iss').read_text(encoding='utf-8')
    assert 'Name: "optionalcomponents"' in setup
    assert 'Flags: unchecked' in next(line for line in setup.splitlines() if line.startswith('Name: "optionalcomponents"'))
    assert '--configure-components' in setup and 'skipifsilent' in setup
    assert 'optional Ollama CPU' in setup
    assert 'optional CUDA' not in setup
    assert not any(p.name.endswith('.zip') for p in (root/'assets').iterdir())
    source=(root/'desktop/component_setup.py').read_text(encoding='utf-8')
    assert 'self.gpu=QCheckBox' not in source
    assert 'CPU-only policy prohibits optional NVIDIA/CUDA installation' in source


def test_cpu_only_whisper_never_runs_gpu_probe(monkeypatch,tmp_path):
    from engine import transcription
    from types import SimpleNamespace
    import sys
    calls=[]
    class WhisperModel:
        def __init__(self,name,**kwargs):
            calls.append((name,kwargs['device']))
    monkeypatch.setitem(sys.modules,'faster_whisper',SimpleNamespace(WhisperModel=WhisperModel))
    def forbidden(*args,**kwargs): raise AssertionError('CUDA must never be initialized')
    monkeypatch.setattr(components,'activate_gpu',forbidden)
    monkeypatch.setattr('desktop.cuda_probe.probe_cuda',forbidden)
    _,device=transcription.load_whisper('medium',model_cache=tmp_path/'Modelos')
    assert device=='CPU'
    assert calls==[('small','cpu')]


def test_custom_onedrive_root_cannot_receive_components(tmp_path,monkeypatch):
    from desktop.storage import validate_local_folder,UnsafeStorage
    root=tmp_path/'CustomSyncedFolder';root.mkdir()
    monkeypatch.setenv('OneDriveCommercial',str(root))
    with pytest.raises(UnsafeStorage,match='nube'): validate_local_folder(root)


def test_model_output_limit_does_not_produce_a_successful_report(monkeypatch):
    rows=b'{"message":{"content":"# partial"},"done":true,"done_reason":"length"}\n'
    monkeypatch.setattr(ollama,'_stream_open',lambda *args,**kwargs:io.BytesIO(rows))
    with pytest.raises(RuntimeError,match='output limit'): ollama.chat([])


def test_pinned_pyav_decodes_the_audio_api_used_by_faster_whisper(tmp_path):
    import wave
    from faster_whisper.audio import decode_audio
    source=tmp_path/'synthetic.wav'
    with wave.open(str(source),'wb') as stream:
        stream.setparams((1,2,16000,0,'NONE','not compressed'))
        stream.writeframes(b'\0\0'*16000)
    assert len(decode_audio(str(source)))==16000


def test_qwen_thinking_is_separate_and_does_not_mutate_source(monkeypatch):
    captured=[]
    def open_stream(endpoint,route,payload,cancel):
        captured.append(payload)
        return io.BytesIO(b'{"message":{"thinking":"internal analysis"}}\n{"message":{"content":"# Minutes"},"done":true,"done_reason":"stop"}\n')
    monkeypatch.setattr(ollama,'_stream_open',open_stream)
    messages=[{'role':'user','content':'Source text'}]
    assert ollama.chat(messages)=='# Minutes'
    assert messages==[{'role':'user','content':'Source text'}]
    assert captured[0]['messages']==messages
    assert captured[0]['think'] is True
