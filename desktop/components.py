"""Opt-in, pinned vendor downloads. No drivers, admin rights or system PATH edits."""
from __future__ import annotations
from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import uuid
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


def _reject_unsafe_path(path: Path, *, writable=False) -> None:
    try:
        info=path.lstat()
    except FileNotFoundError:
        return
    # Python 3.11 has no Path.is_junction. Reject all reparse points here.
    if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
        raise ValueError('Unsafe component link or reparse point: '+path.name)
    if writable and (not stat.S_ISREG(info.st_mode) or info.st_nlink>1):
        raise ValueError('Unsafe writable component file: '+path.name)


@contextmanager
def _package_lock(components: Path, name: str):
    path=components/('.'+name+'.lock')
    _reject_unsafe_path(path,writable=True)
    fd=os.open(path,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
    locked=False
    try:
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locked=True
        except OSError as exc:
            raise RuntimeError('Another setup is using this component') from exc
        yield
    finally:
        try:
            if locked:
                if os.name=='nt':
                    os.lseek(fd,0,os.SEEK_SET)
                    msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
                else:
                    fcntl.flock(fd,fcntl.LOCK_UN)
        finally:
            os.close(fd)


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
    _reject_unsafe_path(cache)
    archive = cache/(package.name+'.zip')
    _reject_unsafe_path(archive)
    if archive.is_file() and archive.stat().st_size == package.size and digest(archive,cancel) == package.sha256:
        return archive
    partial = archive.with_suffix('.partial')
    _reject_unsafe_path(partial,writable=True)
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), VendorRedirects())
    deadline = time.monotonic()+3600
    count = partial.stat().st_size if partial.is_file() else 0
    if count >= package.size:
        partial.unlink(missing_ok=True)
        count = 0
    headers={'User-Agent':'MeetingSplit-components','Accept-Encoding':'identity'}
    if count: headers['Range']=f'bytes={count}-'
    try:
        with opener.open(Request(package.url, headers=headers),timeout=20) as src:
            status=getattr(src,'status',200)
            if count and status == 206:
                expected=f'bytes {count}-{package.size-1}/{package.size}'
                if src.headers.get('Content-Range') != expected:
                    partial.unlink(missing_ok=True)
                    raise ValueError('Invalid component Content-Range; retry from zero')
            elif status == 200:
                count=0
            else:
                raise ValueError('Unexpected component HTTP response')
            with partial.open('ab' if count else 'wb') as dst:
                while True:
                    cancel.check()
                    if time.monotonic()>deadline: raise TimeoutError('Component download exceeded one hour; retry to resume setup.')
                    chunk = src.read(1024*1024)
                    if not chunk: break
                    count += len(chunk)
                    if count>package.size:
                        raise ValueError('Component exceeds its pinned size')
                    dst.write(chunk)
                    progress(f'{package.name}: {count//1048576} / {package.size//1048576} MiB')
        if count != package.size:
            raise OSError('Component download interrupted; retry to resume')
        if digest(partial,cancel) != package.sha256:
            raise ValueError('Component integrity verification failed: '+package.name)
        cancel.check()
        partial.replace(archive)
        return archive
    except ValueError:
        partial.unlink(missing_ok=True)
        raise
    finally:
        # Only strictly incomplete bytes may be reused; never install a partial.
        if partial.is_file() and not 0 < partial.stat().st_size < package.size:
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


def installed_inventory(folder: Path, cancel: Cancellation|None=None) -> dict:
    files={}
    _reject_unsafe_path(folder)
    for path in sorted(folder.rglob('*')):
        if cancel: cancel.check()
        _reject_unsafe_path(path)
        if path.is_file() and path!=folder/'meetingsplit-receipt.json':
            files[path.relative_to(folder).as_posix()]=digest(path,cancel)
    return files


def verify_installed(package: Package, folder: Path, cancel: Cancellation|None=None) -> None:
    _reject_unsafe_path(folder)
    validate_local_folder(folder)
    receipt=folder/'meetingsplit-receipt.json'
    _reject_unsafe_path(receipt)
    if not receipt.is_file() or receipt.is_symlink():
        raise ValueError('Component receipt missing; repair required: '+package.name)
    data=json.loads(receipt.read_text(encoding='utf-8'))
    if (data.get('sha256') != package.sha256 or not data.get('files')
            or data['files'] != installed_inventory(folder,cancel)):
        raise ValueError('Component integrity check failed; reinstall into a clean folder: '+package.name)


def install_package(package: Package, root: Path, progress, cancel: Cancellation, *, repair=False) -> Path:
    root = validate_local_folder(root)
    components = root/'Componentes'
    components.mkdir(exist_ok=True)
    _reject_unsafe_path(components)
    validate_local_folder(components)
    with _package_lock(components,package.name):
        return _install_locked(package,root,components,progress,cancel,repair)


def _install_locked(package, root, components, progress, cancel, repair):
    target=components/package.name
    _reject_unsafe_path(target)
    if target.exists():
        if not target.is_dir():
            raise ValueError('Component target is not a directory')
        try:
            verify_installed(package,target,cancel)
            return target
        except (ValueError,OSError) as exc:
            if not repair:
                raise ValueError('Component requires verified repair in Settings: '+package.name) from exc
            progress('Preparing verified replacement; existing component will be preserved: '+package.name)
    if shutil.disk_usage(root).free < package.size+5*1024**3:
        raise OSError('At least the download size plus 5 GiB free is required')
    cache=components/'Downloads'
    cache.mkdir(exist_ok=True)
    _reject_unsafe_path(cache)
    validate_local_folder(cache)
    archive=download(package,cache,progress,cancel)
    staging=Path(tempfile.mkdtemp(prefix='.stage-',dir=components))
    backup=None
    try:
        extract_verified(archive,staging,cancel)
        (staging/'meetingsplit-receipt.json').write_text(json.dumps({
            'name':package.name,'url':package.url,'sha256':package.sha256,
            'size':package.size,'files':installed_inventory(staging,cancel)},indent=2),encoding='utf-8')
        verify_installed(package,staging,cancel)
        cancel.check()
        if target.exists():
            if not repair:
                raise ValueError('Component appeared during setup; retry')
            _reject_unsafe_path(target)
            backup=components/('.backup-'+package.name+'-'+uuid.uuid4().hex)
            target.rename(backup)
        try:
            staging.rename(target)
        except BaseException:
            if backup is not None and not target.exists():
                backup.rename(target)
            raise
    finally:
        if staging.exists(): shutil.rmtree(staging)
    archive.unlink(missing_ok=True)
    if backup is not None:
        progress('Previous component preserved / Componente anterior conservado: '+backup.name)
    return target


def install_gpu(root: Path, progress, cancel: Cancellation, *, repair=False) -> None:
    for package in GPU_PACKAGES: install_package(package,root,progress,cancel,repair=repair)


def gpu_directories(root: Path) -> list[Path]:
    result=[]
    for package in GPU_PACKAGES:
        folder=root/'Componentes'/package.name
        if folder.is_dir():
            verify_installed(package,folder)
            result.extend(p for p in folder.rglob('bin') if p.is_dir())
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
