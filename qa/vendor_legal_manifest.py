"""Verify exact upstream notice bytes already checked into MeetingSplit.

This is a build-integrity control, not a legal clearance, network lookup,
source-offer, or a reason to change qa/release_gate.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REQUIRED_SOURCE_NOTICES = frozenset({
    "CTranslate2-4.6.2-MIT.txt",
    "Qt-6.12.0-LGPL-3.0.txt",
    "GPL-3.0.txt",
    "FFmpeg-LGPL-2.1.txt",
    "Tokenizers-0.23.3-Apache-2.0.txt",
    "Cython-3.3.0-Apache-2.0.txt",
    "Cython-3.3.0-Pyrex-COPYING.txt",
})
UNRESOLVED = (
    "Qt WebEngine/Chromium: matching binary version, complete third-party notices and LGPL source/relinking rights",
    "FFmpeg/PyAV: all linked native licenses, matching source/build instructions and LGPL obligations",
    "CTranslate2 cuDNN: packaged bytes match official PyPI 4.6.2 wheel (run #39698897754); exact NVIDIA DLL version, governing SDK license and required notices/approval still outstanding",
    "Qt/PySide6: matching LGPL libraries, usable corresponding source, replacement/reverse-engineering rights",
    "Native vulnerability assessment and qualified license review of exact final build",
)


def check_original_notices(notice_root: Path) -> dict:
    """Fail closed on altered bytes, missing required files and unsafe receipts."""
    root = Path(notice_root)
    receipt = root / "sources.json"
    if not receipt.is_file() or receipt.is_symlink():
        raise ValueError("Pinned legal notice receipt index is missing or unsafe")
    entries = json.loads(receipt.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or len(entries) > 200:
        raise ValueError("Invalid legal notice receipt index")
    seen = set()
    verified = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid source-notice receipt")
        name = entry.get("file")
        expected = entry.get("sha256")
        url = entry.get("source")
        if (not isinstance(name, str) or not name or Path(name).name != name
                or "/" in name or "\\" in name or name.casefold() in seen):
            raise ValueError("Unsafe or duplicated legal notice path")
        if (not isinstance(url, str) or not url.startswith("https://raw.githubusercontent.com/")
                or "?" in url or "#" in url):
            raise ValueError("Unpinned or non-upstream legal notice origin")
        if (not isinstance(expected, str) or len(expected) != 64
                or any(ch not in "0123456789abcdef" for ch in expected)):
            raise ValueError("Invalid SHA-256 legal notice receipt")
        seen.add(name.casefold())
        file = root / name
        if not file.is_file() or file.is_symlink() or not file.stat().st_size:
            raise ValueError("Required upstream legal notice missing: " + name)
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("Upstream legal notice SHA-256 mismatch: " + name)
        verified.append({"file": name, "sha256": actual, "source": url})
    absent = sorted(REQUIRED_SOURCE_NOTICES - {v["file"] for v in verified})
    if absent:
        raise ValueError("Uncollected original notices: " + ", ".join(absent))
    return {
        "schema": 1,
        "notice_sha256_verified": True,
        "count": len(verified),
        "files": sorted(verified, key=lambda v: v["file"]),
        "license_review_complete": False,
        "security_review_complete": False,
        "release_allowed": False,
        "unresolved": list(UNRESOLVED),
        "caveat": "Hashing exact upstream notice copies neither proves native matching nor satisfies LGPL source and redistribution duties."
    }


def check_frozen_notices(frozen_root: Path) -> dict:
    frozen = Path(frozen_root)
    notice_root = frozen / "_internal" / "docs" / "third-party-licenses"
    return check_original_notices(notice_root)
