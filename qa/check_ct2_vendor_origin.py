"""Prove provenance of the exact bundled CTranslate2 cuDNN DLL without running it.

Windows x64 CPython 3.11 PyPI wheel is downloaded separately by a tiny
read-only CI job, then checked against PyPI's wheel SHA-256 and the exact
native inventory hash. No wheel or DLL is redistributed by this QA script.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

EXPECTED_WHEEL = "ctranslate2-4.6.2-cp311-cp311-win_amd64.whl"
OFFICIAL_WHEEL_SHA256 = "ce7880fa5d2e1b36329998c711cb764c621a4d2a199b251b1ad02e770b641e91"
CANDIDATE_CUDNN_SHA256 = "c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05"
MAX_CUDNN_FILE = 50 * 1024 * 1024


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_ct2_wheel(wheel: Path, wheel_sha=OFFICIAL_WHEEL_SHA256,
                     target_native_sha=CANDIDATE_CUDNN_SHA256):
    wheel = Path(wheel)
    if wheel.name != EXPECTED_WHEEL:
        raise ValueError("Wrong official CTranslate2/Python/Windows wheel")
    actual_whl = sha256_file(wheel)
    if actual_whl != wheel_sha:
        raise ValueError("PyPI CPython 3.11 Windows wheel SHA-256 mismatch")
    with zipfile.ZipFile(wheel) as z:
        matching = [e for e in z.infolist() if
                    e.filename.casefold().endswith("/cudnn64_9.dll")]
        if len(matching) != 1 or matching[0].file_size <= 0 or matching[0].file_size > MAX_CUDNN_FILE:
            raise ValueError("Expected exactly one bounded cuDNN runtime DLL in official wheel")
        entry = matching[0]
        dll_digest = hashlib.sha256()
        count = 0
        with z.open(entry) as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                count += len(chunk)
                if count > MAX_CUDNN_FILE:
                    raise ValueError("cuDNN DLL exceeds expected provenance size")
                dll_digest.update(chunk)
        matched = dll_digest.hexdigest() == target_native_sha
        return {
            "schema": 1,
            "python_abi": "cp311",
            "platform": "win_amd64",
            "version": "4.6.2",
            "pypi_wheel_sha256_verified": True,
            "wheel_sha256": actual_whl,
            "native_path_in_wheel": entry.filename,
            "embedded_dll_bytes": count,
            "embedded_dll_sha256": dll_digest.hexdigest(),
            "candidate_native_sha256": target_native_sha,
            "candidate_matches_official_wheel": matched,
            "nvidia_sdk_license_applicability_verified": False,
            "nvidia_redistribution_conditions_reviewed": False,
            "release_allowed": False,
            "warning": "A binary hash match is NOT legal sign-off, a CVE scan, or consent to redistribute."
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    result = verify_ct2_wheel(args.wheel)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["candidate_matches_official_wheel"]:
        print("Bundled cuDNN differs from official CTranslate2 wheel; review source and origin.")
        return 2
    print("CTranslate2 cuDNN origin matches official pinned wheel; legal release still blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
