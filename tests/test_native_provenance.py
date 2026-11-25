from qa import native_provenance as native
from qa.native_inventory import inventory_package


def test_exact_hash_matching_and_gpu_flags(tmp_path,monkeypatch):
    root=tmp_path/'frozen'
    root.mkdir()
    (root/'MeetingSplit.exe').write_bytes(b'app')
    (root/'cudnn64_9.dll').write_bytes(b'gpu')
    (root/'Qt6WebEngineCore.dll').write_bytes(b'qt')
    (root/'Chromium-NOTICES.txt').write_text('candidate only')
    inputs=tmp_path/'inputs';inputs.mkdir()
    (inputs/'cudnn64_9.dll').write_bytes(b'gpu')
    (inputs/'Qt6WebEngineCore.dll').write_bytes(b'not the same')
    monkeypatch.setattr(native,'pe_version',lambda p:None)
    report=native.provenance(root,inventory_package(root),[
        (inputs/'cudnn64_9.dll',{'kind':'python_distribution','name':'ctranslate2','version':'4.6.2'}),
        (inputs/'Qt6WebEngineCore.dll',{'kind':'python_distribution','name':'qt','version':'6'}),
    ])
    assert report['gpu_vendor_paths']==['cudnn64_9.dll']
    assert 'Qt6WebEngineCore.dll' in report['unmatched_paths']
    assert 'cudnn64_9.dll' not in report['unmatched_paths']
    assert report['candidate_webengine_notice_paths']==['Chromium-NOTICES.txt']
    assert report['release_allowed'] is False
    assert report['license_review_complete'] is False
    assert report['security_review_complete'] is False
    import json
    assert str(tmp_path) not in json.dumps(report)


def test_gpu_patterns_do_not_classify_unrelated_dlls():
    assert native.GPU_VENDOR.fullmatch('cudnn64_9.dll')
    assert native.GPU_VENDOR.fullmatch('CUBLAS64_12.DLL')
    assert not native.GPU_VENDOR.fullmatch('Qt6Core.dll')
