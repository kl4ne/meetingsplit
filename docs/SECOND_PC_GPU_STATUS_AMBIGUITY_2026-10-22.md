# Real meeting CPU-vs-GPU report, second physical RTX 4060 — 2026-10-22

**Live user report:** Second Windows 11 RTX 4060 Laptop PC started a short meeting; owner said "lo esta haciendo pero con el cpu... aun no a terminado". Processing was not finished at time of report. Do not claim completion or hardware failure.

## Critical finding in EXACT frozen 0.8.6 source

Original `engine/job.py` emitted the literal progress text
`Transcribiendo audio N de N. En CPU el primer fragmento puede tardar varios minutos; el tiempo transcurrido se muestra en pantalla.`
**unconditionally**, even when `device=='NVIDIA GPU'`. Hence CPU progress words **alone cannot establish fallback**. Need check live output `MeetingSplit-<audio-name>-<timestamp>/manifest.json` -> `device` and `actual_model` after model initialisation, and `warnings` on late native runtime fallback. Do not upload raw manifest if meeting names or Windows paths are personal.

CUDA setup `cuda-validation.json` on owner PC reported `ok:true, device:cuda` with **small** model synthetic-silence probe. Actual job's `load_whisper(model_name)` probes the **selected meeting model** via `probe_cuda(model_name,...) `, which may be medium or large-v3. A successful small probe is NOT proof for medium/large-v3 or sustained inference. A previous report also indicated Ollama qwen3:4b `ok:true,complete`.

Two distinct genuine fallback mechanisms in original source:
1. `load_whisper` detects missing DLL / failed `probe_cuda(selected_model)`, emits `GPU CUDA 12 no disponible (<reason>)...` then starts a **small CPU** model. In original release `manifest.device='CPU'` is saved, but the **reason is only transient UI text**, not saved in manifest.
2. During a lazy real CUDA generator, `engine.job` captures a CUDA/CuDNN error, emits `Fallo de bibliotecas NVIDIA/CUDA. Reintentando el audio por CPU.`, appends an error-bearing warning to `manifest.json`, uses CPU and persists `device='CPU'`.

## Isolated source-only repair, NOT on owner's running PC

- `engine/job.py` now emits truthful per-fragment progress conditionally for `CPU` or `NVIDIA GPU`; it no longer prints misleading CPU warning when GPU is used.
- `engine/transcription.py` gains backwards-compatible optional `on_fallback(reason)` callback; `engine/job.py` persists the stage and bounded reason of an initial CUDA probe/model fallback under `manifest.gpu_fallback`. Lazy fallback persists a different stage `live_transcription` and error.
- `ui/app.js` now translates the new two device-specific progress statuses into English UI.
- Offline synthetic mock tests `tests/test_gpu_progress_truth.py` cover GPU progress, initial CPU fallback, backwards compatibility and delayed lazy CUDA fallback. **These tests were added but have NOT YET been run on Windows.**
- Commits and docs kept on `qa/release-evidence-20261021` only with `[skip ci]`, specifically to protect GitHub Actions minutes. No Windows build, external model download, system or user files affected.

## Next real step

Let the ongoing process continue if it is progressing. The generated `manifest.json` in the output folder is written incrementally even before job finishes; owner can inspect only the `device` field, without sharing private audio or the whole manifest. If it says `NVIDIA GPU`, source progress text alone was misleading. If `CPU`, inspect optional `warnings` (redact local names/paths) and note selected model small/medium/large-v3. If still active with no progress after an unusually long period, use the app's normal cancel button (not forced Task Manager) to preserve completed parts; don't infer deadlock from time alone. Running process cannot pick up code changes until a later properly tested build.

Release remains v0.8.6 `release_allowed=false`; open draft PR #1, main and Integrity unchanged.
