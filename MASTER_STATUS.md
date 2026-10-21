# MeetingSplit — MASTER_STATUS

**Version in development:** 0.8.4. **Repository:** public `kl4ne/meetingsplit`, `main`.

## Verified from previous run
- GitHub Actions run #39522806473 built v0.8.3 Windows portable and installer successfully. GitHub self-check/CI passed, but ASUS testing exposed two runtime issues.
- On ASUS Windows 11, internal D: selection was rejected; C: selection inside a cloud sync folder was rejected; C: root subfolder worked. The original drive verifier relied too heavily on `Get-Partition | Get-Disk`.
- ASUS CUDA transcription failed with `Library cublas64_12.dll is not found or cannot be loaded` after processing began.

## New v0.8.4 corrections awaiting hardware confirmation
- Use Windows CIM to classify drive D: if Storage module lacks BusType, with USB/PNP override and no network/USB exceptions.
- LocalAppData is starting folder for chooser; OneDrive/Google Drive remain intentionally excluded.
- GPU DLL preflight and lazy CUDA runtime failure retry via CPU, preserving transcript integrity.
- Unit and integration regressions added. Check GitHub CI before claiming Windows acceptance.

## Gates
- Build and verify v0.8.4 GitHub Actions.
- Validate D: selection and C: non-synced folder on actual ASUS; confirm removable J: is rejected.
- Validate GPU preflight CPU fallback without missing cublas error, then evaluate legitimate CUDA 12/cuDNN 9 installation for GPU.
- Validate actual transcriptions, model download, installer, 1–3h runs, license notices. No public Release until then.
- Do not touch Integrity Business Filings; do not upload audio or credentials to GitHub.
