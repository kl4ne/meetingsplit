# MeetingSplit 0.8 — Compilación Windows y aceptación (2026-10-20)

## Estado verificable

- Fuentes continuadas desde v0.6, sin reiniciar ni tocar Integrity.
- No hay `.exe` nativo compilado ni validado en el entorno de desarrollo Linux.
- `scripts/compilar_windows.bat` prepara un portable ZIP y, si existe Inno Setup 6, un instalador. El proceso **aborta** si faltan FFmpeg/FFprobe, las pruebas básicas o el autodiagnóstico del EXE.
- Al ejecutar `MeetingSplit.exe --self-check <ruta_del_reporte.json>` se verifican sin red las librerías Qt, FFmpeg, FFprobe, Faster-Whisper y la disponibilidad (no obligatoria) de GPU/CUDA. La ausencia de CUDA permite CPU, si el resto está correcto.
- `.github/workflows/windows-build.yml` es un ejemplo de compilación manual en runner Windows 2022, NO se ha ejecutado ni conectado a un repositorio. Necesita revisión del origen/licencias de FFmpeg antes de distribuir el binario.

## En Windows 11 para compilar con Python local

1. Necesita Python 3.11 de 64 bits, conexión a Internet solo para preparar entorno y descargar modelos de Whisper, FFmpeg y FFprobe de procedencia verificada en `bin/` e Inno Setup 6 si quiere instalador.
2. Ejecutar `scripts/instalar.bat` para crear `.venv` y obtener dependencias; no debería solicitar cuentas ni claves API.
3. Ejecutar `scripts/compilar_windows.bat`. Primero ejecuta pruebas de motor, luego compila la carpeta portable, prueba el EXE recién creado y genera ZIP. Si se detecta Inno Setup 6 crea Setup adicional.
4. Inspeccionar `dist/MeetingSplit/MeetingSplit.exe` y, solo después de verificación, probar `dist/MeetingSplit_Setup_v0.8.exe`.
5. Probar una grabación consentida de 5–10 minutos que combine inglés y español, revisar precisión, límites de GPU, carpeta local C:/D:, envío por red (prohibido en el motor, salvo descarga de modelo y acciones externas iniciadas por usuario). Repetir con una grabación de 1–3 horas.
6. Las letras C: y D: son solo ejemplos. Cada instalación pide carpeta local; no usa automáticamente USB, red ni carpetas sincronizadas como destino.

## Alternativa futura: Windows runner en repositorio independiente

Se incluye workflow opt-in `workflow_dispatch` para un repositorio **exclusivo de MeetingSplit**, diferente de Integrity y de los hubs. Requiere subir el código a dicho repositorio y activarlo; este paso NO se ha realizado. El workflow instala FFmpeg desde Chocolatey durante la compilación y crea un artefacto privado. Deben revisarse procedencia, licencias, aviso de atribuciones, posibles advertencias SmartScreen y la instalación real antes de distribuir.

## Antes de hablar de release de producción

- Verificar salida y puesta en marcha del EXE, prueba de instalación/desinstalación en Windows 11.
- Verificar QtWebEngineProcess.exe, plugins Qt, ruta a FFmpeg empaquetado, diálogo de selección de directorio y persistencia EN/ES.
- Realizar ejecución real Whisper GPU y fallback CPU, pruebas de audio bilingüe, memoria, temperatura y largo de tres horas.
- Validar UI a 1366×768, escalado 100%, 125%, 150%, alta densidad 4K.
- Verificar información de terceros, licencia de FFmpeg y falso positivo de antivirus antes de publicarlo.

NO entregar el ZIP de código como si fuera un instalador; el runtime solo es local, sin web app ni servidor de audio.
