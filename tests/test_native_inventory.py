"""QA inventory regressions that run without GPU, Windows, network, or installer."""
import json
import os
from pathlib import Path
import pytest
from qa.native_inventory import inventory_package, classify_ffmpeg, main, hash_file


def test_hash_manifest_records_every_shipped_binary_and_relpaths_only(tmp_path):
    root=tmp_path/'frozen';root.mkdir()
    (root/'MeetingSplit.exe').write_bytes(b'fake executable')
    native=root/'_internal'/'PySide6'/'Qt6Core.dll'
    native.parent.mkdir(parents=True)
    native.write_bytes(b'fake qt')
    web=root/'_internal'/'ui'/'index.html'
    web.parent.mkdir(parents=True)
    web.write_text('public UI',encoding='utf-8')
    legal=root/'_internal'/'legal';legal.mkdir()
    (legal/'ffmpeg-build.txt').write_text('ffmpeg version 7.1\nconfiguration: --enable-gpl --enable-version3 --disable-debug\n')
    result=inventory_package(root)
    rows={x['path']:x for x in result['files']}
    assert rows['MeetingSplit.exe']['native'] is True
    assert rows['_internal/PySide6/Qt6Core.dll']['sha256']==hash_file(native)
    assert rows['_internal/ui/index.html']['native'] is False
    assert result['ffmpeg']['configuration_found'] is True
    assert any('GPL' in x for x in result['ffmpeg']['issues'])
    assert result['release_allowed'] is False and result['license_review_complete'] is False
    assert str(tmp_path) not in json.dumps(result)
    output=tmp_path/'manifest.json'
    assert main([str(root),'--output',str(output)])==0
    assert json.loads(output.read_text())['file_count']==4


def test_missing_ffmpeg_flags_cannot_be_mistaken_for_a_legal_approval(tmp_path):
    root=tmp_path/'package';root.mkdir();(root/'MeetingSplit.exe').write_bytes(b'a')
    result=inventory_package(root)
    assert result['ffmpeg']['configuration_found'] is False
    assert result['release_allowed'] is False
    assert result['manual_review_flags']


def test_nonfree_ffmpeg_is_flagged():
    row=classify_ffmpeg('configuration: --enable-nonfree --enable-gpl\n')
    assert len(row['issues'])>=2


def test_invalid_package_is_rejected(tmp_path):
    with pytest.raises((FileNotFoundError,ValueError)):
        inventory_package(tmp_path/'missing')
    with pytest.raises(ValueError,match='MeetingSplit.exe'):
        inventory_package(tmp_path)


@pytest.mark.skipif(os.name == "nt", reason="Windows cannot create case-colliding filenames")
def test_windows_case_insensitive_file_collision_detected(tmp_path):
    root=tmp_path/'package';root.mkdir()
    (root/'MeetingSplit.exe').write_bytes(b'a')
    (root/'MEETINGSPLIT.EXE').write_bytes(b'b')
    with pytest.raises(ValueError,match='case-insensitive'):
        inventory_package(root)