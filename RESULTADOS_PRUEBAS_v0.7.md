# MeetingSplit 0.7 — Resultados de validación local
Fecha: 2026-10-20
Entorno: Linux + FFmpeg + Chromium. NO Windows 11 ni la tarjeta NVIDIA real.

- Motor de audio, exportación, almacenamiento, límites, cancelación y pruebas de compilación: **21 PASARON**.
- Selector English/Español, idioma inglés inicial, firma permanente: **3 PASARON**.
- Navegación separada (incluyendo distintas resoluciones), perfiles de IA, vista no simulando procesamiento real: **5 PASARON**.

**TOTAL: 29 pruebas automatizadas aprobadas** (ejecutadas en tres grupos por los límites de tiempo de la herramienta).

No se descargó Whisper para estas pruebas ni se ejecutó transcripción por RTX 4070. Una de las integraciones usó voz simulada como texto de prueba y audio sintético con FFmpeg. Tampoco se compiló ni ejecutó un EXE Windows. 

Próxima validación en Windows: ejecutar scripts/compilar_windows.bat con dependencias; usar el autodiagnóstico `--self-check` y luego probar grabaciones bilingües consentidas.
