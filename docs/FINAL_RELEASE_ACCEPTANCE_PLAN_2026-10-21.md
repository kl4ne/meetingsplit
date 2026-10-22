# MeetingSplit 0.8.6 — final acceptance execution plan (no wasted GitHub Actions)

**Checkpoint:** 2026-10-21, branch `qa/release-evidence-20261021`, draft PR #1.
All existing passing native builds and Windows tests must be reused rather than
rerun. This document **does not** authorize any install, live download or
public release. Use a new frozen QA build only after all source/legal changes
are batched and have passed source tests.

## Phase 1 — close exact native license/security work (assistant can prepare)

- Compare the installed `ctranslate2-4.6.2-cp311-cp311-win_amd64.whl`
  SHA-256 with PyPI and the actual `cudnn64_9.dll` hash; verify DLL's
  precise CUDA/cuDNN release and NVIDIA's controlling SDK agreement.
  Official cuDNN 9.1.1 supplement permits runtime `.dll` distribution
  under its conditions, **not blanket permission**.
- Match QtWebEngineCore.dll and QtWebEngineProcess.exe to Qt WebEngine 6.140.0,
  its Chromium 140 base and declared patch level; obtain Chromium's *actual*
  third-party notices and Qt LGPL source/replacement instructions.
- Provide matching FFmpeg source/build scripts and PyAV sources/license texts,
  ensure notices are embedded and visibly reachable by users.
- Keep `qa/vendor_legal_manifest.py`, frozen byte-level manifest validation,
  any vulnerability scans, and the full native audit as separate evidence;
  do not mark compliance complete by passing unit tests.
- Continue from `docs/NATIVE_LICENSING_SECURITY_EVIDENCE_2026-10-21.md`.

## Phase 2 — interactive QA on disposable Windows GUI (external dependency)

**DO NOT** attempt hosted Actions #39694379638 again. That runner could not
display the installer window. Use a Windows 11 *disposable virtual machine*
with working interactive desktop, clean snapshot, standard user account and
at least 16 GiB free. Test on a non-owner installation only. Record source
artifact exact SHA, VM OS/build, app version and timestamps.

1. With user consent, launch the development-only installer from the
   approved GitHub QA artifact inside the disposable VM. Choose Cancel on
   the wizard before any files are copied; confirm installer exits and
   no MeetingSplit app appears in its isolated install directory.
2. Restore VM snapshot. Start another install, request cancellation while
   copying large files, inspect Inno log and verify no partial running app
   or damaged unrelated data. Log outcome separately from pre-copy cancel.
3. Restore snapshot. Verify clean install, same-version reinstall,
   0.8.5->0.8.6 upgrade (already passed in a silent runner; repeat only
   if installer logic changes), uninstall, user-data preservation.
4. Only after explicit acceptance of vendor licenses, simulate a network
   disconnect during **actual** CUDA/Ollama downloads and retry in the VM.
   Verify no unverified partial becomes executable. Test insufficient disk,
   occupied loopback port and cancellation without altering system PATH,
   drivers, existing Ollama services or Windows user settings.
5. Preserve installer logs, hashes and a factual JSON verdict. No claims
   of interactive success from mock tests or a headless runner.

This phase depends on access to a GUI-capable VM; GitHub's hosted runner
does not provide it. Avoid provisioning paid/self-hosted CI without consent.

## Phase 3 — ASUS acceptance (device owner must participate)

After fixes and legal package readiness, validate the **EXACT** internally
approved candidate once on the ASUS RTX 4070. Do not overwrite prior user
installation or data: back up existing settings, use a dedicated verified
internal, unsynced folder on C: or D:, not USB or OneDrive.

- Compare installer SHA, application version, and GPU driver requirement.
- Existing `qa/hardware_speech.py` uses synthetic Windows TTS samples;
  `qa/ollama_minutes.py` uses a synthetic transcript; and
  `qa/long_synthetic.py` runs the actual one-hour synthetic pipeline.
  They are available and previously exercised, so run only when matching
  the final *new binary* on the actual hardware.
- Real spoken English, Spanish and mixed English/Spanish meeting samples,
  1–3h end-to-end export and local Ollama minutes, transcription accuracy,
  GPU/CPU fallback, cancellation, memory, disk, temperatures and UI font
  accessibility require local observation. Local recordings must never be
  uploaded to GitHub or ChatGPT as part of acceptance; preserve only
  non-sensitive diagnostics and redacted numbers with consent.
- The actual app must show `MINUTA_NO_GENERADA.txt` on results after
  a deliberately failed optional local minutes request, and permit user
  to open it without sending content to a server.
- Do not certify this step by a Windows CI GPU-less VM.

## Phase 4 — distribution decision

- Merge only after all new tests and full native/legal evidence have passed
  and owner has reviewed the final freeware license.
- Decide publisher identity and code-signing certificate with owner, test
  Authenticode signature and Windows SmartScreen behavior; do not promise
  an unknown certificate removes warnings.
- Build exact final binary once, rerun changed-scope QA and complete freeze
  tests, publish SBOM + notices + source fulfillment instructions + installer
  SHA256, confirm five views EN/ES and clean removal behavior.
- Only with explicit owner authorization consider changing
  `qa/release_gate.json`. Until then **release_allowed=false**,
  version **0.8.6**, no GitHub Release, no change to `main`.
- Integrity Business Filings is a separate repository and MUST NOT be touched.

## Established successful runs — do not repeat for no reason

- Pinned LGPL frozen QA #39695270843: 102 passed, 2 skipped, install/same-version
  reinstall/uninstall on disposable Windows, 685 files/211 native;
  internal-only artifacts 12390712114 (reports), 12391430920 (installer),
  12390996760 (portable).
- Optional Qt/CPU synthetic regression #39694809814: 26 passed.
- Original 0.8.5->0.8.6 authentic silent upgrade #39598790616: passed.
- Notice SHA checksum test #39696118269: passed.

**No required human step is presently proven complete by this plan alone.**
