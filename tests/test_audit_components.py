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
