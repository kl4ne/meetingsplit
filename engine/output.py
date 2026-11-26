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


def _archive_path(path: Path) -> str:
    name = path.name
    extension = path.suffix.casefold()
    if extension == '.json':
        folder = 'Datos_JSON'
    elif name in ('RESUMEN_Y_MINUTA_LOCAL.md', 'MINUTA_NO_GENERADA.txt'):
        folder = 'Minutas'
    elif name.startswith('parte_') and extension in ('.mp3', '.m4a', '.wav'):
        folder = 'Audio'
    elif name.casefold().startswith('transcripci') and extension in ('.txt', '.srt'):
        folder = 'Transcripciones'
    elif name.startswith('INSTRUCCIONES_'):
        folder = 'Instrucciones'
    else:
        folder = 'Otros'
    return f'{folder}/{name}'


def pack_result(folder: Path, target: Path, cancel: Cancellation|None=None) -> dict:
    """ZIP is stored (audio is already compressed), assembled with atomic replacement."""
    tmp = target.with_suffix('.zip.partial')
    try:
        with ZipFile(tmp, 'w', ZIP_STORED, allowZip64=True) as zipped:
            directories = set()
            for path in sorted(folder.iterdir()):
                if cancel: cancel.check()
                if path.is_file() and not path.is_symlink() and not path.name.startswith('.') and path.name != target.name and not path.name.endswith('.partial'):
                    member = _archive_path(path)
                    directory = member.split('/', 1)[0] + '/'
                    if directory not in directories:
                        zipped.mkdir(directory)
                        directories.add(directory)
                    with path.open('rb') as source, zipped.open(member,'w',force_zip64=True) as sink:
                        while chunk := source.read(1024*1024):
                            if cancel: cancel.check()
                            sink.write(chunk)
        if cancel: cancel.check()
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return {'name': target.name, 'bytes': target.stat().st_size}
