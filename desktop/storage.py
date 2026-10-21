"""Validate user-selected data folders without trusting fixed USB disks or cloud folders."""
from __future__ import annotations
import ctypes
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


def _windows_bus_type(letter: str) -> str:
    """First ask Storage for BusType, then CIM for systems where Get-Disk fails.

    Cross-check a PnP USB identifier even when the Storage provider reports
    SCSI/RAID. Never approve a disk based solely on DRIVE_FIXED.
    """
    if not re.fullmatch(r"[A-Za-z]", letter):
        return ""
    command = r'''$ErrorActionPreference = 'Stop'
$bus = ''
try {
  $part = Get-Partition -DriveLetter '__LETTER__' -ErrorAction Stop
  $disk = $part | Get-Disk -ErrorAction Stop
  $bus = [string]$disk.BusType
} catch { $bus = '' }
try {
  $ld = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='__LETTER__:'" -ErrorAction Stop
  if ($ld) {
    $part = Get-CimAssociatedInstance -InputObject $ld -ResultClassName Win32_DiskPartition -ErrorAction Stop | Select-Object -First 1
    if ($part) {
      $physical = Get-CimAssociatedInstance -InputObject $part -ResultClassName Win32_DiskDrive -ErrorAction Stop | Select-Object -First 1
      if ($physical) {
        $pnp = [string]$physical.PNPDeviceID
        $interface = [string]$physical.InterfaceType
        if ($interface -eq 'USB' -or $pnp -match 'USBSTOR|UASPSTOR|(^USB\\)|(^SD\\)|(^1394\\)|&VEN_USB|&PROD_USB') {
          $bus = 'USB'
        } elseif ($pnp -match 'ISCSI|VIRTUAL|VHD|FILEBACKED') {
          $bus = 'Virtual'
        } elseif ($bus -eq '' -or $bus -eq 'Unknown') {
          if ($pnp -match 'NVME|NVM EXPRESS') { $bus = 'NVMe' }
          elseif ($interface -in @('IDE', 'ATA')) { $bus = 'ATA' }
          elseif ($interface -in @('SCSI', 'SAS')) { $bus = 'SCSI' }
          elseif ($interface -eq 'PCI') { $bus = 'PCI' }
        }
      }
    }
  }
} catch { }
Write-Output $bus'''.replace('__LETTER__', letter.upper())
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            text=True, capture_output=True, timeout=18,
            creationflags=flags, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip().splitlines()[-1].strip() if result.returncode == 0 and result.stdout.strip() else ""


def validate_local_folder(folder: Path) -> Path:
    target = Path(folder).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise UnsafeStorage("La ubicación seleccionada no es una carpeta.")
    if any(part.casefold() in _CLOUD_NAMES for part in target.parts):
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
    try:
        with tempfile.NamedTemporaryFile(prefix=".ms-write-check-", dir=root, delete=True) as f:
            f.write(b"OK")
            f.flush()
    except OSError as exc:
        raise UnsafeStorage("Esta carpeta no permite escribir archivos. Selecciona otra ubicación.") from exc
    if shutil.disk_usage(root).free < 2 * 1024**3:
        raise UnsafeStorage("Se necesitan al menos 2 GB libres. Selecciona otra unidad con espacio.")
    return root
