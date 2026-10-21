# Redistribution and security review — release HOLD

No new version or Release is authorized until all required QA is evaluated. A
successful source test or development installer compilation is not release approval.

The base package uses dynamically linked PySide6/Qt, Faster-Whisper, CTranslate2,
PyAV/FFmpeg and other Python distributions. `qa/collect_licenses.py` preserves their
available original notices and exact installed metadata in `build/legal`, included
in the packaged app. Optional NVIDIA/Ollama archives are fetched separately and
retained in the selected data folder with their own notices and hash receipts.

Outstanding checks before distribution:

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
