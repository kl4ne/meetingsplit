# MeetingSplit 0.8.6 — native licensing/security evidence, exact follow-up

**Internal QA branch:** qa/release-evidence-20261021. **Release is not authorized.**
The previously successful QA installer #39695270843 was built at 90238d6,
BEFORE the new notice-integrity gate and UI diagnostic fix in this branch.
Do not equate a changed repository with a newly packaged, accepted EXE.

## VERIFIED from official upstream sources (October 21, 2026)

1. **Qt for Python 6.12 and WebEngine 6.140.0:** Qt announced that WebEngine
   has separate versioning starting with Qt 6.12; the Python wheel uses
   `6.12.0.140` for WebEngine 6.140. The upstream qt/qtwebengine tag
   `6.140.0`, file `CHROMIUM_VERSION`, Git blob
   `af94dd121710fc8df04db6182bc27a1faf7d83e6`, declares:
   Chromium base `140.0.7339.264` and security patch level
   `155.0.8059.85`.
   Source: https://github.com/qt/qtwebengine/blob/6.140.0/CHROMIUM_VERSION
   Version mapping: https://www.qt.io/blog/qt-webengine-will-release-separate
   **This is upstream source evidence only**, not a CVE-free claim or
   proof that the frozen `Qt6WebEngineCore.dll` contains exactly those
   patches. Confirm compiled metadata and binary origin before release.
2. **cuDNN 9.1.1:** NVIDIA's official *cuDNN supplement*, item 2,
   explicitly identifies runtime `.dll` and `.so` files as
   redistributable under its SDK agreement. Sections 1.2 and 2 contain
   further application-use, notices and other conditions; this is not
   unconditional redistribution permission for any third-party copy.
   Source:
   https://docs.nvidia.com/deeplearning/cudnn/backend/v9.1.1/reference/eula.html
   Exact actual candidate's `_internal/ctranslate2/cudnn64_9.dll`:
   SHA-256 `c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05`.
   Its exact version and origin from the CTranslate2 wheel, plus
   which SDK EULA revision controls it, remain unverified.
3. **Candidate ctranslate2 4.6.2 upstream wheel:** PyPI offers
   `ctranslate2-4.6.2-cp311-cp311-win_amd64.whl`, published
   2025-12-05, with SHA-256
   `ce7880fa5d2e1b36329998c711cb764c621a4d2a199b251b1ad02e770b641e91`.
   Link: https://pypi.org/project/ctranslate2/4.6.2/
   The SHA of the wheel is **not** independent evidence that the shipped
   cuDNN DLL matches the original wheel bytes. To close this subtask,
   download and verify wheel on an authorized developer system,
   extract its exact embedded DLL and compare SHA-256 with frozen inventory,
   inspect native version information, and retain the EULA/notice.
   No such independent wheel comparison was completed in this chat.
4. **Chromium license obligations:** Qt's official WebEngine documentation
   states that Chromium sources form part of Qt WebEngine Core and require
   their own third-party notices as well as Qt's LGPL obligations.
   https://doc.qt.io/qt-6/qtwebengine-licensing.html
   The prior 685-file internal QA inventory has no verified full Chromium
   third-party notice collection and a link alone is not a license package.
   Match actual Qt WebEngine build and Qt module dependencies and collect
   the complete applicable texts or a legally suitable source/notice delivery.

## Technical changes performed (source-only until next QA frozen build)

- `qa/vendor_legal_manifest.py` checks the seven original licenses in
  `docs/third-party-licenses/sources.json`, SHA-256, upstream URLs, safe
  filenames, missing/duplicate notices, and reports unresolved legal steps.
- `qa/collect_licenses.py` now requires those source records to match
  before a build and writes `build/legal/PINNED_UPSTREAM_NOTICE_RECEIPTS.json`
  for an auditor. `qa/audit_package.py` additionally verifies the
  **actually frozen** source notice bytes in `_internal/docs/third-party-licenses`.
- `ui/app.js` now shows the existing `MINUTA_NO_GENERADA.txt`
  diagnostic after Ollama failure; the production Python pipeline and
  Qt bridge were already exposing the file. It is only an allowlist fix,
  not a change to the transcript or model.
- Regression tests cover both above.
- No broad native dependency upgrades, system PATH changes, registry changes,
  background services or hardware test have been performed.

## Other required release blockers

- Exact corresponding source/build material and license replacement/
  reverse engineering duties for Qt/FFmpeg/PyAV LGPL.
- Native version/CVE/security audit against the exact frozen bits; CTranslate2
  bundled cuDNN origin and license review; Qt Chromium notices/versions.
- Interactive installer cancellation on GUI-capable disposable Windows;
  prior GitHub-hosted test #39694379638 had **no visible desktop**.
- Full optional CUDA/Ollama *real* network interruption/retry/disk-full and
  final target ASUS GPU+Ollama mixed EN/ES *natural speech* acceptance.
- Human review of license terms; publisher/signing/SmartScreen decision.

**Gate remains unchanged**: MeetingSplit 0.8.6,
`qa/release_gate.json` with `release_allowed=false`. No public
Release, merge, install on ASUS or other app modification is authorized.
