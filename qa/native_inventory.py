"""Build an auditable, hash-pinned manifest of an actual frozen Windows package.

This is evidence for a human native-licensing/security review, NOT an approval
of redistribution or a vulnerability scan. No archive or installation is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

NATIVE_SUFFIXES = {'.dll', '.exe', '.pyd', '.so', '.dylib'}
FFMPEG_CONFIG_NAME = 'ffmpeg-build.txt'


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def classify_ffmpeg(build_log: str | None) -> dict[str, Any]:
    """Report build flags; do not guess licenses from FFmpeg version alone."""
    if not build_log:
        return {'configuration_found': False, 'flags': [],
                'issues': ['Exact FFmpeg configure flags unavailable: manual review required']}
    config = next((row.strip() for row in build_log.splitlines()
                   if re.match(r'^\s*configuration\s*:', row, re.I)), '')
    if not config:
        return {'configuration_found': False, 'flags': [],
                'issues': ['FFmpeg -version output lacked configuration: manual review required']}
    flags = re.findall(r'--[\w-]+(?:=[^\s]+)?', config)
    issues = []
    if '--enable-gpl' in flags:
        issues.append('FFmpeg build enables GPL: determine exact binary GPL duties and provide corresponding source/build information')
    if '--enable-nonfree' in flags:
        issues.append('FFmpeg build enables nonfree: do not distribute until incompatible license terms are resolved')
    if '--enable-version3' in flags:
        issues.append('FFmpeg build enables version3: review LGPLv3/GPLv3 obligations and dependencies')
    if '--disable-gpl' not in flags and '--enable-gpl' not in flags:
        issues.append('FFmpeg GPL configuration not explicit; inspect linked libraries and actual license')
    return {'configuration_found': True, 'flags': sorted(set(flags)), 'issues': issues}


def inventory_package(package_root: Path, *, legal_root: Path | None = None) -> dict[str, Any]:
    package_root = Path(package_root).resolve(strict=True)
    if not package_root.is_dir():
        raise ValueError('Frozen package root must be a directory')
    if not (package_root/'MeetingSplit.exe').is_file():
        raise ValueError('Frozen package must contain MeetingSplit.exe')
    files = []
    total_size = 0
    for file in sorted(package_root.rglob('*')):
        if file.is_symlink():
            raise ValueError('Unexpected symbolic link in frozen package: '+str(file.relative_to(package_root)))
        if not file.is_file():
            continue
        relative = file.relative_to(package_root).as_posix()
        # Never include a developer path or file contents in this record.
        size = file.stat().st_size
        files.append({'path': relative, 'bytes': size, 'sha256': hash_file(file),
                      'native': file.suffix.casefold() in NATIVE_SUFFIXES})
        total_size += size
    names = {row['path'].casefold() for row in files}
    collisions = len(names) != len(files)
    if collisions:
        raise ValueError('Frozen package contains duplicate Windows case-insensitive paths')
    legal = legal_root or (package_root/'_internal'/'legal')
    ffmpeg_log = (legal/FFMPEG_CONFIG_NAME)
    build_log = ffmpeg_log.read_text(encoding='utf-8',errors='replace') if ffmpeg_log.is_file() else None
    ffmpeg = classify_ffmpeg(build_log)
    ffmpeg['log_in_package'] = ffmpeg_log.is_relative_to(package_root) if ffmpeg_log.is_file() else False
    ffmpeg['log_sha256'] = hash_file(ffmpeg_log) if ffmpeg_log.is_file() else None
    flags = ['Native Qt, PyAV/FFmpeg, CTranslate2, Chromium and model redistribution review not yet signed off']
    flags.extend(ffmpeg['issues'])
    if not ffmpeg['log_in_package']:
        flags.append('FFmpeg build log not verifiably included in frozen package')
    return {
        'schema': 1, 'product': 'MeetingSplit', 'inventory_scope': 'actual frozen package',
        'files': files, 'file_count': len(files),
        'native_file_count': sum(row['native'] for row in files),
        'package_bytes': total_size, 'ffmpeg': ffmpeg,
        'license_review_complete': False, 'security_review_complete': False,
        'release_allowed': False, 'manual_review_flags': flags,
        'disclaimer': 'Hash inventory and FFmpeg flags are evidence only; they do not establish GPL/LGPL compliance or software safety.'
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package_root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    report = inventory_package(args.package_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f"Native inventory recorded: {report['file_count']} files / {report['native_file_count']} native binaries. Release remains blocked.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())