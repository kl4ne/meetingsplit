# MeetingSplit v0.8.5 — Next action

1. Publish and validate v0.8.5 on GitHub Actions. Stop on CI errors; do not claim completed installer before artifact upload.
2. Run portable build on ASUS: D: choose local folder (USB J: must remain rejected); compare time to previous release. C: root local remains fallback.
3. Confirm button displays PROCESSING and timer immediately after click.
4. Try short consented 2–5 minute transcription. GPU without CUDA should switch to CPU small and eventually complete. Check manifest actual_model. CPU may take minutes; do not assume freeze from unchanged percentage alone.
5. If D: still fails, retrieve only hardware bus info (no audio/path details) to add safe explicit verification; do not disable local-drive security.
6. Further optimize GPU library distribution and code signing after CPU acceptance.

# MeetingSplit — NEXT_ACTION v0.8.5

1. Monitor Windows GitHub Actions for v0.8.5; fix build if CI fails.
2. Download the v0.8.5 private-run artifact (not a production Release), prefer a short test with the portable version on ASUS before reinstalling.
3. Verify `D:` internal is accepted, removable `J:` remains blocked, and C: cloud folders are declined with a useful explanation; use local AppData or C:\MeetingSplit for non-synced output.
4. Run a consented 2–5 minute transcription. With missing CUDA 12/cuDNN 9, it should choose CPU rather than abort; verify `manifest.json` field `device` and warnings.
5. If GPU acceleration is desired, plan a legal, compatible NVIDIA runtime installation/bundling and repeat RTX 4070 test; do not copy random DLLs from the web.
6. Audit binary dependencies/licensing/SmartScreen before official Release.
7. Integrity Business Filings remains untouched.
