"""Per-installation local storage validation; do not use USB, network or cloud-sync outputs."""
from __future__ import annotations
import ctypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

_ALLOWED_BUS={"nvme", "sata", "ata", "sas", "scsi", "raid", "spaces"}
_BLOCKED_BUS={"usb", "sd", "mmc", "unknown", "virtual", "file backed virtual", "iscsi"}
_CLOUD_NAMES={"onedrive", "icloud drive", "icloud", "google drive", "dropbox"}


class UnsafeStorage(ValueError):
    pass


def classify_storage(drive_type: int, bus_type: str, *, is_system_drive: bool=False) -> tuple[bool,str]:
    """Windows: DRIVE_FIXED=3 alone is unsafe; many external USB SSDs also appear fixed."""
    if drive_type != 3:
        return False, "Solo se permiten unidades locales fijas; USB y unidades de red están bloqueadas."
    bus=(bus_type or '').strip().lower()
    if bus in _BLOCKED_BUS:
        return False, f"Unidad excluida: tipo de conexión {bus_type or 'desconocida'}."
    if bus in _ALLOWED_BUS:
        return True, "Unidad interna verificada"
    if is_system_drive and not bus:
        return True, "Unidad de sistema local; no se pudo consultar el tipo de bus"
    return False, "No se pudo confirmar que la unidad sea interna. Selecciona una unidad local verificada."


def _windows_drive_type(letter: str) -> int:
    return int(ctypes.windll.kernel32.GetDriveTypeW(f'{letter}:\\'))


def _windows_bus_type(letter: str) -> str:
    # Uses built-in Windows PowerShell Storage module. Only the drive letter is passed.
    cmd=(f"$p=Get-Partition -DriveLetter '{letter}' -ErrorAction Stop; "
         f"$d=$p | Get-Disk -ErrorAction Stop; $d.BusType")
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    try:
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],
                              text=True,capture_output=True,timeout=12,creationflags=flags,check=False)
    except (OSError,subprocess.TimeoutExpired):
        return ''
    return result.stdout.strip().splitlines()[-1].strip() if result.returncode == 0 and result.stdout.strip() else ''


def validate_local_folder(folder: Path) -> Path:
    target=Path(folder).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise UnsafeStorage('La ubicación seleccionada no es una carpeta.')
    if any(part.casefold() in _CLOUD_NAMES for part in target.parts):
        raise UnsafeStorage('Selecciona una carpeta local que no se sincronice con la nube.')
    if os.name == 'nt':
        drive=target.drive
        match=re.fullmatch(r'([A-Za-z]):',drive)
        if not match:
            raise UnsafeStorage('No se permiten rutas de red ni carpetas sin una unidad local.')
        letter=match.group(1).upper()
        system_drive=os.environ.get('SystemDrive','C:').upper()
        allowed,msg=classify_storage(_windows_drive_type(letter),_windows_bus_type(letter),
                                     is_system_drive=(drive.upper()==system_drive))
        if not allowed:
            raise UnsafeStorage(msg)
    return target


def configure_data_root(selected_parent: Path) -> Path:
    """Creates only the app's own subfolder under an explicitly user-selected folder."""
    parent=validate_local_folder(selected_parent)
    root=parent if parent.name.casefold() == 'meetingsplit' else parent/'MeetingSplit'
    root.mkdir(parents=True,exist_ok=True)
    # Test writeability before persisting; no audio files touched.
    try:
        with tempfile.NamedTemporaryFile(prefix='.ms-write-check-',dir=root,delete=True) as f:
            f.write(b'OK');f.flush()
    except OSError as exc:
        raise UnsafeStorage('Esta carpeta no permite escribir archivos. Selecciona otra ubicación.') from exc
    if shutil.disk_usage(root).free < 2*1024**3:
        raise UnsafeStorage('Se necesitan al menos 2 GB libres. Selecciona otra unidad con espacio.')
    return root
