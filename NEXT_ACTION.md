## MeetingSplit v0.8.6 — Ready for ASUS visual acceptance
1. Successful Windows workflow: https://github.com/kl4ne/meetingsplit/actions/runs/39537216562
2. Download artifact `MeetingSplit-v0.8.6-Windows-build-unvalidated-on-user-hardware` (artifact ID 12317478170). Contains `MeetingSplit_Setup_v0.8.6.exe` and portable `MeetingSplit-v0.8.6-Windows-portable.zip`.
3. Prefer portable to check enlarged typography on ASUS. Review EN and ES on Home, Import, Settings, Processing, Results; check no clipping; no need to re-run 11-min transcription just to validate typography.
4. Leave CPU splitting/transcription and D: disk storage untouched. Later: NVIDIA CUDA setup to resolve `cublas64_12.dll` if user approves, validate performance separately.
5. App is still unvalidated for public Release; do not claim SmartScreen is removed or that GPU support is ready.
6. Integrity Business Filings remains untouched.

## NEXT: v0.8.6 accessibility/layout validation
- Keep D: storage support and CPU fallback stable (user verified six completed transcripts in ~11 minutes).
- Confirm GitHub Actions v0.8.6 Windows compilation, then test user perception of +2-step fonts on ASUS in all five screens and EN/ES.
- Only after typography approval, address optional RTX 4070 CUDA acceleration separately; do not conflate successful CPU fallback with CUDA repair.

## v0.8.6 next
1. Validate 5 independent pages in EN/ES at 1366×768, 1440×900 and 1920×1080 with larger typography.
2. Run engine tests and Windows CI, verify updated installer artifact.
3. Ask user to validate legibility on ASUS before pursuing CUDA speed-up. CPU fallback in v0.8.5 WORKS, D: ACCEPTED.

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
