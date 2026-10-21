## v0.8.6 — Readability pass
- Increased UI typography two steps throughout all five English/Spanish screens, including dropdowns, status and footer.
- Rebalanced layout to protect visible text and preserve independent, scrollable screens at shorter heights.
- No change to audio processing, CUDA fallback, storage policy, donation handling, or author privacy.

## v0.8.5 — Storage detection, CPU recovery and immediate feedback

- Faster native Windows physical bus detection for internal D: (keeps USB/removable blocked); fallback query capped at 4 seconds. Hardware acceptance still pending.
- Missing CUDA/cuBLAS continues with smaller `small` model on CPU; manifest records the actual fallback model and warns of possible accuracy difference. CPU inference uses less expensive decoding where supported.
- Processing button disables immediately, shows animated activity, and the screen displays elapsed time. Long CPU steps can still take minutes and cancellation may wait for an inference boundary.
- No external audio transmission or changes to PayPal, author credit, or Integrity.

## v0.8.5 — ASUS Windows runtime recovery (development)
- Correct internal D: drive validation with Windows Storage and CIM fallbacks, while rejecting USB and cloud-synced folders.
- The default folder dialog opens from local AppData instead of potentially cloud-synced Desktop/Documents.
- Preflight Windows CUDA 12 cuBLAS/cuDNN DLLs; if missing, choose CPU before inference.
- If CUDA DLL / runtime failure occurs on the first actual transcription pass (lazy generator), retry only that segment on CPU and record the warning and device used.
- Regression tests for GPU failure, storage classification, progress and lack of duplicate transcript rows.
- GPU acceleration still requires compatible CUDA 12/cuDNN 9 libraries installed and discoverable on Windows. No unreviewed CUDA DLLs bundled.
- Not a production release. Requires testing on actual ASUS Windows 11 and RTX 4070 before distribution.

# Change log

## v0.7 — Windows packaging readiness
- Conserva íntegramente el motor y las cinco pantallas v0.6 (UI EN inicial, ES alternativo y firma).
- Autodiagnóstico offline del ejecutable, salida JSON elegida por quien compila.
- Compilación Windows con verificación de dependencias y autodiagnóstico antes de crear ZIP/Setup.
- Icono Windows de alta resolución y workflow Windows manual (no ejecutado).
- Pruebas de regresión añadidas para los contratos de empaquetado.

## v0.6
- Selector English/Español persistente y firma permanente en las cinco pantallas.

## v0.8 — Owner-provided PayPal support button
- Optional bilingual support button; PayPal opens only in system browser by explicit click.
- PayPal SDK embedded once in independent HTML, never in local audio interface.
- Windows packaging now includes `support/`; no .exe or live payments verified yet.

## v0.8.1 — Light-background legibility correction
- Darkened captions, secondary descriptions, labels, action links and copyright on white/cream cards.
- Increased text size for many supporting labels; maintained deep navy and gold on intentionally dark surfaces.
- Updated the native `ui/styles.css` and standalone preview with equivalent CSS.
- Verified EN/ES on five standalone preview screens; 38 selected light-surface contrast checks meet at least 4.5:1 against white; 0 JS page errors.
- No audio processing, PayPal hosted button ID, source data paths, credit, license terms or website repositories changed.
- This is NOT a Windows installer and has not been verified on the user's machine.

## v0.8.3 — Direct PayPal link and author privacy
- Replaced nonworking local PayPal page/embedded widget with direct external HTTPS NCP PayPal link.
- Made optional support button larger, high-contrast gold and keyboard-focusable.
- Removed clickable author name and personal digital-card URLs from application and README.
- Retained copyright, EN/ES UI, local audio privacy, safe slicing, and contrast improvements from v0.8.1.
- Not yet packaged/tested as native Windows EXE.
