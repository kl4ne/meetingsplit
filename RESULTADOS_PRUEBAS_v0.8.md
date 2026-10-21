# MeetingSplit v0.8 — Verificaciones ejecutadas

Fecha: 2026-10-20. Entorno de ejecución: Linux (pruebas de fuente y Chromium), **NO Windows 11**.

- `tests/test_paypal_support.py`: **4 passed**. ID y client ID aportados por propietario, SDK confinado a la página externa, botón bilingüe bajo clic, ausencia de solicitud HTTP en vista local, puente de escritorio y empaquetado.
- `tests/test_copyright_support.py` y `tests/test_ui_language.py`: **5 passed**. Copyright, firma, selección inglesa inicial / española opcional y persistencia.
- `tests/test_ui_navigation.py`: **5 passed**. Las cinco pantallas independientes, traducción y controles de visualización.
- `tests/test_audio.py`, `test_planning.py`, `test_output.py`, `test_storage.py`, `test_hardware_limits.py`, `test_cancel_and_integration.py`, `test_windows_build_gate.py`: **21 passed**.
- `node --check ui/app.js`, `node --check ui/locales.js`, Python syntax `py_compile desktop/main.py desktop/self_check.py`: **OK**.

**Total en grupos: 35 pruebas aprobadas.** Hubo inicialmente pruebas con expectativas obsoletas de versión y formato de texto; se corrigieron antes de los pases indicados. Algunas ejecuciones globales se interrumpieron por timeout; se sustituyeron por ejecuciones en grupos que sí terminaron.

## Límites de validación

- El botón de PayPal **no ha ejecutado un cobro real**, no se ha abierto con credenciales del propietario ni se ha confirmado que el PayPal SDK acepte páginas `file://` en Edge/Chrome del usuario. La primera prueba se hará en el navegador predeterminado de Windows. Si falla, solicitar al propietario el **enlace compartible oficial** para abrir PayPal directamente, sin deducirlo del botón.
- No se ha compilado ni ejecutado `MeetingSplit.exe` en Windows 11 o en la GPU NVIDIA RTX 4070.
- Ningún archivo de grabación ni dato privado ha sido subido a PayPal o a terceros desde la app.
