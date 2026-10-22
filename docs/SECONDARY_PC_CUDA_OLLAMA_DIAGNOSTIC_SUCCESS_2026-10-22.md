# MeetingSplit v0.8.6 — second physical Windows 11 optional components diagnostic

**Provenance:** User supplied the read-only diagnostic report generated on their **SECOND** physical Windows 11 PC in this conversation, after observing a transient GUI setup error. It contains no underlying individual CUDA/Ollama test report contents or first-failure error. Do not infer things absent from the report. No new app build or GitHub Action was initiated by this analysis.

## What the user-supplied summary DOES establish

- Two detected GPUs: Intel UHD Graphics and NVIDIA GeForce RTX **4060 Laptop GPU**, not the separate ASUS RTX 4070 target device.
- `component_folder_exists=true`.
- CUDA component folders present: `cublas-12.4.5.8`, `cudart-12.4.127`, `nvrtc-12.4.127`, `cudnn-9.1.1.17`, each with present **schema-2 receipt**. Receipt **presence is NOT a fresh SHA audit**.
- Ollama folder `ollama-0.40.6` present with schema-2 receipt.
- `cuda_validation={ok:true, error:null, device:"cuda", validation:"synthetic silence inference only"}`: CUDA's built-in inference probe returned success at the time the source report was generated, NOT a natural-speech benchmark.
- `ollama_validation={ok:true, status:"complete", error:null, model:"qwen3:4b"}`: built-in local model setup reported success, NOT a natural bilingual meeting report review.
- `cuda_report_exists=true`, `ollama_report_exists=true`, `ollama_server_log_exists=true`; raw log contents were not accessed.
- `last_gui_attempt=null` and `setup_report_exists=false` are EXPECTED for the original frozen development QA candidate, which had NO general attempt report. The source-only fix on the QA branch is not installed on the second PC.

## What remains UNKNOWN / NOT PROVEN

- The exact first GUI error text, whether first attempt partially failed but a subsequent attempt succeeded, or which stage the error came from. **Do not assert a root cause**.
- All five downloaded binaries SHA-256 were not independently rehashed by this specific user-side diagnostic.
- Real speech English/Spanish/mixed natural audio accuracy, actual 1–3h throughput and long-run resource measurements, end-to-end GUI document outputs, real interruption/repair/mid-copy cancellation or second-PC installer uninstall regression.
- Final ASUS RTX 4070 physical acceptance, full Chromium/Qt/FFmpeg/NVIDIA legal clearance and Windows publisher signing.

## Immediate safe disposition

- **No need to redownload or reinstall optional CUDA and Ollama now.** Do not delete user's cached component folders, previously verified receipts, model data or log.
- The original install GUI's Prepare button may be reenabled on normal completion or captured error, and retrying can re-run native inference tests; repeated clicks are not diagnostic. Avoid them.
- Continue to a SHORT synthetic, non-sensitive meeting speech end-to-end test on this second PC after confirming its installed MeetingSplit launches. Keep separately from user private audio and data.
- User-reported GUI error's lack of persisted general report was confirmed in prior source review; a development-only patch records `component-setup-report.json` and adds a GUI button. That newer source **has not** been frozen into this QA build nor validated on physical hardware.
- Keep `qa/release_gate.json` release_allowed=false, version 0.8.6, PR #1 draft, main and Integrity unchanged.

**This note reflects user-provided evidence only; no fresh Windows job and no approval to release.**
