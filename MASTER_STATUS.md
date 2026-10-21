# MeetingSplit — MASTER_STATUS

**Source checkpoint:** v0.8.3. **Repository:** public `kl4ne/meetingsplit`, `main`.

## Confirmed
- Public repo initialized with source, bilingual README, custom freeware `LICENSE`, privacy-safe ignores, tests, and GitHub Actions.
- Default English UI; selectable Spanish; independent screens; contrasting luxury visuals; non-linked author credit and copyright.
- Voluntary PayPal contribution uses the direct user-provided NCP URL; no payment SDK loads in local audio processing.
- 26 selected local tests passed prior to publication.
- Initial Windows CI run #39522565477 failed because Chocolatey FFmpeg shim files were copied instead of actual binaries.
- FFmpeg packaging repaired in commit `f6df551`.
- **Windows CI run #39522806473 COMPLETED SUCCESSFULLY**. All engine/integration tests, PyInstaller build, EXE self-check, creation checks, and GitHub Actions upload passed.
- Artifact: `MeetingSplit-v0.8.3-Windows-build-unvalidated-on-user-hardware` (artifact ID `12311658024`, approx. 654 MB), containing `MeetingSplit_Setup_v0.8.3.exe` and `MeetingSplit-v0.8.3-Windows-portable.zip`. Artifact retention: 14 days per workflow.
- CI build success is **NOT** ASUS hardware validation and NOT a public production release.

## Next acceptance gate
1. Download artifact from successful Actions run on GitHub.
2. Prefer portable ZIP first and start on ASUS Windows 11 without running installer.
3. Check English default / Español switcher, author credit without link, PayPal support button external navigation, local data folder selection (C: or D:; never removable J:), FFmpeg processing on sample, and GPU transcription with RTX 4070.
4. If successful, validate installation/uninstallation and 1–3 hour mixed-language recordings.
5. Review PySide6/Qt, FFmpeg, model and bundled dependency license notices before publishing a Release.

## Rules
No personal meeting recordings, transcripts, local caches, credentials or private data in public repo. Do not touch `kl4ne/integrity-business-filings`. Continue from existing checkpoint and never restart.
