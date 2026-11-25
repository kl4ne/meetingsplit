"""Validate user-selected data folders without trusting fixed USB disks or cloud folders."""
from __future__ import annotations
import ctypes
import json
import stat
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

_ALLOWED_BUS = {"nvme", "sata", "ata", "sas", "scsi", "raid", "spaces", "pci"}
_BLOCKED_BUS = {"usb", "sd", "mmc", "unknown", "virtual", "file backed virtual", "iscsi", "1394"}
_CLOUD_NAMES = {"onedrive", "icloud drive", "icloud", "google drive", "dropbox"}


class UnsafeStorage(ValueError):
    pass


def classify_storage(drive_type: int, bus_type: str, *, is_system_drive: bool = False) -> tuple[bool, str]:
    """DRIVE_FIXED alone is insufficient: external USB SSDs often report fixed."""
    if drive_type != 3:
        return False, "Solo se permiten unidades locales fijas; USB y unidades de red están bloqueadas."
    bus = (bus_type or "").strip().lower()
    if bus in _BLOCKED_BUS:
        return False, f"Unidad excluida: tipo de conexión {bus_type or 'desconocida'}."
    if bus in _ALLOWED_BUS:
        return True, "Unidad interna verificada"
    if is_system_drive and not bus:
        return True, "Unidad de sistema local; no se pudo consultar el tipo de bus"
    return False, (
        "No se pudo confirmar que la unidad sea interna. "
        "No se autorizarán discos USB por error. "
        "Prueba una carpeta en C: fuera de OneDrive o Google Drive."
    )


def _windows_drive_type(letter: str) -> int:
    return int(ctypes.windll.kernel32.GetDriveTypeW(f"{letter}:\\"))


def _native_windows_bus_type(letter: str) -> str:
    """Fast Windows volume-to-physical-device query (no PowerShell or admin needed).

    Fail closed on a query error. A fixed USB SSD must never be accepted
    merely because GetDriveType reports DRIVE_FIXED.
    """
    if os.name != 'nt' or not re.fullmatch(r'[A-Za-z]', letter):
        return ''
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                   ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                                      wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                                      ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    kernel.DeviceIoControl.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    invalid = ctypes.c_void_p(-1).value

    def open_device(path):
        handle = kernel.CreateFileW(path, 0, 7, None, 3, 0, None)
        if handle is None or handle == invalid:
            raise OSError(ctypes.get_last_error(), 'Windows storage device unavailable')
        return handle

    def ioctl(handle, code, request, result_size):
        result = ctypes.create_string_buffer(result_size)
        returned = wintypes.DWORD()
        if not kernel.DeviceIoControl(handle, code, request, 0 if request is None else len(request),
                                      result, result_size, ctypes.byref(returned), None):
            raise OSError(ctypes.get_last_error(), 'Windows storage query failed')
        return result.raw[:returned.value]

    bus_codes = {1:'SCSI', 2:'ATA', 3:'ATA', 4:'1394', 7:'USB',
                 8:'RAID', 9:'iSCSI', 10:'SAS', 11:'SATA', 12:'SD',
                 13:'MMC', 14:'Virtual', 15:'Virtual', 16:'Spaces',
                 17:'NVMe', 18:'PCI', 19:'ATA'}
    try:
        volume = open_device(r'\\.' + '\\' + letter.upper() + ':')
        try:
            # IOCTL_STORAGE_GET_DEVICE_NUMBER = CTL_CODE(FILE_DEVICE_MASS_STORAGE, 0x420, 0, 0)
            info = ioctl(volume, 0x002D1080, None, 12)
            if len(info) < 12:
                return ''
            disk_number = int.from_bytes(info[4:8], 'little')
            if disk_number == 0xFFFFFFFF:
                return ''
        finally:
            kernel.CloseHandle(volume)
        disk = open_device(r'\\.\PhysicalDrive' + str(disk_number))
        try:
            # STORAGE_PROPERTY_QUERY: StorageDeviceProperty / PropertyStandardQuery
            request = ctypes.create_string_buffer(12)
            buffer = ctypes.create_string_buffer(256)
            returned = wintypes.DWORD()
            if not kernel.DeviceIoControl(disk, 0x002D1400, request, len(request),
                                          buffer, len(buffer), ctypes.byref(returned), None):
                return ''
            if returned.value < 36:
                return ''
            bus_id = int.from_bytes(buffer.raw[28:32], 'little')
            return bus_codes.get(bus_id, '')
        finally:
            kernel.CloseHandle(disk)
    except (OSError, ValueError):
        return ''


def _windows_bus_type(letter: str) -> str:
    """Fast native detection first; bounded PowerShell fallback if unavailable.

    External USB disks must remain blocked even when marked DRIVE_FIXED.
    """
    if not re.fullmatch(r'[A-Za-z]', letter):
        return ''
    native = _native_windows_bus_type(letter)
    if native:
        return native
    # Legacy query for unusual disk controllers; four-second absolute cap.
    command = r'''$ErrorActionPreference = 'Stop'
try {
  $part = Get-Partition -DriveLetter '__LETTER__' -ErrorAction Stop
  $disk = $part | Get-Disk -ErrorAction Stop
  [string]$disk.BusType
} catch { '' }'''.replace('__LETTER__', letter.upper())
    try:
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
            text=True, capture_output=True, timeout=4,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0), check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ''
    if result.returncode != 0 or not result.stdout.strip():
        return ''
    return result.stdout.strip().splitlines()[-1].strip()


def _configured_sync_roots() -> list[Path]:
    roots=[Path(value).expanduser() for key in ('OneDrive','OneDriveConsumer','OneDriveCommercial')
           if (value:=os.environ.get(key))]
    for key in ('APPDATA','LOCALAPPDATA'):
        if value:=os.environ.get(key):
            try:
                data=json.loads((Path(value)/'Dropbox'/'info.json').read_text(encoding='utf-8'))
                roots.extend(Path(item['path']) for item in data.values()
                             if isinstance(item,dict) and isinstance(item.get('path'),str))
            except (OSError,ValueError,AttributeError):
                pass
    if os.name=='nt':
        import winreg
        for hive,path,field in (
            (winreg.HKEY_CURRENT_USER,r'Software\Microsoft\OneDrive\Accounts','UserFolder'),
            (winreg.HKEY_CURRENT_USER,r'Software\SyncEngines\Providers','MountPoint'),
        ):
            try:
                with winreg.OpenKey(hive,path) as parent:
                    for i in range(winreg.QueryInfoKey(parent)[0]):
                        with winreg.OpenKey(parent,winreg.EnumKey(parent,i)) as child:
                            try:
                                value,_=winreg.QueryValueEx(child,field)
                                if isinstance(value,str) and value: roots.append(Path(value))
                            except OSError:
                                continue
            except OSError:
                pass
    return roots


def _has_cloud_attributes(path: Path) -> bool:
    mask=(getattr(stat,'FILE_ATTRIBUTE_OFFLINE',0x1000)|0x40000|0x400000)
    return any(getattr(parent.stat(),'st_file_attributes',0)&mask
               for parent in (path,*path.parents))


def validate_local_folder(folder: Path) -> Path:
    target = Path(folder).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise UnsafeStorage("La ubicación seleccionada no es una carpeta.")
    configured_cloud=any(target.is_relative_to(root.resolve()) for root in _configured_sync_roots())
    if configured_cloud or (os.name=='nt' and _has_cloud_attributes(target)) or any(part.casefold() in _CLOUD_NAMES or part.casefold().startswith('onedrive - ') for part in target.parts):
        raise UnsafeStorage(
            "Esa carpeta está dentro de OneDrive, Google Drive u otra nube. "
            "Selecciona C:\\MeetingSplit o una carpeta en un disco interno, "
            "no Escritorio/Documentos si se sincronizan con la nube."
        )
    if os.name == "nt":
        drive = target.drive
        match = re.fullmatch(r"([A-Za-z]):", drive)
        if not match:
            raise UnsafeStorage("No se permiten rutas de red ni carpetas sin una unidad local.")
        letter = match.group(1).upper()
        system_drive = os.environ.get("SystemDrive", "C:").upper()
        allowed, msg = classify_storage(
            _windows_drive_type(letter), _windows_bus_type(letter),
            is_system_drive=(drive.upper() == system_drive),
        )
        if not allowed:
            raise UnsafeStorage(msg)
    return target


def configure_data_root(selected_parent: Path) -> Path:
    """Make the application folder only under a deliberately selected directory."""
    parent = validate_local_folder(selected_parent)
    root = parent if parent.name.casefold() == "meetingsplit" else parent / "MeetingSplit"
    root.mkdir(parents=True, exist_ok=True)
    root = validate_local_folder(root)
    try:
        with tempfile.NamedTemporaryFile(prefix=".ms-write-check-", dir=root, delete=True) as f:
            f.write(b"OK")
            f.flush()
    except OSError as exc:
        raise UnsafeStorage("Esta carpeta no permite escribir archivos. Selecciona otra ubicación.") from exc
    if shutil.disk_usage(root).free < 2 * 1024**3:
        raise UnsafeStorage("Se necesitan al menos 2 GB libres. Selecciona otra unidad con espacio.")
    return root
