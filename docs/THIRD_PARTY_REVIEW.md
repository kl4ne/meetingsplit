## 2026-10-21: confirmed package-level GPL indicators

Windows QA evidence: `docs/QA_CONSOLIDATED_2026-10-21.md`.
Exact included `ffmpeg.exe` and `ffprobe.exe` are FFmpeg 9.0.2 Gyan
essentials builds with `--enable-gpl` and `--enable-version3`.
The PyAV Windows wheel separately includes `libx264` and `libx265` DLLs
in `av.libs`; licensing the PyAV Python wrapper under BSD does not
override the licenses of its native libraries. Thus simply adding a
generic FFmpeg LGPL notice is **not enough**. Either establish the precise
GPL compliance path and corresponding source for these binaries (including
the combined-work assessment) or replace with vetted LGPL configurations
and re-run QA. Do not assume this automatically relicenses MeetingSplit's
original standalone code. Seek qualified legal review before public
distribution. Release gate stays closed.

# Redistribution and security review — release HOLD

No new version or Release is authorized until all required QA is evaluated. A
successful source test or development installer compilation is not release approval.

The base package uses dynamically linked PySide6/Qt, Faster-Whisper, CTranslate2,
PyAV/FFmpeg and other Python distributions. `qa/collect_licenses.py` preserves their
available original notices and exact installed metadata in `build/legal`, included
in the packaged app. Optional NVIDIA/Ollama archives are fetched separately and
retained in the selected data folder with their own notices and hash receipts.

## Development-only native package evidence (not release approval)

`qa/native_inventory.py` now produces `build/native-inventory.json` only
after an actual PyInstaller output exists. It records every frozen file's
relative path, SHA-256, size and native binary classification. It also reads
the included `_internal/legal/ffmpeg-build.txt` and flags an FFmpeg build
with `--enable-gpl`, `--enable-version3`, `--enable-nonfree` or missing
configuration information. The separate QA artifact retains this manifest.

A checksum list is **not** a native security/vulnerability audit, a provenance
attestation or license clearance. The report explicitly records
`release_allowed: false` and `license_review_complete: false`; neither can
be automatically promoted to true. Native origin, Qt/Chromium notices,
FFmpeg/PyAV build-specific source obligations, LGPL replaceability and
Qwen/Ollama/NVIDIA notices still require review against actual shipped bytes.
A new QA installer build is **not** authorized by introducing this script.

Outstanding checks before distribution:

- Wheel metadata alone was insufficient: CTranslate2 4.6.2 contained no original
  license file, and the installed PySide6 wheels only supplied the commercial
  notice despite declaring LGPL/GPL alternatives. Original CTranslate2 MIT,
  Qt LGPLv3/GPLv3 and FFmpeg LGPLv2.1 texts are now preserved separately under
  `docs/third-party-licenses`, with upstream URLs and SHA-256 receipts. These
  texts do not substitute for the full native dependency notices or matching source.

- Local frozen-package investigation found the generic Qt QML hooks collected unused
  Charts/Graphs/Quick3D/VirtualKeyboard modules. Application-specific hooks exclude
  application QML plugins, QML debugging and virtual keyboard; `qa/audit_package.py`
  rejects these native modules. This is a narrow package check, not full LGPL/GPL
  compliance approval. Preserve required Qt WebEngine/Quick dependencies and test
  actual frozen rendering after any hook change.
- Build PATH is scoped to the venv, bundled tools and Windows for this process only.
  The host's unrelated Poppler ICU DLL previously shadowed Windows ICU and broke
  QtCore imports in the local frozen app. No host PATH or system DLLs were changed.

- Audit the exact frozen dependency inventory and vulnerability scan, including native
  Qt, FFmpeg/PyAV and CTranslate2 binaries. A pip-only scan does not cover all native code.
- Review LGPL obligations for Qt/PySide6, including dynamic library replacement,
  reverse engineering allowances, notices and matching source availability. MeetingSplit's
  proprietary license must not restrict rights granted by those separate libraries.
- Determine exact FFmpeg build configuration. The pre-existing workflow downloads a
  Chocolatey FFmpeg build, which can enable GPL components. Capture `-version` output,
  preserve license text and provide corresponding source/build materials appropriate
  to the exact shipped binary. A generic source URL alone does not close this gate.
- Check PyAV's bundled FFmpeg licenses independently from the separate CLI executables.
- Review NVIDIA's redistribution lists/EULAs and retain archives' notices. The base
  package does not redistribute NVIDIA runtimes or install drivers. Vendor downloading
  is opt-in and checksum pinned; system library replacement is prohibited.
- Retain Ollama runtime/native dependency notices and exact Qwen model license/digest.
  Review the synthetic generated minutes for invented facts and truncation. Local
  generation completion is not a factual-accuracy certificate.
- Test installer clean/upgrade/cancel/uninstall and component retry/disk-full behavior,
  EN/ES UI and all existing disk restrictions on actual Windows. Components/models in
  the user-selected data folder survive base uninstall; disclose this explicitly.
- Assess signing/SmartScreen separately. No claim of removed Windows warnings is made.

Official references:
https://doc.qt.io/qt-6/licensing.html
https://ffmpeg.org/legal.html
https://docs.nvidia.com/cuda/eula/index.html
https://docs.nvidia.com/deeplearning/cudnn/backend/v9.1.1/installation/windows.html
https://github.com/ollama/ollama/blob/v0.40.6/LICENSE
https://ollama.com/library/qwen3:4b
