"""Offline checks for the exact original notice collection and frozen QA gate."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from qa.vendor_legal_manifest import check_frozen_notices, check_original_notices

SOURCE = Path(__file__).resolve().parents[1]/"docs"/"third-party-licenses"


@pytest.fixture
def copies(tmp_path):
    target = tmp_path/"third-party-licenses"
    shutil.copytree(SOURCE, target)
    return target


def test_all_original_notices_hash_and_release_remains_blocked():
    result = check_original_notices(SOURCE)
    assert result["notice_sha256_verified"]
    assert result["count"] >= 8
    assert any(x["file"] == "Chromium-140.0.7339.264-BSD-3-Clause.txt" for x in result["files"])
    assert result["release_allowed"] is False
    assert result["license_review_complete"] is False
    assert result["security_review_complete"] is False
    assert any("Chromium" in x for x in result["unresolved"])
    assert any("cuDNN" in x for x in result["unresolved"])


def test_notice_modified_without_receipt_update_rejected(copies):
    entry = json.loads((copies/"sources.json").read_text(encoding="utf-8"))[0]
    path = copies/entry["file"]
    path.write_bytes(path.read_bytes()+b"modified")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        check_original_notices(copies)


def test_notice_missing_rejected(copies):
    (copies/"Qt-6.12.0-LGPL-3.0.txt").unlink()
    with pytest.raises(ValueError, match="missing"):
        check_original_notices(copies)


def test_duplicate_case_insensitive_notice_rejected(copies):
    p = copies/"sources.json"
    records = json.loads(p.read_text(encoding="utf-8"))
    records.append({**records[0], "file": records[0]["file"].swapcase()})
    p.write_text(json.dumps(records),encoding="utf-8")
    with pytest.raises(ValueError,match="duplicated"):
        check_original_notices(copies)


def test_untrusted_notice_origin_rejected(copies):
    p = copies/"sources.json"
    records = json.loads(p.read_text(encoding="utf-8"))
    records[0]["source"] = "http://evil.example/forged.txt"
    p.write_text(json.dumps(records),encoding="utf-8")
    with pytest.raises(ValueError,match="origin"):
        check_original_notices(copies)


def test_frozen_notices_are_checked_against_actual_packaged_bytes(tmp_path):
    shipped = tmp_path/"frozen"/"_internal"/"docs"/"third-party-licenses"
    shutil.copytree(SOURCE, shipped)
    assert check_frozen_notices(tmp_path/"frozen")["count"] >= 7
    (shipped/"GPL-3.0.txt").write_bytes(b"not actual license")
    with pytest.raises(ValueError,match="mismatch"):
        check_frozen_notices(tmp_path/"frozen")


def test_build_hooks_invoke_manifest_before_distribution():
    root = Path(__file__).resolve().parents[1]
    collected = (root/"qa"/"collect_licenses.py").read_text(encoding="utf-8")
    audited = (root/"qa"/"audit_package.py").read_text(encoding="utf-8")
    assert "check_original_notices(ROOT/'docs'/'third-party-licenses')" in collected
    assert "check_frozen_notices(root)" in audited
    assert '"docs;docs"' in (root/"scripts"/"compilar_windows.bat").read_text(encoding="utf-8")
