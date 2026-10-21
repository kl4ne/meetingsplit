# MeetingSplit 0.8.6 — consolidated Windows installer **development QA only**

Date: 2026-10-21. RELEASE HOLD; no new version and no public GitHub Release.
Source checkpoint: `9d41c9b66980eec917c15d3ed36b5858e2e1fbf3` on `main`.
Temporary isolated QA branch `qa/consolidated-20261021` commit `3c01af9b3fecd46dc711751d2d051cbe8f70cfec`
contains a workflow trigger only; executable source is from the main checkpoint.
GitHub Actions run: https://github.com/kl4ne/meetingsplit/actions/runs/39592132218

## Observed Windows CI results

- CI job: **success**. PyInstaller packaged `MeetingSplit.exe` and Inno Setup created
  `MeetingSplit_Setup_v0.8.6.exe`; portable archive produced.
- Disposable-runner installer smoke: clean silent install, binary self-check,
  hidden WebEngine rendering of five-screen English UI, same-version reinstall,
  silent uninstall and preservation of a separate synthetic data file: **passed**.
- Frozen self-check: Qt WebEngine 6.12.0, FFmpeg and FFprobe 9.0.2 essentials,
  Faster-Whisper with CTranslate2 4.6.2: **passed**. CUDA unavailable on the
  virtual Windows runner (no NVIDIA driver): optional and not counted as a failure.
- Artifacts (development QA, 14-day retention): reports `12342368926`,
  installer `12342218926`, portable `12341888951`.
- Not tested by this smoke: interactive install cancellation, actual upgrade
  from the user's v0.8.5, real optional CUDA/Ollama downloads and retries,
  GPU inference on this runner, Windows signing/SmartScreen. The previous ASUS
  hardware tests remain valid evidence but do not validate this exact installer.

## Hash inventory findings: `build/native-inventory.json`

- Actual frozen package: **670 files**, **205 native files**, **950,475,677 bytes**
  (uncompressed). Every file's path, size and SHA-256 is in the artifact report.
- `_internal/bin/ffmpeg.exe` SHA-256:
  `3256173f3f8bffd7df12227c68adf68025edb1832273a9530688a7bb1ed8edec`.
- `_internal/bin/ffprobe.exe` SHA-256:
  `f0d36ecbbdd3bcfac3efa078c96c7271c2e68b3810595552ac3b7f17e9a65c52`.
- Exact shipped FFmpeg configuration includes `--enable-gpl`,
  `--enable-version3`, `--enable-static`, `--enable-libx264`,
  `--enable-libx265`; no `--enable-nonfree` was identified in the captured
  configure flags. The GPL-licensed components and corresponding-source,
  notices and build-script duties **must** be reconciled before distribution.
- The bundled PyAV 16.0.1 wheel's `av.libs` directory independently contains
  `libx264-165-11ed6a233462fe268a51e595a3873920.dll` and
  `libx265-eee5149aa3046c760a0c36ff7d4dbca9.dll`.
  The PyAV Python wrapper's BSD-3-Clause metadata does **not** settle the
  separate bundled native codec licenses. Those FFmpeg/codec libraries require
  their own exact-source/build/redistribution review.
- CTranslate2 package also bundles `_internal/ctranslate2/cudnn64_9.dll`:
  include this in the native-license audit even though the optional NVIDIA
  runtime download is separate.
- Qt, Qt WebEngine/Chromium third-party notices, dynamic replacement requirements,
  all bundled codec licenses, LGPL/GPL notices and corresponding source remain
  OPEN. Hash evidence does not certify malware-free binaries or license compliance.

Upstream references:
- https://ffmpeg.org/legal.html
- https://ffmpeg.org/doxygen/trunk/md_LICENSE.html
- https://github.com/PyAV-Org/pyav-ffmpeg

## Mandatory decisions before definitive installer

1. Choose and verify a defensible distribution path for FFmpeg CLI and the
   PyAV-supplied native GPL codecs: e.g. vetted LGPL-only builds without
   x264/x265 **or** fulfill actual GPL obligations with suitable legal review.
   Do **not** assert the proprietary MeetingSplit source must automatically
   be relicensed solely because the standalone FFmpeg executable is present;
   evaluate linking/aggregation and the exact combined work carefully.
2. Repeat installer QA after any native binary replacement. Test an authentic
   0.8.5 -> consolidated upgrade and interactive cancel, isolated from the
   user's working installation.
3. Test optional setup network failure, disk full, occupied managed port and
   retry with real Windows UI; existing mocks are not a substitute.
4. Verify bilingual UI and natural long-recording accuracy/thermals on user-
   approved test media. Keep the production release gate closed.

This is an engineering evidence report, not legal advice or a release approval.
