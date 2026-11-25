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
