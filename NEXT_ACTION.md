# MeetingSplit — NEXT_ACTION v0.8.4

1. **Windows CI #39527141699 PASSED**: https://github.com/kl4ne/meetingsplit/actions/runs/39527141699 . Download artifact `MeetingSplit-v0.8.4-Windows-build-unvalidated-on-user-hardware` (contains Setup and portable ZIP). Retention 14 days.
2. Download the v0.8.4 private-run artifact (not a production Release), prefer a short test with the portable version on ASUS before reinstalling.
3. Verify `D:` internal is accepted, removable `J:` remains blocked, and C: cloud folders are declined with a useful explanation; use local AppData or C:\MeetingSplit for non-synced output.
4. Run a consented 2–5 minute transcription. With missing CUDA 12/cuDNN 9, it should choose CPU rather than abort; verify `manifest.json` field `device` and warnings.
5. If GPU acceleration is desired, plan a legal, compatible NVIDIA runtime installation/bundling and repeat RTX 4070 test; do not copy random DLLs from the web.
6. Audit binary dependencies/licensing/SmartScreen before official Release.
7. Integrity Business Filings remains untouched.
