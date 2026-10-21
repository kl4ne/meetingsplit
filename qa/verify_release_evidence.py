"""Validate an existing MeetingSplit Windows QA report archive, without rebuilding.

This verifies report consistency, not the actual frozen EXE/DLL bytes or legal
permission. Evidence corruption fails closed; release is NEVER authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

PINNED_FFMPEG_SHA256 = "453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a"
PINNED_PYAV_SOURCE_SHA256 = "dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf"
EXPECTED_ASSET = "autobuild-2026-10-20-13-08/ffmpeg-n8.1.3-18-g46d899d7a0-win64-lgpl-shared-8.1.zip"
NATIVE_SUFFIXES = {".exe", ".dll", ".pyd", ".so", ".dylib"}
BAD_CODEC = re.compile(r"(?:^|[-_])(?:lib)?(?:x264|x265|xvid(?:core)?|xavs2)(?:[-_.]|$)", re.I)
BAD_FLAGS = {"--enable-gpl", "--enable-nonfree", "--enable-libx264", "--enable-libx265", "--enable-libxvid"}
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class EvidenceError(ValueError):
    """Evidence integrity or pinned-package identity is not established."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_archive(report_zip: Path) -> dict:
    with zipfile.ZipFile(report_zip) as archive:
        names = set(archive.namelist())
        if len(names) != len(archive.namelist()):
            raise EvidenceError("Duplicate archive entries are not trustworthy")
        required = {
            "build/native-inventory.json",
            "build/lgpl-wheel/lgpl-media-receipt.json",
            "build/legal/LGPL_MEDIA_BUILD_RECEIPT.json",
            "build/legal/ffmpeg-build.txt",
            "build/legal/ffprobe-build.txt",
            "work/installer-smoke/installer-qa.json",
        }
        if required - names:
            raise EvidenceError("Report ZIP lacks required receipts: " + ", ".join(sorted(required - names)))
        try:
            manifest = json.loads(archive.read("build/native-inventory.json"))
            receipt = json.loads(archive.read("build/lgpl-wheel/lgpl-media-receipt.json"))
            packaged_receipt = json.loads(archive.read("build/legal/LGPL_MEDIA_BUILD_RECEIPT.json"))
            smoke = json.loads(archive.read("work/installer-smoke/installer-qa.json"))
        except (KeyError, json.JSONDecodeError) as exc:
            raise EvidenceError("Malformed QA report: " + str(exc)) from exc

        if manifest.get("product") != "MeetingSplit" or manifest.get("inventory_scope") != "actual frozen package":
            raise EvidenceError("Manifest is not the expected frozen MeetingSplit package inventory")
        if manifest.get("release_allowed") is not False or manifest.get("license_review_complete") is not False or manifest.get("security_review_complete") is not False:
            raise EvidenceError("Report incorrectly suggests approval for public distribution")
        files = manifest.get("files")
        if not isinstance(files, list) or not files:
            raise EvidenceError("Missing frozen-package file inventory")
        seen = set()
        total = native = 0
        blocked = []
        for row in files:
            path = row.get("path")
            if not isinstance(path, str) or not path or "\\" in path:
                raise EvidenceError("Malformed native path in report")
            parsed = PurePosixPath(path)
            if parsed.is_absolute() or ".." in parsed.parts or path.startswith("./"):
                raise EvidenceError("Unsafe package path in report: " + path)
            if path.casefold() in seen:
                raise EvidenceError("Case-insensitive duplicate in Windows package inventory: " + path)
            seen.add(path.casefold())
            size = row.get("bytes")
            digest = row.get("sha256")
            expected_native = parsed.suffix.casefold() in NATIVE_SUFFIXES
            if type(size) is not int or size < 0 or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise EvidenceError("Invalid file size/digest for " + path)
            if row.get("native") is not expected_native:
                raise EvidenceError("Incorrect native-binary flag for " + path)
            if expected_native and BAD_CODEC.search(parsed.name):
                blocked.append(path)
            total += size
            native += int(expected_native)
        if blocked:
            raise EvidenceError("Prohibited codec DLLs/binaries in inventory: " + ", ".join(blocked))
        if (manifest.get("file_count"), manifest.get("native_file_count"), manifest.get("package_bytes")) != (len(files), native, total):
            raise EvidenceError("Native inventory aggregate totals do not match file entries")

        ffmpeg = manifest.get("ffmpeg") or {}
        if ffmpeg.get("configuration_found") is not True or ffmpeg.get("log_in_package") is not True:
            raise EvidenceError("FFmpeg configure flags or embedded log are missing")
        flags = set(ffmpeg.get("flags") or [])
        if flags & BAD_FLAGS:
            raise EvidenceError("FFmpeg report includes GPL/nonfree flags: " + ", ".join(sorted(flags & BAD_FLAGS)))
        if "--enable-shared" not in flags or "--disable-static" not in flags:
            raise EvidenceError("FFmpeg is not identified as the pinned shared build")
        if sha256(archive.read("build/legal/ffmpeg-build.txt")) != ffmpeg.get("log_sha256"):
            raise EvidenceError("FFmpeg -version bytes conflict with the manifest SHA-256")
        # This report contains build/legal files, but not the native executable bytes.
        file_map = {row["path"]: row for row in files}
        for entry in names:
            if not entry.startswith("build/legal/") or entry.endswith("/"):
                continue
            packaged_path = "_internal/legal/" + entry.removeprefix("build/legal/")
            if packaged_path not in file_map:
                raise EvidenceError("Legal file missing in package inventory: " + packaged_path)
            data = archive.read(entry)
            row = file_map[packaged_path]
            if sha256(data) != row["sha256"] or len(data) != row["bytes"]:
                raise EvidenceError("Collected legal notice has different frozen manifest hash: " + entry)

        if receipt != packaged_receipt:
            raise EvidenceError("Media receipt in build/legal is different from pinned source receipt")
        if receipt.get("release_allowed") is not False:
            raise EvidenceError("Media source receipt incorrectly approves release")
        if (receipt.get("ffmpeg_archive_sha256") != PINNED_FFMPEG_SHA256
            or receipt.get("pyav_source_sha256") != PINNED_PYAV_SOURCE_SHA256
            or EXPECTED_ASSET not in receipt.get("source_url", "")
            or type(receipt.get("ffmpeg_archive_bytes")) is not int
            or receipt["ffmpeg_archive_bytes"] < 10_000_000
            or not SHA256_RE.fullmatch(str(receipt.get("repaired_pyav_wheel_sha256", "")))):
            raise EvidenceError("Pinned media source or rebuilt wheel receipt is missing/mismatched")
        if "--enable-shared" not in receipt.get("ffmpeg_configuration", ""):
            raise EvidenceError("Source receipt does not describe shared FFmpeg")
        if not all(smoke.get(key) is True for key in ("clean_install", "same_version_reinstall", "uninstall", "external_data_preserved")):
            raise EvidenceError("Basic disposable-runner installer acceptance report is incomplete")

        paths_lower = [r["path"].lower() for r in files]
        qt_webengine = any("qt6webenginecore.dll" in p for p in paths_lower)
        cudnn = [r for r in files if PurePosixPath(r["path"]).name.lower() == "cudnn64_9.dll"]
        chromium_notices = [p for p in paths_lower if ("chromium" in p or "qtwebengine" in p)
                            and ("license" in p or "notice" in p or "copyright" in p)
                            and PurePosixPath(p).suffix in {".txt", ".md", ".html"}]
        gaps = [
            "Frozen application EXE/DLL bytes are not in this report archive; this audit validates report integrity only",
            "Independent corresponding-source/build/relinking review for FFmpeg, PyAV, Qt and dependencies remains open",
            "Native vulnerability assessment, model and optional component license review remain open",
        ]
        if qt_webengine and not chromium_notices:
            gaps.append("Qt WebEngine/Chromium third-party notice file not found in frozen-package inventory")
        if cudnn:
            gaps.append("Bundled CTranslate2 cudnn64_9.dll requires exact NVIDIA redistribution provenance/permissions")
        return {
            "schema": 1, "version": "0.8.6",
            "report_archive_sha256": sha256(report_zip.read_bytes()),
            "evidence_integrity_ok": True, "binary_bytes_verified": False,
            "file_count": len(files), "native_file_count": native,
            "package_bytes_claimed_by_manifest": total,
            "ffmpeg_archive_sha256_from_receipt": receipt["ffmpeg_archive_sha256"],
            "pyav_source_sha256_from_receipt": receipt["pyav_source_sha256"],
            "qt_webengine_present": qt_webengine,
            "chromium_notice_files_detected": chromium_notices,
            "ctranslate2_bundled_cudnn": [{"path": r["path"], "sha256": r["sha256"]} for r in cudnn],
            "smoke_clean_reinstall_uninstall": True,
            "upgrade_085_to_086": "verified separately in GitHub Actions 39598790616",
            "manual_gaps": gaps,
            "license_review_complete": False, "security_review_complete": False, "release_allowed": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit_archive(args.report_zip)
    except (EvidenceError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"QA evidence rejected (no release): {exc}\n")
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
