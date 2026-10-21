## MeetingSplit v0.8.6 — Windows CI SUCCESS
- Github Actions run #39537216562: https://github.com/kl4ne/meetingsplit/actions/runs/39537216562
- **37 tests PASSED, 1 skipped** in Windows (job ran tests twice); PyInstaller EXE self-check passed; portable ZIP and Setup EXE verified; upload-artifact completed.
- Artifact ID **12317478170**: `MeetingSplit-v0.8.6-Windows-build-unvalidated-on-user-hardware` (~654 MB, retention 14 days).
- Large readable typography (+2 scale steps) across all five EN/ES pages published. Acceptance on ASUS Windows hardware remains pending; this is still a development build, not a production Release.
- User confirmed v0.8.5: internal D: accepted, CPU fallback transcribed six clips correctly in ~11 minutes, GPU CUDA 12 library missing. No changes to working audio engine in v0.8.6.

## VERIFIED USER ACCEPTANCE — MeetingSplit v0.8.5 (2026-10-20)
- User confirmed internal D: was ACCEPTED.
- User confirmed all six audio segments were successfully transcribed on CPU, taking approximately 11 minutes.
- Windows CUDA acceleration is still unavailable because cublas64_12.dll cannot load; CPU fallback works. No GPU fix claimed.
- User requested that all UI fonts be TWO STEPS LARGER, on every screen. v0.8.6 implements only layout/typography and version metadata, preserving working audio functions and storage security.
- Chromium QA visually checked five EN/ES screens at 1366x768, 1440x900, 1920x1080, 2560x1440. Windows CI and ASUS approval pending.

## v0.8.6 typography checkpoint
- User confirmed v0.8.5 accepted internal D: and transcribed 6 audio segments on CPU successfully in approximately 11 minutes.
- CUDA 12 is still missing cublas64_12.dll; fallback is functional but GPU acceleration is not fixed.
- User requested ALL UI letters two typographic steps larger, implemented in CSS for v0.8.6. Pending Windows CI and visual acceptance.

# MeetingSplit v0.8.5 — Checkpoint

User-reported v0.8.4 behavior: D: rejected after slow check; GPU DLL failure recovered to CPU but stayed on transcription 1/6 for a long period; Start Processing gave inadequate immediate feedback. Split-only mode succeeds.

The v0.8.5 source modifies storage querying, CPU performance mode and visual feedback. Actual acceptance on user ASUS is NOT yet confirmed. CUDA acceleration is not repaired; it is deliberately avoided when missing libraries.

Next: GitHub Windows CI, inspect build artifact, then verify C: and D: drives on ASUS, CPU transcript (2–5 min) and spinner/timer. Do not allow USB J: or synced folders; no Integrity modifications.

# MeetingSplit — MASTER_STATUS

**Version in development:** 0.8.5. **Repository:** public `kl4ne/meetingsplit`, `main`.

## Verified from previous run
- GitHub Actions run #39522806473 built v0.8.3 Windows portable and installer successfully. GitHub self-check/CI passed, but ASUS testing exposed two runtime issues.
- On ASUS Windows 11, internal D: selection was rejected; C: selection inside a cloud sync folder was rejected; C: root subfolder worked. The original drive verifier relied too heavily on `Get-Partition | Get-Disk`.
- ASUS CUDA transcription failed with `Library cublas64_12.dll is not found or cannot be loaded` after processing began.

## New v0.8.5 corrections awaiting hardware confirmation
- Use Windows CIM to classify drive D: if Storage module lacks BusType, with USB/PNP override and no network/USB exceptions.
- LocalAppData is starting folder for chooser; OneDrive/Google Drive remain intentionally excluded.
- GPU DLL preflight and lazy CUDA runtime failure retry via CPU, preserving transcript integrity.
- Unit and integration regressions added. Check GitHub CI before claiming Windows acceptance.

## Gates
- Build and verify v0.8.5 GitHub Actions.
- Validate D: selection and C: non-synced folder on actual ASUS; confirm removable J: is rejected.
- Validate GPU preflight CPU fallback without missing cublas error, then evaluate legitimate CUDA 12/cuDNN 9 installation for GPU.
- Validate actual transcriptions, model download, installer, 1–3h runs, license notices. No public Release until then.
- Do not touch Integrity Business Filings; do not upload audio or credentials to GitHub.
