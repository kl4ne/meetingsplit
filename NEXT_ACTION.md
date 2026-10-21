## Optional Ollama setup failure-state regression

- Source now records `status=complete`, `cancelled`, or `failed`
  instead of leaving an interrupted download stuck at `testing`.
- Three isolated tests cover failed download, cancellation, and successful
  reuse of an existing model. No real model download or installer has run.
- These tests must pass on the next tests-only Windows CI before QA packaging.
- Public release remains blocked; version stays 0.8.6.

## Pre-installer actions (new checkpoint)

1. Run the Windows **tests-only** workflow once, without `package_for_qa`,
   to validate new optional-component failure simulations; do not create another installer.
2. On a future *explicitly authorized* consolidated QA package build, collect
   `build/native-inventory.json` and reconcile its SHA-256 entries with
   Qt, FFmpeg CLI, PyAV native FFmpeg, Chromium and CTranslate2 notices.
3. Continue the paused clean/upgrade/cancel/uninstall and optional download/
   retry/disk-full acceptance matrix using isolated test environments only.
4. Keep `qa/release_gate.json` closed; no new app version or user download until
   legal review, native dependency evidence and final installer QA pass.

# CURRENT next actions — 2026-10-21 — no new version/delivery

Keep 0.8.6; continue main/checkpoints. Do not publish Release, deliver a new build,
ask user to install anything, or touch kl4ne/integrity-business-filings. Historical
delivery steps below are superseded by this section and the user's release hold.

1. Frozen ASUS CUDA speech and Ollama EN/ES generation now passed; see current
   MASTER_STATUS for exact timings and EXE hash. Independent updated generic-prompt
   example also passed (Priya/Marco/$200, 128.42 s). Keep separate thinking-field
   handling and truncation rejection. Do not reuse stale JSON as new evidence.
2. 71-test full local regression passed, zero skips; latest focused batch 32 passed.
   Repeat affected checks after new changes only. Preserve enlarged five-screen
   EN/ES UI, PayPal and plain author credit. Frozen five-screen load also passed.
3. Save local verified changes before considering another CI build. Installer
   packaging now requires an explicit workflow_dispatch QA input; commit markers
   no longer build installers. Cancel superseded runs automatically. Do not spend
   Actions minutes repeating checks that can run locally. Compilation is not acceptance.
4. Final consolidated package still needs installer acceptance after the current
   packaging hooks, prompt/legal updates and EN/ES installer text. Evaluate wizard
   with internal test data: CPU recovery, existing instance, occupied port, cancel/retry,
   disk full, clean/upgrade/cancel/uninstall. Preserve the user's working installation.
5. Finish docs/THIRD_PARTY_REVIEW.md requirements, exact Qt/FFmpeg/PyAV inventory,
   original notices and corresponding-source obligations. Python-only audit is clean;
   native security/license review is still open.
6. One-hour synthetic CUDA/medium pipeline passed in 339.3 s (7 clips, 622 segments,
   SRT/ZIP). Short actual missing-library CPU fallback also passed EN/ES. Remaining:
   final consolidated installer, natural-meeting accuracy, three-hour/resource/thermal evaluation.
7. Update checkpoints/gate only with observed evidence. release_allowed stays false
   until every required item is prepared and evaluated.

Anti-timeout: long operations asynchronous; bounded tool calls/progress; inspect
errors before retry; persist checkpoints. Do not upload recordings/tokens/credentials.

---
## Historical next actions (superseded)

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
