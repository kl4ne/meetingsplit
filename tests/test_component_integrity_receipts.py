"""No-network regressions for optional-component extracted-file integrity receipts."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from desktop import components
from engine.control import Cancellation


def _package_and_zip(root, monkeypatch):
    from desktop import components as impl
    monkeypatch.setattr(impl, 'validate_local_folder', lambda path: Path(path))
    monkeypatch.setattr(impl.shutil, 'disk_usage', lambda _: SimpleNamespace(free=64*1024**3))
    content = io.BytesIO()
    with ZipFile(content, 'w') as archive:
        archive.writestr('vendor/bin/working.dll', b'known dll bytes')
        archive.writestr('vendor/LICENSE.txt', b'upstream vendor notice')
    payload = content.getvalue()
    pkg = components.Package('qa-integrity',
                             'https://developer.download.nvidia.com/qa-integrity.zip',
                             hashlib.sha256(payload).hexdigest(), len(payload))
    calls = []
    def fake_download(package, cache, progress, cancel):
        calls.append(1)
        cache.mkdir(parents=True,exist_ok=True)
        dest = cache/(package.name+'.zip')
        dest.write_bytes(payload)
        return dest
    monkeypatch.setattr(components, 'download', fake_download)
    return pkg, calls


def test_new_receipt_hashes_all_extracted_files_and_reuses_verified_install(tmp_path, monkeypatch):
    package, calls = _package_and_zip(tmp_path,monkeypatch)
    notices = []
    root = components.install_package(package, tmp_path, notices.append, Cancellation())
    assert root.is_dir()
    record = json.loads((root/'meetingsplit-receipt.json').read_text(encoding='utf-8'))
    assert record['schema'] == 2
    assert sorted(x['path'] for x in record['files']) == [
        'vendor/LICENSE.txt','vendor/bin/working.dll']
    assert all(len(x['sha256']) == 64 for x in record['files'])
    assert components.install_package(package,tmp_path,notices.append,Cancellation()) == root
    assert calls == [1], "No fresh download after verified reuse"


def test_changed_existing_native_dll_is_detected_before_reuse(tmp_path,monkeypatch):
    package, _ = _package_and_zip(tmp_path,monkeypatch)
    root = components.install_package(package,tmp_path,lambda _:None,Cancellation())
    dll = root/'vendor/bin/working.dll'
    dll.write_bytes(b'altered dll byxxx')
    with pytest.raises(ValueError,match='hash differs|files changed'):
        components.install_package(package,tmp_path,lambda _:None,Cancellation())


def test_unlisted_native_dll_in_existing_folder_is_rejected(tmp_path,monkeypatch):
    package, _ = _package_and_zip(tmp_path,monkeypatch)
    root = components.install_package(package,tmp_path,lambda _:None,Cancellation())
    (root/'vendor/bin/unlisted.dll').write_bytes(b'untrusted')
    with pytest.raises(ValueError,match='Unrecognized native executable'):
        components.install_package(package,tmp_path,lambda _:None,Cancellation())


def test_legacy_receipt_kept_without_destructive_migration(tmp_path,monkeypatch):
    package, calls = _package_and_zip(tmp_path,monkeypatch)
    root = tmp_path/'Componentes'/package.name
    root.mkdir(parents=True)
    old = {'name':package.name,'url':package.url,'sha256':package.sha256,'size':package.size}
    (root/'meetingsplit-receipt.json').write_text(json.dumps(old),encoding='utf-8')
    messages=[]
    assert components.install_package(package,tmp_path,messages.append,Cancellation()) == root
    assert not calls
    assert any('legacy' in msg for msg in messages)


def test_v2_missing_file_manifest_fails_closed(tmp_path,monkeypatch):
    package, _ = _package_and_zip(tmp_path,monkeypatch)
    root = components.install_package(package,tmp_path,lambda _:None,Cancellation())
    receipt = root/'meetingsplit-receipt.json'
    row = json.loads(receipt.read_text(encoding='utf-8'))
    row['files'] = []
    receipt.write_text(json.dumps(row),encoding='utf-8')
    with pytest.raises(ValueError,match='manifest is unavailable'):
        components.install_package(package,tmp_path,lambda _:None,Cancellation())
