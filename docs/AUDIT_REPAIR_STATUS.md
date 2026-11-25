# Audit repair — development only (0.8.6)

Branch fix/audit-stability-086, no public release. Initial repair batch:
- Monotonic pipeline progress and disk-space estimates before work and ZIP.
- Per-clip timestamped JSON checkpoints (not yet a resumable workflow).
- Finite duration validation, cancellable ZIP streaming, final data-root validation.
- Added focused regression tests; Windows and ASUS verification pending.

Remaining: isolated persistent inference worker, restart/recovery UI, explicit CPU
quality policy, report evidence validation, component integrity and resumable
downloads, cloud-root detection, CI/SBOM, exact installer acceptance and legal review.
Do not change release_allowed or distribute an installer.

Second batch: HTTP range resume with pinned size/hash, installed file inventory
and revalidation (legacy receipts require reinstall in a clean folder),
GPU verification failure uses CPU, diagnostic minute file exposed in UI.
Local receipts detect corruption, not malicious modification of both receipt and files.
Live Windows installer, download and runtime acceptance still required.

Third batch: desktop uses persistent isolated Whisper subprocess with bounded
file IPC; native GPU worker crash/timeout retries current clip on CPU. CPU
precision opt-in preserves selected model and word timestamps. PR tests-only
trigger added. Frozen worker lifecycle, real cancellation, layouts and GPU
fallback require Windows/ASUS acceptance. No release or packaging authorized.

Fourth batch: resumable interrupted jobs, same-source SHA-256 and settings
signature, per-export and transcript checkpoint hashes, explicit folder
picker and preservation of orphan files. Only jobs created by this new
implementation have compatible recovery metadata. End-to-end Windows QA
and resume test execution are pending.

Fifth batch: report timestamp citations must exist in original transcript;
draft review warning and manifest flag. This checks citations, not factual
correctness; structured fact extraction/validation and natural EN/ES QA
are outstanding. Extra Dropbox/Windows sync-root heuristics are not a
guarantee that every sync provider is detected. Browser PR tests and
Python CycloneDX dependency audit added. Native security/SBOM, legal review,
reproducible transitive lock, signing and hardware acceptance remain.
All release evidence flags reset for this changed candidate; previous
main evidence is historical, not proof that the new branch passed.

## First repair-branch Windows CI, 2026-11-25

Run #45555215797: engine 97 passed, 2 skipped; browser 11 passed.
Dependency audit failed: 12 known vulnerabilities in one package. Downloaded
CycloneDX artifact #14995786441 maps the reported findings to pip 24.0 in the
audit environment, not to the MeetingSplit runtime packages. The engine CI
successfully installed pip 26.3. Pin both CI environments to pip 26.3 before
installing dependencies; retain a failing security gate and print advisory IDs
from the SBOM. New execution required; no frozen installer was built.

## Recovery integrity follow-up

Use an OS-backed exclusive job lock to prevent two processes writing the same
resumed job. Detect source file identity/metadata changes before/after exports
and before completion; do not checkpoint a changed source. Write metadata and
text outputs atomically using unique staging files; rebuild missing per-clip
text from verified JSON checkpoints; quarantine stale temporary audio. ZIP
excludes symlinks. These are defensive checks, not protection against a hostile
local administrator or arbitrary simultaneous filesystem tampering. Regression
tests added; exact new commit requires CI.

## Evidence-based local minutes

Replace lossy recursive free-text consolidation with bounded structured JSON
candidate extraction. A deterministic validator checks exact source IDs,
verbatim quotations and literal owner/deadline fields before rendering bilingual
Markdown. Failed mechanical validation gets one retry, then the optional minutes
operation fails without discarding audio or transcripts. An evidence JSON sidecar
records source citations and review-required status; classifications, summaries,
translations and completeness are still AI interpretations, not verified facts.
Empty extraction is not proof that nothing was discussed. Real Qwen EN/ES and
long-meeting accuracy/performance acceptance are required; unit tests use mocks.

## CI evidence and next acceptance

Run #45555606107 at 228163d: engine 101 passed / 2 skipped; browser 11
passed; dependency-audit SUCCESS (No known vulnerabilities found in scanned
Python environment). Both jobs passed. This is historical evidence for that
commit, not the newer minutes changes. No installer packaging.

Expose the evidence sidecar in Results, show IDs of empty extraction blocks,
reject duplicate JSON keys, and retain distinct interpretations of a shared
quotation. Add a synthetic bilingual local-only acceptance rubric in
qa/minutes_acceptance.py (requires existing Ollama/Qwen on verified Windows
storage). No hardware evaluation has been performed by this checkpoint.

## Native review checkpoint and minutes regression

Run #45556005729: Python dependency audit succeeded; engine test collection
failed because a stray quote in test_minutes_evidence.py caused a SyntaxError.
Corrected the typo. Browser tests were skipped in that failed run. Added an
evidence-only native provenance report to the future manual QA packaging path,
including exact local build-input hash matches, PE version metadata, NVIDIA
binary flags and candidate Chromium notice files. See docs/NATIVE_RELEASE_REVIEW.md.
The exact frozen binaries, native vulnerability review and qualified license
review are still outstanding. No installer built; new tests require CI.

Release-gate hardening: all ten mandatory requirements must be explicitly present
and true; empty or partially removed requirement sets cannot authorize release.
Malformed or duplicate-key JSON and non-boolean approval fail closed. The current
gate remains unchanged and blocked. This guard does not validate legal sign-off
or hardware evidence by itself; those must still be reviewed separately.

## Component migration and actual worker IPC

Added an explicit unchecked repair option for legacy or invalid component receipts.
Stage and verify new vendor bytes before replacing a component, retain old files
under a unique backup directory, avoid moving models/recordings, and serialize
component setup via OS-backed file locks. Reject unsafe reparse points and writable
hardlinked partials. Add offline repair failure and preservation tests. Add a
real subprocess ping/error/cleanup test (no model download or GPU). This tests
source-mode IPC, not the frozen executable or hardware inference. Windows CI and
interactive installer/ASUS acceptance remain required; no installer was built.

## Windows worker lifecycle regression

Run #45556632831: 129 passed, 1 failed, 2 skipped; Python dependency scan
passed. The actual IPC handshake succeeded but Windows virtual-environment
launcher PID differed from the executing Python PID. Correct the assertion to
check the stable worker PID, not the launcher PID. Add an application-owner
watchdog and private stop marker, with process-tree termination fallback on
Windows, and test the actual executing process's exit using a Windows handle.
Long synthetic and frozen hardware QA now exercise the isolated production
worker rather than the in-process legacy test path. This is not yet hardware
acceptance. The new commit must pass CI; no new installer has been built.

## QA media archive refresh — 2026-11-25

Approved source candidate ccaaf42: run #45557024304, 131 engine tests passed,
2 skipped, 11 browser tests passed and Python dependency audit passed.
Owner-authorized isolated QA run #45557597177 failed before compilation: the
October 20 FFmpeg archive returned Not Found. Upstream has moved to
FFmpeg-Builds/FFmpeg-Builds. Pin the November 24 published shared LGPL 8.1 asset
(ffmpeg-n8.1.3-41-ga8029b6528-win64-lgpl-shared-8.1.zip), 81544256 bytes, SHA-256 dbed3e64d68de76472bf2cd0b0f3250384fb96bac14b635a708e998f6e1d6996,
from the upstream release API. Preserve the existing PyAV source digest,
codec gates and blocked release status. New media binary needs fresh QA; a
published digest is not an independent signature or legal clearance. The dated
upstream asset can expire again; do not use an unpinned latest alias. No installer
was produced in the failed run.
