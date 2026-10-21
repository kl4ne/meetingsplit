# Development QA: LGPL-only FFmpeg and PyAV attempt

This is an isolated experiment. The existing public 0.8.6 release hold applies.

The current PyAV 16.0.1 binary wheel and Gyan/Chocolatey FFmpeg CLI include
GPL codecs. This experiment attempts to build PyAV 16.0.1 **from official
source**, linked to BtbN's LGPL shared Windows FFmpeg distribution. The
FFmpeg shared libraries are copied beside the CLI and the wheel is repaired
against that exact library directory using delvewheel. A failure must halt
packaging; the build MUST NOT fall back to the PyPI GPL wheel or Chocolatey.

The remote LGPL download is initially provenance-checked by HTTPS, build
configuration and SHA-256 receipt, but the BtbN `latest` URL is **mutable**.
Release requires replacing that URL with a fixed, hash-pinned vendor build or
an independently reproducible source build, as well as matching FFmpeg sources,
notices, dynamic LGPL replacement support, and native vulnerability review.

Acceptance tests: all actual audio output codecs (MP3, M4A, WAV), Faster-Whisper
small/medium CPU fallback and isolated CUDA GPU where available, PyAV audio
decode, frozen EXE start, portable DLL loading, installation/uninstall, no
x264/x265 in all shipped binary folders, complete license notices, reproducible
build receipts and SHA-256 files.

Only the development QA branch should invoke this script until validated. Do
not change the release gate or ship a new version based on a successful build.
## QA attempt 1 (failed safely)

Windows run #39594879663 downloaded and rejected/attempted GPL-free FFmpeg
successfully but PyAV 16.0.1 did not compile with n9.0 latest headers:
`AVCodec.supported_framerates`, `supported_samplerates`,
`pix_fmts` and `sample_fmts` are absent. No binary was packaged.
Attempt 2 uses the upstream-documented BtbN n8.1 LGPL shared headers.
Acceptance still requires a full wheel + native package verification.

## QA reproducibility update

The final QA candidate is pinned to BtbN's dated, immutable
`autobuild-2026-10-20-13-08` release (LGPL/shared 8.1.3), SHA-256
`453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a`.
Official PyAV 16.0.1 source SHA-256:
`dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf`.
Both digests are **verified before building**. The previous mutable-latest
source produced a clean LGPL package, but these specific dated bytes still
require the final Windows QA run; do not assume identical zip contents.
