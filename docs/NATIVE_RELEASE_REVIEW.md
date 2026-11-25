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
