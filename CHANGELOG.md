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
