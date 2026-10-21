# MeetingSplit — NEXT_ACTION (Windows CI passed)

**CI status: SUCCESS** — https://github.com/kl4ne/meetingsplit/actions/runs/39522806473

1. From the run page, download artifact `MeetingSplit-v0.8.3-Windows-build-unvalidated-on-user-hardware` (GitHub login may be required). It contains `MeetingSplit-v0.8.3-Windows-portable.zip` and `MeetingSplit_Setup_v0.8.3.exe`.
2. Start with a controlled **portable** launch on ASUS Windows 11, without installing or bypassing OS security warnings. Keep source audio private; use a disposable, consented 5–10 minute sample.
3. Check actual UI, EN default / ES selection, contrast, one-screen navigation, unlinked author credit, PayPal direct external URL, and local output folder on C: or D: (reject USB J:).
4. Process sample audio: split coverage, no lost sentence at seams, WAV/MP3/M4A exports, TXT/SRT/ZIP; verify actual Whisper CPU/GPU behavior and model download.
5. Capture diagnostics as text and fix any Windows-specific runtime issue; then try Setup install/uninstall and a 1–3-hour audio.
6. Audit bundled third-party license notices, model licenses and code signing/SmartScreen before publishing official Release.
7. Integrity Business Filings is read-only / untouched.

Artifact retention 14 days. Do not call CI-built executable a production release.
