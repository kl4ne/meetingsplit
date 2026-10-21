## Pre-installer development checkpoint — 2026-10-21

- Added a frozen-package SHA-256 inventory and conservative FFmpeg build-flag review.
- Added offline regression tests for interrupted vendor downloads, timeouts,
  low disk space, an occupied managed Ollama port and existing Ollama reuse.
- `qa/native_inventory.py` passed 5 local synthetic Python tests. Optional
  component fault-injection tests require Windows CI validation.
- Only a future manually authorized **QA build** can collect a report from
  actual frozen Windows binaries; NO new installer or public Release has been created.
- The release gate stays BLOCKED and the application version remains 0.8.6.

# CURRENT checkpoint — 2026-10-21 — RELEASE HOLD

Latest observed updates:
- Local frozen EXE tested on the actual ASUS RTX 4070: CUDA/medium synthetic
  speech passed EN (0.78 s) and ES (0.62 s); Ollama qwen3:4b completed synthetic
  minutes EN (100.31 s) and ES (87.48 s). Both retained Ana/Friday and Luis/Monday.
  These are short synthetic checks, not general accuracy or sustained-speed claims.
  EXE SHA-256: 8c6616ca02b7c54983d3841e650915153d187125dee0500e0754f4479e9e1831.
  Frozen Qt/FFmpeg/Whisper self-check and hidden five-screen WebEngine load passed.
  This tested binary predates the subsequent general prompt/legal-text changes;
  the final consolidated installer still requires acceptance before any delivery.
- Fixed local packaging contamination: unrelated host Poppler ICU was shadowing
  Windows ICU and breaking frozen QtCore. Build PATH is process-scoped. Custom
  Qt hooks exclude unused QML/debugger/virtual-keyboard modules; native package
  audit passed with no blocked unused Qt modules. This does not close native licensing.
- Real generated English minutes used "None" for an unspecified pending section.
  Generalized production instructions now request "Not specified" for absent
  section information and no longer mention example draft tasks. Separate source
  evaluation passed in 128.42 s with Priya/reserve room/Tuesday, Marco/confirm
  capacity/Wednesday and $200; no Ana/Luis/draft tasks appeared, absent sections
  used "No especificado". Minor generated wording still warrants human review.
- Original MIT/LGPL/GPL texts missing from exact installed wheel notices are now
  retained with upstream URLs/hash receipts. License explicitly preserves LGPL
  library modification/replacement and debugging rights. Full corresponding-source,
  Chromium/native notice and security review remains OPEN.
- Local full regression before packaging: 71 passed, zero skips (126.23 s).
  Latest targeted component/storage/build regression: 32 passed (4.32 s).
- Previous development runs 39541919344, 39542617600, 39543320166 and 39543467751
  completed successfully. Disposable CI installer clean/reinstall/uninstall smoke
  passed on the earlier source; it does not test a real 0.8.5 upgrade or cancellation.
- User explicitly requested conserving Actions minutes. No Actions run started
  during this continuation. Installer builds now require manual QA dispatch; commit
  markers no longer trigger packaging. Superseded runs cancel automatically,
  optional Inno tooling only installs for packaging, duplicate tests are removed,
  job timeout reduced to 40 min and frozen startup check bounded to 60 s.
  Save this checkpoint with [skip ci]; do not dispatch another build speculatively.
- One-hour synthetic repeated EN/ES workload completed on ASUS CUDA/medium in
  339.3 seconds: 7 exported clips, 622 transcript segments, subtitles and ZIP.
  This is workload evidence, not natural-meeting accuracy or a three-hour test.
- Actual missing-library CPU recovery passed in a fresh process without application
  CUDA folders: cublasLt64_12.dll absent, CPU transcribed both EN/ES test samples.
- Finished English and Spanish synthetic minutes reviewed: Ana/send/Friday and
  Luis/review/Monday preserved; unknown meeting date not invented, attendance not
  assumed, headings/statuses localized. Spanish succeeded alone in ~96 s after a
  concurrent GPU stress run had caused a bounded timeout. Production unloads Whisper
  before starting Ollama; generated text always still requires human review.
- Optional minutes failure now preserves completed transcript/audio/SRT/ZIP and
  exposes MINUTA_NO_GENERADA.txt in Results; integration regression passed.
- Existing Ollama weights must also have an API-reported source path validated as
  internal and unsynced before reuse. Unknown/USB/cloud paths and remote aliases
  are not reused; a separate managed installation remains available.
- Original NVIDIA license texts and Ollama MIT notice included for review before
  optional download. Exact Qt/FFmpeg source and native licensing/security obligations
  remain open.
- First development build 01343bb: Windows compilation, frozen self-check, Setup
  and portable archive passed (run 39541919344). c415e18 disposable installer
  smoke QA also passed (run 39542617600). No new version or Release.
  Artifact downloads have a 512 MiB connector limit; future portable/setup/reports
  are uploaded separately for internal inspection.

Continue `kl4ne/meetingsplit` main from `434651f`. Keep app version **0.8.6**.
NO Release, new version number, user delivery or installation request until CUDA,
optional Ollama, installer QA, regressions, security and licenses are evaluated.
Commits/development CI are allowed. Do not touch `kl4ne/integrity-business-filings`.
All older next-step/delivery instructions below are historical and superseded.

Implemented in this checkpoint:
- Pinned Faster-Whisper 1.2.1 / CT2 4.6.2 / PyAV 16.0.1, patched setuptools and
  tested Qt/build versions. Testing found real dependency breaks: CT2 4.6.0 needed
  removed pkg_resources; PyAV 19 removed metadata_errors required by Faster-Whisper.
- Optional NVIDIA cuBLAS 12.4.5.8, CUDA runtime/NVRTC 12.4.127 and cuDNN 9.1.1.17:
  official SHA-256/size pinned archives, safe extraction, internal storage validation,
  retained licenses and cancellation. No driver/admin/global PATH/System32 changes.
- Complete split cuDNN preflight and isolated bounded lazy-inference probe; existing
  small/int8 CPU fallback retained. Whisper released before Ollama to free VRAM.
- Unchecked optional component wizard from Inno Setup and Settings; base package
  has no NVIDIA/Ollama archives or model weights.
- SHA-pinned Ollama 0.40.6 standalone; reuse ready existing qwen3:4b on 127.0.0.1:11434,
  otherwise own temporary server on 127.0.0.1:11435 with models in selected internal
  folder. Never pull into an existing server with unknown storage location. No
  system service/startup/global environment changes. Loopback only, no proxies or
  redirects, fixed model, progress/cancellation, bounded reads, cold-load handling,
  license/digest receipt and synthetic minutes test. Reject empty/truncated output.
- Existing five EN/ES pages, enlarged fonts, direct PayPal and plain credit retained.
  Custom/corporate OneDrive roots additionally blocked; USB security retained.
- Explicit fail-closed qa/release_gate.json and license inventory collection.
  Normal pushes test only; installer builds require explicit manual workflow input.
  CI has no Release permission. Use [skip ci] for locally validated checkpoints
  when no new runner evidence is needed.

Observed here on the actual ASUS (source environment; no private meeting audio):
- Hardware: ROG Strix G614JI, RTX 4070 Laptop 8188 MiB, driver 617.42.
- Official NVIDIA archives downloaded/hash verified under ignored work/hardware.
  CUDA inference passed with silence and Windows TTS EN/ES samples (~10 s each),
  small and medium. Final CT2 4.6.2 medium CUDA int8_float16: ~0.72 s EN / ~0.61 s ES
  after preparation. These short warm tests do not establish long-recording or
  frozen-installer acceptance. Medium preserved Ana/Luis and stated $5000 budget;
  small confused some names, reinforcing manual review.
- CPU small/int8 also transcribed both synthetic speech samples. User's previous
  six-clip CPU/~11 min success remains the real-meeting baseline.
- Read-only actual drive checks: internal C:/D: accepted, J: rejected as USB.
- Regression batch: 55 passed, 1 skipped before final added tests; browser/optional
  security batch: 26 passed. Final counts/CI recorded in NEXT_ACTION when available.
- Python dependency audit after CT2/setuptools/pip correction: no known advisories
  from pip-audit. Native licensing/security review remains pending.
- Ollama runtime/model downloaded; endpoint, model and license validated. Initial
  minutes tests exposed cold-load timeout and a model declaring thinking.values=[true].
  Disabling thinking was not supported. The corrected client enables its separate
  thinking channel, discards that field, reserves adequate context/output budget,
  and rejects truncation. A finished English synthetic minute was generated and
  reviewed; explicit locale/task rules corrected mixed-language headings and an
  omitted task. Corrected English output includes both Ana/Friday and Luis/Monday,
  no invented date and no claim of confirmed attendance. Spanish QA also passed;
  see latest updates above.
- Full local regression with final pinned dependencies: 68 passed (no skips),
  including browser EN/ES navigation. Subsequent small fixes require targeted checks.

Remaining: corrected EN/ES minutes assessment, frozen EXE/installer end-to-end GPU
and Ollama, clean/upgrade/cancel/uninstall, long-recording/resource tests, complete
native dependency and GPL/LGPL redistribution evaluation. Keep release gate closed.
See docs/OPTIONAL_COMPONENTS.md and docs/THIRD_PARTY_REVIEW.md.

---
## Historical checkpoints (superseded next steps)

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
