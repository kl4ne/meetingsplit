import hashlib
import io
import json
import pytest
from desktop import components
from engine.control import Cancellation, JobCancelled


def test_resume_partial_validates_range_and_hash(tmp_path,monkeypatch):
    data=b'abcdef'
    pkg=components.Package('test','https://github.com/test.zip',hashlib.sha256(data).hexdigest(),len(data))
    (tmp_path/'test.partial').write_bytes(b'abc')
    class Response(io.BytesIO):
        status=206
        headers={'Content-Range':'bytes 3-5/6'}
    class Opener:
        def open(self,request,**kwargs):
            assert request.get_header('Range')=='bytes=3-'
            return Response(b'def')
    monkeypatch.setattr(components,'build_opener',lambda *a:Opener())
    assert components.download(pkg,tmp_path,lambda _:None,Cancellation()).read_bytes()==data
    assert not (tmp_path/'test.partial').exists()


def test_component_inventory_detects_changed_dll(tmp_path,monkeypatch):
    monkeypatch.setattr(components,'validate_local_folder',lambda p:p)
    pkg=components.Package('test','https://github.com/test.zip','0'*64,1)
    dll=tmp_path/'a.dll'
    dll.write_bytes(b'original')
    receipt=tmp_path/'meetingsplit-receipt.json'
    receipt.write_text(json.dumps({'sha256':pkg.sha256,'files':components.installed_inventory(tmp_path)}))
    components.verify_installed(pkg,tmp_path)
    dll.write_bytes(b'changed')
    with pytest.raises(ValueError,match='integrity'):
        components.verify_installed(pkg,tmp_path)


def _repair_fixture(tmp_path,monkeypatch):
    from zipfile import ZipFile
    from types import SimpleNamespace
    monkeypatch.setattr(components,'validate_local_folder',lambda p:p.resolve(strict=True))
    monkeypatch.setattr(components.shutil,'disk_usage',lambda p:SimpleNamespace(free=20*1024**3))
    archive=tmp_path/'fixture.zip'
    with ZipFile(archive,'w') as z:
        z.writestr('bin/new.dll',b'verified')
    data=archive.read_bytes()
    package=components.Package('test','https://github.com/test.zip',hashlib.sha256(data).hexdigest(),len(data))
    target=tmp_path/'Componentes'/'test'
    target.mkdir(parents=True)
    (target/'old.dll').write_bytes(b'old')
    (target/'meetingsplit-receipt.json').write_text(json.dumps({'sha256':package.sha256}))
    (tmp_path/'Modelos').mkdir()
    (tmp_path/'Modelos'/'model.bin').write_bytes(b'model')
    def download(pkg,cache,progress,cancel):
        result=cache/'test.zip'
        result.write_bytes(data)
        return result
    monkeypatch.setattr(components,'download',download)
    return package,target


def test_legacy_component_requires_opt_in_and_repair_preserves_old_files(tmp_path,monkeypatch):
    package,target=_repair_fixture(tmp_path,monkeypatch)
    task=Cancellation()
    with pytest.raises(ValueError,match='verified repair'):
        components.install_package(package,tmp_path,lambda _:None,task)
    assert (target/'old.dll').read_bytes()==b'old'
    result=components.install_package(package,tmp_path,lambda _:None,task,repair=True)
    assert result==target
    components.verify_installed(package,result)
    backups=list(target.parent.glob('.backup-test-*'))
    assert len(backups)==1 and (backups[0]/'old.dll').read_bytes()==b'old'
    assert (tmp_path/'Modelos'/'model.bin').read_bytes()==b'model'
    assert (result/'bin'/'new.dll').read_bytes()==b'verified'


def test_failed_repair_leaves_legacy_component_untouched(tmp_path,monkeypatch):
    package,target=_repair_fixture(tmp_path,monkeypatch)
    def fail(*args,**kwargs):
        raise OSError('simulated full disk')
    monkeypatch.setattr(components,'extract_verified',fail)
    with pytest.raises(OSError,match='full disk'):
        components.install_package(package,tmp_path,lambda _:None,Cancellation(),repair=True)
    assert (target/'old.dll').read_bytes()==b'old'
    assert not list(target.parent.glob('.backup-test-*'))
    assert not list(target.parent.glob('.stage-*'))


def test_hardlinked_partial_never_overwrites_another_file(tmp_path,monkeypatch):
    import os
    source=tmp_path/'external.txt'
    source.write_bytes(b'original')
    os.link(source,tmp_path/'test.partial')
    package=components.Package('test','https://github.com/test.zip','0'*64,20)
    monkeypatch.setattr(components,'build_opener',lambda *a:pytest.fail('unexpected network'))
    with pytest.raises(ValueError,match='Unsafe writable'):
        components.download(package,tmp_path,lambda _:None,Cancellation())
    assert source.read_bytes()==b'original'
