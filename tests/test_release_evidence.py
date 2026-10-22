"""Offline evidence integrity / release-hold regression; no Windows runner needed."""
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from qa.verify_release_evidence import (
    audit_archive, EvidenceError, PINNED_FFMPEG_SHA256,
    PINNED_PYAV_SOURCE_SHA256, EXPECTED_ASSET,
)


def create_fake_archive(tmp_path, *, inject_gpl=False, corrupt_notice=False, include_chromium=False):
    files = {}

    def add(path, data):
        files[path] = dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                           native=Path(path).suffix.lower() in {'.exe', '.dll', '.pyd', '.so', '.dylib'})

    add('MeetingSplit.exe', b'exe-placeholder')
    add('_internal/PySide6/Qt6WebEngineCore.dll', b'qt-placeholder')
    add('_internal/ctranslate2/cudnn64_9.dll', b'nvidia-placeholder')
    add('_internal/bin/libx264-foo.dll' if inject_gpl else '_internal/bin/ffmpeg.exe', b'media-placeholder')
    ffver = b'ffmpeg version 8.1\nconfiguration: --enable-version3 --enable-shared --disable-static\n'
    fpver = b'ffprobe version 8.1\nconfiguration: --enable-version3 --enable-shared --disable-static\n'
    add('_internal/legal/ffmpeg-build.txt', ffver)
    add('_internal/legal/ffprobe-build.txt', fpver)
    add('_internal/legal/LICENSE', b'some license')
    if include_chromium:
        add('_internal/docs/licenses/Chromium-ThirdPartyNotices.txt', b'vendor notices')
    receipt = dict(release_allowed=False, ffmpeg_archive_bytes=80993108,
                   source_url='https://github.com/BtbN/FFmpeg-Builds/releases/download/' + EXPECTED_ASSET,
                   ffmpeg_archive_sha256=PINNED_FFMPEG_SHA256,
                   pyav_source_sha256=PINNED_PYAV_SOURCE_SHA256,
                   repaired_pyav_wheel_sha256='c' * 64,
                   ffmpeg_configuration=ffver.decode())
    add('_internal/legal/LGPL_MEDIA_BUILD_RECEIPT.json', json.dumps(receipt).encode())
    manifest = dict(product='MeetingSplit', inventory_scope='actual frozen package', release_allowed=False,
                    license_review_complete=False, security_review_complete=False,
                    files=list(files.values()), file_count=len(files),
                    native_file_count=sum(f['native'] for f in files.values()),
                    package_bytes=sum(f['bytes'] for f in files.values()),
                    ffmpeg=dict(configuration_found=True, log_in_package=True,
                                log_sha256=hashlib.sha256(ffver).hexdigest(),
                                flags=['--enable-version3', '--enable-shared', '--disable-static']))
    smoke = dict(clean_install=True, same_version_reinstall=True, uninstall=True, external_data_preserved=True)
    zip_path = tmp_path / 'reports.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('build/native-inventory.json', json.dumps(manifest))
        z.writestr('build/lgpl-wheel/lgpl-media-receipt.json', json.dumps(receipt))
        z.writestr('build/legal/LGPL_MEDIA_BUILD_RECEIPT.json', json.dumps(receipt))
        z.writestr('build/legal/ffmpeg-build.txt', ffver)
        z.writestr('build/legal/ffprobe-build.txt', fpver)
        z.writestr('build/legal/LICENSE', b'DOCTORED' if corrupt_notice else b'some license')
        z.writestr('work/installer-smoke/installer-qa.json', json.dumps(smoke))
    return zip_path


def test_evidence_review_preserves_release_hold_and_critical_gaps(tmp_path):
    report = audit_archive(create_fake_archive(tmp_path))
    assert report['evidence_integrity_ok'] is True
    assert report['binary_bytes_verified'] is False
    assert report['release_allowed'] is False
    assert report['license_review_complete'] is False
    assert report['security_review_complete'] is False
    assert len(report['ctranslate2_bundled_cudnn']) == 1
    assert any('Chromium' in gap for gap in report['manual_gaps'])


def test_chromium_notice_is_detected_without_granting_release(tmp_path):
    report = audit_archive(create_fake_archive(tmp_path, include_chromium=True))
    assert report['chromium_notice_files_detected']
    assert report['release_allowed'] is False


def test_gpl_codecs_are_rejected(tmp_path):
    with pytest.raises(EvidenceError, match='Prohibited codec'):
        audit_archive(create_fake_archive(tmp_path, inject_gpl=True))


def test_legal_file_digest_must_match_frozen_inventory(tmp_path):
    with pytest.raises(EvidenceError, match='different frozen manifest hash'):
        audit_archive(create_fake_archive(tmp_path, corrupt_notice=True))


def test_duplicate_evidence_archive_entries_are_rejected(tmp_path):
    archive = create_fake_archive(tmp_path)
    with zipfile.ZipFile(archive, 'a') as z:
        z.writestr('build/native-inventory.json', '{"tampered":true}')
    with pytest.raises(EvidenceError, match='Duplicate archive'):
        audit_archive(archive)


def test_reject_falsely_open_release_gate(tmp_path):
    archive = create_fake_archive(tmp_path)
    with zipfile.ZipFile(archive) as z:
        contents = {name: z.read(name) for name in z.namelist()}
    manifest = json.loads(contents['build/native-inventory.json'])
    manifest['release_allowed'] = True
    contents['build/native-inventory.json'] = json.dumps(manifest).encode()
    with zipfile.ZipFile(archive, 'w') as z:
        for name, data in contents.items():
            z.writestr(name, data)
    with pytest.raises(EvidenceError, match='incorrectly suggests approval'):
        audit_archive(archive)
