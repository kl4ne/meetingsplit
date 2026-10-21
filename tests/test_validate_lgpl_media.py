"""Test negative gates before expensive Windows build and packaging."""
from pathlib import Path
import subprocess
import zipfile
import pytest
from qa import validate_lgpl_media as m


def test_rejects_x264_x265_and_xvid_even_with_hashed_names():
    for name in ('libx264-165-11ed6a.dll','libx265-eeae.dll','libxvidcore-4.dll'):
        with pytest.raises(ValueError, match='GPL'):
            m.reject_native_names(['av.libs/'+name])
    m.reject_native_names(['av.libs/avcodec-62-d1a.dll','av.libs/libopus-0.dll'])


def test_wheel_native_codec_rejection(tmp_path, monkeypatch):
    binary_dir=tmp_path/'bin';binary_dir.mkdir()
    for name in ('ffmpeg.exe','ffprobe.exe'):(binary_dir/name).write_bytes(b'test')
    wheel=tmp_path/'av.whl'
    with zipfile.ZipFile(wheel,'w') as archive:
        archive.writestr('av.libs/libx264-165-aaa.dll',b'bad')
        archive.writestr('av/audio/codec.cp311-win_amd64.pyd',b'fake')
    with pytest.raises(ValueError,match='GPL'):
        m.validate(binary_dir,wheel)


def test_forbidden_configuration_fails(tmp_path, monkeypatch):
    binary_dir=tmp_path/'bin';binary_dir.mkdir()
    for name in ('ffmpeg.exe','ffprobe.exe'):(binary_dir/name).write_bytes(b'test')
    wheel=tmp_path/'av.whl'
    with zipfile.ZipFile(wheel,'w') as archive:
        archive.writestr('av/audio/codec.cp311-win_amd64.pyd',b'fake')
    def fake_run(*args,**kwargs):
        return subprocess.CompletedProcess(args,0,'ffmpeg version 9\nconfiguration: --enable-gpl --enable-libx264\n','')
    monkeypatch.setattr(m.subprocess,'run',fake_run)
    with pytest.raises(ValueError,match='GPL'):
        m.validate(binary_dir,wheel)


def test_license_safe_configuration_accepted_as_build_evidence(tmp_path, monkeypatch):
    binary_dir=tmp_path/'bin';binary_dir.mkdir()
    for name in ('ffmpeg.exe','ffprobe.exe'):(binary_dir/name).write_bytes(b'test')
    wheel=tmp_path/'av.whl'
    with zipfile.ZipFile(wheel,'w') as archive:
        archive.writestr('av/audio/codec.cp311-win_amd64.pyd',b'fake')
    def fake_run(*args,**kwargs):
        return subprocess.CompletedProcess(args,0,'ffmpeg version 9\nconfiguration: --enable-libmp3lame --disable-gpl\n','')
    monkeypatch.setattr(m.subprocess,'run',fake_run)
    m.validate(binary_dir,wheel)


def test_ci_source_builder_has_fail_closed_vendor_strategy():
    source=(Path(__file__).resolve().parents[1]/'scripts'/'prepare_lgpl_media.ps1').read_text(encoding='utf-8')
    assert 'libx264' in source and 'libx265' in source
    assert 'repaired' in source and 'delvewheel' in source
    assert 'release_allowed = $false' in source
    assert 'av==16.0.1' in source and '--no-binary av' in source
def test_media_vendor_archive_pin_matches_exact_release():
    from pathlib import Path
    script=(Path(__file__).resolve().parents[1]/'scripts/prepare_lgpl_media.ps1').read_text(encoding='utf-8')
    assert 'autobuild-2026-10-20-13-08/ffmpeg-n8.1.3-18-g46d899d7a0-win64-lgpl-shared-8.1.zip' in script
    assert '453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a' in script
    assert 'download/latest/' not in script
    assert 'win64-lgpl-shared-9.0.zip' not in script
