"""Offline tests for official wheel SHA and inner cuDNN provenance verifier."""
import hashlib
from pathlib import Path
from zipfile import ZipFile
import pytest

from qa.check_ct2_vendor_origin import EXPECTED_WHEEL, verify_ct2_wheel


def make_wheel(tmp_path, content=b"synthetic CUDA placeholder", name="ctranslate2/cudnn64_9.dll"):
    wheel = tmp_path / EXPECTED_WHEEL
    with ZipFile(wheel, "w") as z:
        z.writestr(name, content)
    whl_sha = hashlib.sha256(wheel.read_bytes()).hexdigest()
    dll_sha = hashlib.sha256(content).hexdigest()
    return wheel, whl_sha, dll_sha


def test_pinned_wheel_and_exact_dll_match_is_evidence_not_approval(tmp_path):
    wheel, wsha, dsha = make_wheel(tmp_path)
    result = verify_ct2_wheel(wheel, wsha, dsha)
    assert result["candidate_matches_official_wheel"] is True
    assert result["release_allowed"] is False
    assert result["nvidia_sdk_license_applicability_verified"] is False


def test_wheel_tampering_rejected_before_native_bytes(tmp_path):
    wheel, wsha, dsha = make_wheel(tmp_path)
    with wheel.open("ab") as output:
        output.write(b"forged")
    with pytest.raises(ValueError, match="wheel SHA-256 mismatch"):
        verify_ct2_wheel(wheel, wsha, dsha)


def test_bundle_mismatch_is_reported_not_approved(tmp_path):
    wheel, wsha, _dsha = make_wheel(tmp_path)
    result = verify_ct2_wheel(wheel, wsha, "0" * 64)
    assert result["candidate_matches_official_wheel"] is False
    assert result["release_allowed"] is False


def test_missing_cudnn_in_wheel_fails_closed(tmp_path):
    wheel, wsha, dsha = make_wheel(tmp_path, name="ctranslate2/other.dll")
    with pytest.raises(ValueError, match="exactly one"):
        verify_ct2_wheel(wheel, wsha, dsha)


def test_duplicate_dll_fails_closed(tmp_path):
    wheel = tmp_path/EXPECTED_WHEEL
    with ZipFile(wheel,"w") as z:
        z.writestr("ctranslate2/cudnn64_9.dll",b"first")
        z.writestr("subfolder/cudnn64_9.dll",b"second")
    wsha = hashlib.sha256(wheel.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="exactly one"):
        verify_ct2_wheel(wheel, wsha, "0"*64)
