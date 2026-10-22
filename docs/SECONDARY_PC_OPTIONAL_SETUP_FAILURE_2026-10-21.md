# Physical SECONDARY Windows 11 — optional CUDA/Ollama failure reported (2026-10-21)

The owner reported an **actual error** after selecting and downloading optional
CUDA and Ollama within the MeetingSplit GUI. They observed
`Prepare selected components` enabled again; repeatedly pressing it appeared
to loop, and they could not find `qa-summary-shareable.json`.
**THE EXACT ERROR TEXT, DEVICE GPU, AND FAILED STAGE REMAIN UNKNOWN.**
Do not say that GPU or Ollama was validated or that the download was the cause.

## Source-grounded root of missing report / confusing retry

- The `Prepare selected components` button is part of
  `desktop/component_setup.py`, not the separate secondary PC installer QA
  PowerShell kit `02-PRUEBAS-GUIADAS.cmd`. Only the latter writes
  `qa-summary-shareable.json` after an explicitly guided installer session.
- Historic frozen candidate `90238d6` / `desktop/component_setup.py`
  previously captured exceptions and displayed `Setup incomplete ...` **only
  as a temporary QLabel**. Worker then finishes, enabling the Prepare
  button again; no durable generic report was written for failure at any
  stage. The control is retryable, NOT an infinite background loop by itself.
- CUDA first runs all four package installers, then frozen
  `probe_cuda('small',...)`. It writes
  `<selected-data-root>/Componentes/cuda-validation.json` **ONLY after**
  this probe returns. If package install/extraction failed, this file may
  not exist. Failed NVIDIA inference blocks subsequent Ollama setup even
  if the owner checked both components.
- Ollama writes `<selected-data-root>/Componentes/ollama-validation.json`
  only **after** `setup_ollama()` has actually started. When completed its
  `status` is `complete`, `failed` or `cancelled`. On failure the
  optional `ollama-server.log` may have detailed personal paths; DO NOT
  request or upload raw logs. A successful download of the vendor binary
  does not establish installed local qwen3:4b or successful test.
- Installed component folders with valid `meetingsplit-receipt.json` are
  reused on retry; absent or malformed folders may block installation.
  Do NOT delete these folders or attempt repeated large vendor downloads
  without diagnosis. The physical second PC may lack an NVIDIA GPU.

## User-facing read-only artifact in this conversation

`MeetingSplit-Diagnostico-Opcionales-Win11.zip`
- ZIP SHA-256:
  `ff4047ecef106ccdb033673b74d929ab84b412ec3c2c8ae33c507e097374115f`.
- Small ZIP generated in conversation container (not in GitHub), CRC checked,
  containing `01-DIAGNOSTICAR-SIN-INSTALAR.cmd`,
  `MeetingSplit-Diagnostico-Seguro.ps1`, `LEEME-DIAGNOSTICO.txt`.
- Invoking its CMD in a **standard user session** opens a manual folder
  picker for the application's chosen data root (NOT the installed app
  folder), reads only known local JSON receipts and GPU model; no
  installation or vendor download; produces
  `MeetingSplit-Diagnostico-Compartible.json` alongside the script.
  Reports presence/status, not user data/audio. Error strings have
  best-effort path redaction; user should review before sharing.
- The ZIP is not committed to the repo; do not invent a future sandbox link.
  User's next action is to share generated JSON, or the exact on-screen
  error if the diagnostic cannot find the folder.

## Development-only fix now on isolated branch (not packaged/validated yet)

- `desktop/component_setup.py` `SetupWorker` has been amended to
  atomically persist `Componentes/component-setup-report.json` with
  `stage`, `status`, `requested` CUDA/Ollama and bounded `detail`.
  Covers success, failure and cancelled setup and identifies the specific
  phase: `cuda_download`, `cuda_inference` or
  `ollama_download_and_test`.
- The Qt component dialog now has `Open setup report` / `Abrir informe
  de instalación` button, and failure message includes stage/report name.
- `tests/test_component_setup_reports.py` adds synthetic Qt/worker tests
  for CUDA download, CUDA inference, Ollama failure and retry, cancellation,
  report GUI affordance. **These new tests have NOT yet been run on Windows.**
- Existing frozen binary on the physical test PC is PRE-FIX; opening it
  again will NOT reveal the new report button until later rebuilt/accepted.
- No full installer/PyAV build or GitHub Actions run was triggered during
  investigation; release still blocked. Prefer gathering the actual user
  diagnostic BEFORE modifying native download/install logic or running
  any new builds.

## Next

1. Receive and interpret `MeetingSplit-Diagnostico-Compartible.json`.
2. Distinguish no-NVIDIA, download/ZIP verification, CUDA missing model,
   native runtime inference, Ollama port/server failure, model download
   and failed synthetic minutes based on presence and status.
3. Patch only the confirmed fault, add a regression and run a SINGLE
   narrowly scoped source Windows test if justified (no full PyAV
   compilation), batch with durable-report tests.
4. Deploy candidate only after legitimate packaging QA and user approval;
   do not overwrite the ASUS installation or discard cached components.
5. Preserve MeetingSplit v0.8.6, `release_allowed=false`,
   draft PR #1, main unchanged, Integrity untouched.
