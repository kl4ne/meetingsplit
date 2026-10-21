"""Opt-in, pinned vendor downloads. No drivers, admin rights or system PATH edits."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import time
from urllib.request import build_opener, HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request
from urllib.parse import urlsplit
from zipfile import ZipFile
from desktop.storage import validate_local_folder
from engine.control import Cancellation


@dataclass(frozen=True)
class Package:
    name: str
    url: str
    sha256: str
    size: int


CUDA_BASE = 'https://developer.download.nvidia.com/compute/cuda/redist/'
GPU_PACKAGES = (
    Package('cublas-12.4.5.8', CUDA_BASE+'libcublas/windows-x86_64/libcublas-windows-x86_64-12.4.5.8-archive.zip',
            '698140f12da055a3709eee2e022fcfe7bc8edf31f30115e3f7a5c877a9491de5', 391538487),
    Package('cudart-12.4.127', CUDA_BASE+'cuda_cudart/windows-x86_64/cuda_cudart-windows-x86_64-12.4.127-archive.zip',
            '6a1c32e68ee1a95ca17334691ff9ad1ffe7f352c24a083d55e4c96b8063b2bcb', 2474721),
    Package('nvrtc-12.4.127', CUDA_BASE+'cuda_nvrtc/windows-x86_64/cuda_nvrtc-windows-x86_64-12.4.127-archive.zip',
            'f140545e06d0d10780c1382a577db2e2c242db7a2d94970f0e6026b2d01aeb1b', 101865624),
    Package('cudnn-9.1.1.17', 'https://developer.download.nvidia.com/compute/cudnn/redist/cudnn/windows-x86_64/cudnn-windows-x86_64-9.1.1.17_cuda12-archive.zip',
            '3f1efb1a82e480594594e8b1fc8075a4852b4ada5a1fea3c8ec4b3ed1e5122ed', 669632100),
)
OLLAMA_PACKAGE = Package('ollama-0.40.6',
    'https://github.com/ollama/ollama/releases/download/v0.40.6/ollama-windows-amd64.zip',
    'e359637575302f288d76c0007c408a4be9c7376d59c4f28684d63b232a44b427',1471164488)


class VendorRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.hostname not in {
            'developer.download.nvidia.com', 'github.com', 'release-assets.githubusercontent.com',
            'objects.githubusercontent.com'}:
            raise ValueError('Untrusted component download redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def digest(path: Path, cancel: Cancellation | None = None) -> str:
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            if cancel: cancel.check()
            hasher.update(chunk)
    return hasher.hexdigest()


def download(package: Package, cache: Path, progress, cancel: Cancellation) -> Path:
    """Bounded streaming, check cancellation, verify size AND SHA before extraction."""
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache/(package.name+'.zip')
    if archive.is_file() and archive.stat().st_size == package.size and digest(archive,cancel) == package.sha256:
        return archive
    partial = archive.with_suffix('.partial')
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), VendorRedirects())
    deadline = time.monotonic()+3600
    count = 0
    try:
        with opener.open(Request(package.url, headers={'User-Agent':'MeetingSplit-components'}),timeout=20) as src, partial.open('wb') as dst:
            while True:
                cancel.check()
                if time.monotonic()>deadline: raise TimeoutError('Component download exceeded one hour; retry to resume setup.')
                chunk = src.read(1024*1024)
                if not chunk: break
                count += len(chunk)
                if count>package.size: raise ValueError('Component exceeds its pinned size')
                dst.write(chunk)
                progress(f'{package.name}: {count//1048576} / {package.size//1048576} MiB')
        if count != package.size or digest(partial,cancel) != package.sha256:
            raise ValueError('Component integrity verification failed: '+package.name)
        partial.replace(archive)
        return archive
    finally:
        partial.unlink(missing_ok=True)


def extract_verified(archive: Path, dest: Path, cancel: Cancellation) -> None:
    """Fresh staging folder only; reject Windows paths, links, duplicates and bombs."""
    seen = set()
    total = 0
    with ZipFile(archive) as zipfile:
        members = zipfile.infolist()
        if len(members)>25000: raise ValueError('Too many component files')
        for info in members:
            name = info.filename
            parts = PurePosixPath(name).parts
            key = name.casefold().rstrip('/')
            mode = info.external_attr >> 16
            if (not parts or name.startswith(('/', '\\')) or '\\' in name or ':' in name
                or any(p in ('..','.') or p.endswith((' ','.')) or re.match(r'(?i)^(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)',p) for p in parts)
                or key in seen or stat.S_ISLNK(mode)):
                raise ValueError('Unsafe component archive entry: '+name)
            seen.add(key)
            total += info.file_size
            if total>12*1024**3: raise ValueError('Component archive too large')
        if shutil.disk_usage(dest).free < total+512*1024**2:
            raise OSError('Insufficient disk space for component extraction')
        for info in members:
            cancel.check()
            target = dest.joinpath(*PurePosixPath(info.filename).parts)
            if info.is_dir(): target.mkdir(parents=True,exist_ok=True); continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.open(info) as src, target.open('xb') as dst:
                while chunk := src.read(1024*1024):
                    cancel.check(); dst.write(chunk)


def install_package(package: Package, root: Path, progress, cancel: Cancellation) -> Path:
    root = validate_local_folder(root)
    components = root/'Componentes'
    components.mkdir(exist_ok=True)
    validate_local_folder(components)
    target = components/package.name
    receipt = target/'meetingsplit-receipt.json'
    if receipt.is_file():
        data=json.loads(receipt.read_text(encoding='utf-8'))
        if data.get('sha256') == package.sha256: return target
    if target.exists(): raise ValueError('Incomplete component; choose another folder or repair: '+package.name)
    if shutil.disk_usage(root).free < package.size+5*1024**3:
        raise OSError('At least the download size plus 5 GiB free is required')
    archive=download(package, components/'Downloads', progress, cancel)
    staging=Path(tempfile.mkdtemp(prefix='.stage-',dir=components))
    try:
        extract_verified(archive,staging,cancel)
        (staging/'meetingsplit-receipt.json').write_text(json.dumps({
            'name':package.name,'url':package.url,'sha256':package.sha256,
            'size':package.size},indent=2),encoding='utf-8')
        cancel.check()
        staging.rename(target)
    finally:
        if staging.exists(): shutil.rmtree(staging)
    archive.unlink(missing_ok=True)
    return target


def install_gpu(root: Path, progress, cancel: Cancellation) -> None:
    for package in GPU_PACKAGES: install_package(package,root,progress,cancel)


def gpu_directories(root: Path) -> list[Path]:
    result=[]
    for package in GPU_PACKAGES:
        folder=root/'Componentes'/package.name
        if folder.is_dir(): result.extend(p for p in folder.rglob('bin') if p.is_dir())
    return result


_dll_handles=[]
_dll_dirs=set()


def activate_gpu(root: Path) -> None:
    """Per-process only; retain AddDllDirectory handles for all lazy native calls."""
    if os.name != 'nt': return
    root=validate_local_folder(root)
    for folder in gpu_directories(root):
        folder=validate_local_folder(folder)
        if str(folder) not in _dll_dirs:
            _dll_handles.append(os.add_dll_directory(str(folder)))
            _dll_dirs.add(str(folder))
