# Owner decision — permanently CPU-only MeetingSplit v0.8.6 (2026-10-22)

The owner explicitly cancelled the NVIDIA acceleration goal: **"olvida esto de usar la nvidia. usemos siempre el cpu."** The goal is no longer to prove the ASUS RTX 4070 or the separate RTX 4060 laptop. Respect this instruction unless owner changes it.

## Confirmed source changes, scoped QA branch only

1. `engine/transcription.py` always constructs Faster-Whisper `WhisperModel(...,device='cpu',compute_type='int8')`; it never calls `activate_gpu`, probes CUDA, loads an NVIDIA DLL, selects `device='cuda'`, or performs a GPU-to-CPU fallback. The legacy `load_whisper` signature remains usable.
2. Whisper's default and sole UI choice are **`small`** to keep CPU transcription practical. Older jobs selecting `medium` or `large-v3` are mapped to actual `small`, and `manifest.json` separately discloses requested `model`, effective `actual_model`, `device='CPU'` and `execution_policy='CPU_ONLY'`. CPU duration and accuracy are not guaranteed equivalent to GPU inference.
3. `engine/job.py` rejects any non-CPU engine, no longer retries CUDA, and never emits false GPU progress. Partial/cancelled output preservation remains.
4. Optional Ollama qwen3:4b **must also use CPU**: every chat API request includes `options.num_gpu=0`, even if using an existing local server. MeetingSplit-owned server subprocess additionally receives `OLLAMA_LLM_LIBRARY=cpu`, `CUDA_VISIBLE_DEVICES=-1`, `HIP_VISIBLE_DEVICES=-1`, `ROCR_VISIBLE_DEVICES=-1`. No global system settings, other Ollama installation or Windows driver are modified.
5. The in-app optional wizard and Inno postinstall task offer **Ollama CPU only**. A legacy `install_gpu()` call fails closed; runtime `activate_gpu()` is a no-op; `--cuda-probe` entrypoint exits without probing.
6. Five-screen native UI, bilingual locale strings and standalone preview now state **solo CPU** and `Small · CPU recomendado`. The original larger-font style and version 0.8.6 are preserved. The persistent component setup report is retained.
7. QA scripts for one-hour synthetic/hardware acceptance are changed to expect CPU; `qa/release_gate.json` replaces obsolete GPU gates with true CPU-only tests, all **false until proven**; top-level `release_allowed=false`.
8. The Windows PyInstaller build no longer explicitly adds the unused CUDA probe module. CTranslate2 may still have upstream-bundled NVIDIA DLL bytes; although unused, native license/notice review remains a separate release gate. This is **not** a claim that all NVIDIA binaries have been physically removed from distribution.
9. Existing CUDA files/models in user data folders are **preserved**, not deleted or uninstalled. Previously downloaded Ollama qwen3:4b can be reused by policy-constrained CPU inference.

## Validation completed / currently underway

- Minimal Ubuntu source-only QA #39723186879 **SUCCESS: 17 passed / 5 skipped**, `python -m compileall`, `node --check`, CPU-only unit tests, and blocked-release test; no vendor bytes, FFmpeg wheel rebuild, installer or GPU required.
- One justified Windows frozen installer QA #39723395202 was started on commit `1351b8e53f0498136bd74fa0c13a06e367dd1fe4`. It does source-built LGPL FFmpeg/PyAV and old smoke once; requires all source tests, frozen CPU-only self-check, absence of UI CUDA button, real silent install/reinstall/uninstall, native manifest and artifact. **Its result is NOT YET VERIFIED in this document.**
- No live second laptop test is required for GPU acceleration; don't repeat CUDA/Ollama installation or occupy spouse's computer again. CPU-only real-speech and 1–3h workload acceptance can occur on a convenient test Windows device when the candidate passes, with no private recordings uploaded.
- No public Release, no merge of draft PR #1 into main, no changes to Integrity Business Filings, no claim of full native license/security closure or signed publisher until specifically verified/authorized.

## Remaining publication blockers after CPU pivot

- Confirm exact new Windows frozen CPU-only EXE and installer really pass relevant smoke and Qt controls; observe one real EN/ES/mixed speech and Ollama local minutes generation with CPU.
- Measure end-to-end time/RAM on long meetings; 3h CPU may take substantially longer than wall clock and should not be marketed otherwise.
- Complete matching LGPL/Chromium/NVIDIA-bundled-binary licensing/security and interactive GUI installer cancellation.
- Resolve code signing / Windows publisher decision before publishing. Draft QA only.
