## ACTIVE NEXT ACTIONS — 2026-10-21 — after Windows QA run #39694809814

Already passed; do not repeat without material changes:
- Pinned LGPL source-built FFmpeg/PyAV & MP3/M4A/WAV frozen installer QA #39599798144 (82 pass/2 skip).
- Real isolated 0.8.5 -> 0.8.6 upgrade #39598790616.
- Main source Windows tests-only #39602465892 (84 pass/2 skip).
- New isolated source Qt-dialog cancel/disk-full/retry and extracted-file hash QA #39694809814 (**26 passed**; no hardware/vendor download).
- Existing final frozen package includes Qt WebEngine/Chromium and bundled CTranslate2 cudnn64_9.dll; read exact legal evidence matrix.

Remaining true blockers in priority order:
1. Independent legal/native-security audit of frozen package, including Qt WebEngine's Chromium 140-era third-party notices, exact source/build receipts/replacement rights, FFmpeg LGPLv3 dependencies, and provenance/redistribution rights for bundled CTranslate2 cudnn64_9.dll; see `docs/REDISTRIBUTION_EVIDENCE_MATRIX_2026-10-21.md`. Obtain full corresponding sources and notices, not just links; do not mark compliance approved without qualified review.
2. **Interactive** Windows installer cancel and interrupted real CUDA/Ollama component download/retry/full-disk using a GUI-capable throwaway Windows desktop, not GitHub's headless host. Exact pinned installer #12346625631 was downloaded/hash verified in #39694379638 but interactive window was unavailable, so this was inconclusive. Do not ask for screenshots or operate on the owner's working installation.
3. Validate this QA branch's new extracted-file receipt behavior in a final *packaged* test app and then on actual ASUS without losing prior optional components. CPU, D:, UI EN/ES, GPU and Ollama behaviors already approved elsewhere must not regress.
4. Actual ASUS (RTX 4070) exact full combined 0.8.6 build: GPU Whisper, Ollama Qwen EN/ES/mixed natural speech minutes, 1–3h resource/memory/thermal assessment, large typography views. Earlier synthetic tests are not this acceptance.
5. Separate signing/SmartScreen and identity disclosure consent decision, if needed for public shipping.

No new version, no definitive user installer, no GitHub Release. Keep `qa/release_gate.json` `release_allowed=false`. Do not change Integrity. Handoff is `qa/release-evidence-20261021`.

---
## ACTIVE NEXT ACTIONS — 2026-10-21, QA release-evidence branch

1. **Do not repeat resolved work:** #39598629560 hash failed because the source URL was `latest/n9.0` while expecting a dated 8.1.3 digest; the dated build and pinned PyAV succeeded in #39599798144. #39598790616 authentic upgrade PASSED. Main tests-only #39602465892 PASSED. Do not rerun these without material changes.
2. Finish exact Qt 6.12/WebEngine 6.12.0.140 Chromium third-party notices and source/BOM obligations, FFmpeg/PyAV LGPLv3 corresponding source/relinking evidence, and native CTranslate2 bundled `cudnn64_9.dll` NVIDIA licensing/provenance. See `docs/QA_NATIVE_EVIDENCE_AUDIT_2026-10-21.json`. External legal review still needed.
3. Run real Windows isolated interactive-cancel tests and optional CUDA/Ollama interrupted download, retry, full-disk and occupied-port matrix; simulation-only unit tests do not count as installer UI acceptance. Protect ASUS installation and its data.
4. On the ASUS, verify the exact consolidated pinned installer with GPU/Whisper + Ollama and natural EN/ES/mixed speech, sustained duration/resource behavior; one-hour synthetic predecessor is not three-hour realistic acceptance.
5. Keep `qa/release_gate.json` false and 0.8.6. No Release, no definitive installer, no unreviewed source/license substitutions, no Integrity changes. QA evidence checker was tested locally (6 focused cases); no additional Windows run was ordered.

Checkpoint branch: `qa/release-evidence-20261021`, based on main `c292ad5d`. Previous `qa/consolidated-20261021` was not rewritten.

---
## Next action after successful pinned main tests-only CI

1. Assemble exact Qt WebEngine/Chromium and bundled cuDNN third-party
   notices/source/redistribution proofs. Qualified review is needed;
   SHA-256 inventories alone do not clear this gate.
2. Perform Windows interactive installer cancellation, optional CUDA/Ollama
   download interruption/resume and full-disk cases against the exact
   consolidated candidate (prior mocks do not prove full UI behavior).
3. Validate the final consolidated GPU/Whisper + Ollama minute workflow on
   the actual ASUS, then re-check all five views at +2 font scale EN/ES.
4. Keep signed-publisher/SmartScreen work separate and avoid exposing
   verified private identity without the user's permission.
5. Do not increment the version, publish artifacts as a Release, or enable
   `qa/release_gate.json` until all are verified.

## Remaining acceptance work after pinned media consolidation

1. Finalize LGPL/Qt WebEngine/Chromium source notices and corresponding
   source/build instructions for exact frozen binaries; record third-party
   legal review, not merely SHA-256 checks.
2. Run isolated interactive cancellation and real CUDA/Ollama optional
   setup failure/retry test matrix; preserve external user data.
3. Verify the final combined GPU + Ollama setup and real EN/ES meeting
   accuracy on ASUS (the CI runner has no NVIDIA driver).
4. Consider Authenticode signing, publisher identity privacy and
   Microsoft SmartScreen separately.
5. The user forbids partial versions: keep `qa/release_gate.json`
   blocked and do not release a new public installer before all gates pass.

## Remaining technical gates after successful LGPL media package QA

1. Finish isolated authentic v0.8.5->0.8.6 Windows upgrade run
   #39596746344; audit any failure against real logs.
2. Repeat a **single** consolidated QA build using the pinned dated BtbN
   archive SHA-256 `453a30a501...` and verify its frozen PyAV and audio
   exports. Only then consider moving the reviewed LGPL build code into main.
3. Complete Qt/Chromium/FFmpeg LGPLv3 third-party source and notice
   obligations, and any remaining native-vulnerability review.
4. Verify live optional CUDA/Ollama wizard cancellation/retry/disk-full
   on Windows, and real ASUS natural-meeting GPU/minutes acceptance.
5. No public Release, new version or user installation request until all
   release requirements are confirmed.

## Next required engineering actions after LGPL experiment

1. Inspect QA Windows run #39595255314:
   https://github.com/kl4ne/meetingsplit/actions/runs/39595255314
   Check PyInstaller, frozen audio/Qt, install/uninstall and final artifacts.
2. If successful, download `lgpl-media-receipt.json` and native inventory;
   verify no bundled x264/x265, LGPL FFmpeg flags and actual MP3/M4A/WAV
   export/transcription. Pin downloaded LGPL FFmpeg archive digest.
3. Run the staged authentic prior-installer upgrade test with old Actions
   artifact #12315582489 and current QA installer in a **separate** throwaway
   Windows runner, without repackaging unrelated dependencies.
4. Resolve LGPL attribution/source/Qt WebEngine native notices and test
   interactive optional-component failures. Only after hardware and legal
   acceptance can the release gate ever be changed to true.
5. Preserve existing 0.8.6 and no public user install/release during QA.

## Next pre-release engineering tasks — after consolidated QA

1. **Highest priority:** address confirmed GPL-enabled FFmpeg 9.0.2 CLI
   and PyAV-supplied x264/x265 DLL licensing. Prefer investigating a
   pinned LGPL-only FFmpeg distribution and compatible PyAV-native build,
   or supplying corresponding sources/notices/build scripts with legal review.
2. Implement/verify actual 0.8.5 upgrade path and cancellable Windows
   installer interactions in a disposable Windows environment.
3. Execute optional CUDA/Ollama real-download and retry matrix plus resource
   checks, without affecting the user's installed version.
4. Re-run consolidated QA **only after** material changes. Do not deliver or
   publish the QA binary as a release; keep 0.8.6 and release gate blocked.
5. Link to evidence: `docs/QA_CONSOLIDATED_2026-10-21.md`,
   Actions #39592132218, report artifact #12342368926.

# Next acceptance gate — before definitive MeetingSplit installer

1. Preserve `release_allowed=false` and version 0.8.6. No more ordinary CI builds
   for this checkpoint; tests-only CI #39590849581 already passed (75 / 2 skipped).
2. When the consolidated **development QA package** is explicitly arranged, inspect
   `build/native-inventory.json` and exact `ffmpeg-build.txt` flags. Collect
   corresponding native sources/build receipts and copyright notices for Qt/
   Chromium, FFmpeg CLI, PyAV FFmpeg libs, CTranslate2 and remaining bundled DLLs.
3. On disposable Windows installations test clean install, real upgrade from
   0.8.5, interactive cancellation, uninstall/data preservation, and optional
   CUDA/Ollama network interruption, reattempt, occupied port and full disk.
   Current isolated unit tests do not prove a Windows wizard passed these.
4. Evaluate natural Spanish/English/code-switch meetings, 1-3 hour memory/thermal
   stability and the final combined GPU/Ollama installer on the ASUS.
5. Only after release gate evidence is reviewed may a definitive installer/
   public Release be considered. Keep Integrity Business Filings untouched.

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
