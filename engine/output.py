"""Readable timecoded exports and deterministic local bundle packaging."""
from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED
from .control import Cancellation


def clock_srt(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    h, remainder = divmod(milliseconds, 3600000)
    m, remainder = divmod(remainder, 60000)
    s, ms = divmod(remainder, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def format_srt(rows: list[dict]) -> str:
    pieces = []
    for i, row in enumerate(rows, 1):
        if not row.get('text','').strip():
            continue
        start = max(0.0, float(row['start']))
        end = max(start + .1, float(row['end']))
        pieces.append(f'{i}\n{clock_srt(start)} --> {clock_srt(end)}\n{row["text"].strip()}\n')
    return '\n'.join(pieces) + ('\n' if pieces else '')


def pack_result(folder: Path, target: Path, cancel: Cancellation|None=None) -> dict:
    """ZIP is stored (audio is already compressed), assembled with atomic replacement."""
    tmp = target.with_suffix('.zip.partial')
    try:
        with ZipFile(tmp, 'w', ZIP_STORED, allowZip64=True) as zipped:
            for path in sorted(folder.iterdir()):
                if cancel: cancel.check()
                if path.is_file() and not path.name.startswith('.') and path.name != target.name and not path.name.endswith('.partial'):
                    zipped.write(path, arcname=path.name)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return {'name': target.name, 'bytes': target.stat().st_size}
