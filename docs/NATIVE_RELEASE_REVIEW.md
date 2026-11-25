# Native release review — development only, v0.8.6

**Not cleared for public distribution.** The previous frozen candidate is historical evidence;
the changed repair branch has no newly authorized installer build. Keep the custom
MeetingSplit freeware license intact; its section 7 already preserves applicable LGPL rights.

| Component | Evidence required before distribution | Status |
|---|---|---|
| Qt/PySide6 | Exact wheel/version, native hash match, corresponding sources, LGPL notices and replacement test | Open |
| Qt WebEngine/Chromium | Actual Chromium revision, complete matching third-party notices and source/build materials | Open |
| FFmpeg and PyAV | Pinned archive/source receipt, exact build flags, corresponding sources and linked dependency notices, replacement test | Prior technical QA passed; new candidate pending |
| CTranslate2 | Exact wheel/hash, MIT notice, native imports and CPU/GPU smoke | Open |
| NVIDIA cuDNN/CUDA | Exact vendor version and redistributable status for every bundled DLL, or remove from base package and prove optional runtime still works | Open |
| Ollama and Qwen | Exact archive and model digest, applicable runtime/model notices, local-only QA | Open |
| Native vulnerabilities | Version/provenance mapping and advisories for actual bundled native binaries; document remediation or reviewed exceptions | Open |

## Evidence collection implemented

The future, explicitly authorized frozen QA build will produce both
`build/native-inventory.json` and `build/native-provenance.json`.
The latter records exact hash matches to installed distribution files or local media
inputs, Windows PE versions where available, unmatched binaries, and candidate
Chromium notice files. It flags NVIDIA binaries for review. These are local
build-input matches, not signatures or an upstream provenance attestation.
Neither report approves licenses or certifies absence of vulnerabilities.

## Official references for qualified review

- Qt WebEngine licensing: https://doc.qt.io/qtforpython-6/overviews/qtwebengine-licensing.html
- Qt licensing: https://doc.qt.io/qt-6/licensing.html
- FFmpeg checklist: https://ffmpeg.org/legal.html
- NVIDIA cuDNN manifests and Windows redistribution archives:
  https://docs.nvidia.com/deeplearning/cudnn/installation/latest/windows.html
- NVIDIA license: https://docs.nvidia.com/cuda/eula/index.html

Qt WebEngine incorporates Chromium and requires review of both sets of licenses.
FFmpeg recommends matching distributed binaries to exact corresponding source
and build configuration. NVIDIA publishes per-version manifests with checksums
and license names; the optional component receipt is not sufficient evidence
for a different DLL included by a Python wheel.

Do not use this checklist as legal advice. No gate may be marked passed based on
a candidate notice filename, a PE version field, a successful Python scan, or a hash
match alone. Do not generate or publish any installer without explicit QA authorization.

## Exact package review, 2026-11-25

Artifact #14997636321 from run #45558345248: 685 files, 211 native; 27
unmatched and 107 without PE version. CTranslate2 4.6.2 wheel supplied
_internal/ctranslate2/cudnn64_9.dll (PE file/product 9.1.0.70; SHA-256
c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05).
The sole WebEngine candidate notice was LicenseRef-Qt-Commercial.txt; this
is not complete Chromium notices. Python 3.11.9/OpenSSL 3.0.13 require
refresh; updated source compatibility evidence is in run #45565932281.
Qt's own licensing instructions require reviewing Chromium and Qt licenses:
https://doc.qt.io/qtforpython-6/overviews/qtwebengine-licensing.html .
NVIDIA's version-specific archive manifest is the starting point for vendor
provenance, not a blanket redistribution license:
https://docs.nvidia.com/deeplearning/cudnn/backend/v9.1.0/installation/windows.html .
Keep the release gate false. The exact frozen candidate must be rechecked.
