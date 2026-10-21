# MeetingSplit — NEXT_ACTION

1. Check Windows GitHub Actions run: https://github.com/kl4ne/meetingsplit/actions/runs/39522806473 .
2. If it fails, inspect the failed step and job log, implement the smallest fix on `main`, and rerun Windows CI.
3. If successful, inspect the artifact names, check for `MeetingSplit_Setup_v0.8.3.exe` and portable ZIP, then mark as **CI-built, not yet ASUS-tested**.
4. Test Windows install/uninstall, English/Spanish UI, direct PayPal support URL, local C:/D: folder picker, audio splitting, and CUDA Whisper on the user's RTX 4070 with consented sample audio.
5. Review third-party licenses and notices before publishing a public GitHub Release. Do not ask user to install an unverified EXE.
6. Leave `kl4ne/integrity-business-filings` unchanged.
