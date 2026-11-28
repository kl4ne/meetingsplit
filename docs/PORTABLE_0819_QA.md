# MeetingSplit 0.8.19 — guía de revisión en ASUS

Candidato portable autorizado para QA, **no release pública ni aceptación editorial**. Conserva Qwen3.5 9B, procesamiento local y las advertencias de revisión. No desinstalar la versión anterior ni borrar proyectos.

## Descargar y comprobar

1. Abrir [artefacto de compilación QA](https://github.com/kl4ne/meetingsplit/actions/runs/46078575131/artifacts/15236425376) con sesión GitHub iniciada (retención 14 días). Extraer el ZIP exterior: contiene el portable y su archivo .sha256.
2. En PowerShell, desde la carpeta donde está el ZIP interior:

    Get-FileHash -Algorithm SHA256 .\MeetingSplit-v0.8.19-Windows-portable-candidate.zip

   SHA-256 esperado (no importa mayúsculas/minúsculas): `d93c2334a1a2a81d26ef02a89d92952f268cb7695c3dd587fc1d80ba08ba05e5`. Si no coincide, no ejecutar.
3. Extraer el ZIP interior completo en una carpeta nueva de disco interno, no sincronizada, p. ej. D:\MeetingSplit-0.8.19. Mantener MeetingSplit.exe junto a _internal. El paquete ocupa unos 1.18 GB extraído; reservar espacio adicional para audio, transcripción y modelos.
4. Abrir MeetingSplit.exe. Confirmar 0.8.19. No se requiere Setup. Conservar la 0.8.18 en su carpeta.

## Primera prueba (la más útil)

Utilizar una grabación corta conocida, de preferencia ya probada con 0.8.18. En opciones elegir el idioma de entrada correcto, idioma de informe español (o el que corresponda), resumen y minuta, y generación local con Qwen3.5 9B. Confirmar ruta de salida interna no sincronizada y el modo CPU/GPU que se quiere evaluar. No cambiar modelo para comparar. Verificar que la interfaz funciona, que se genera la transcripción y que se conserva el audio. Leer el Markdown, contrastarlo con la fuente: temas, decisiones, tareas, responsables, plazos, cifras y propuestas. Revisar advertencias y MINUTA_EVIDENCIAS.json; una cita no certifica significado. Registrar duración y discrepancias; comprobar RESULTADOS_COMPLETOS.zip. No enviar grabaciones privadas ni transcripciones personales a GitHub.

Después de primera prueba satisfactoria, evaluar EN/BOTH, reunión larga, NVIDIA y CPU, cancelación/reanudación, recuperación y los cinco paneles. Si aparece un fallo, guardar diagnóstico, versión, ajuste usado y texto pertinente anonimizado. No repetir pruebas largas sin diagnóstico.

## Diagnóstico opcional

Desde la carpeta extraída, PowerShell:

    .\MeetingSplit.exe --self-check "$env:TEMP\meetingsplit-0819-self-check.json"

El diagnóstico no procesa audio ni valida fidelidad editorial. El runner Windows superó las cuatro comprobaciones obligatorias (Qt WebEngine, FFmpeg, ffprobe y Whisper); CUDA no estaba disponible allí. El ASUS debe comprobarse por separado. No interpretar un self-check verde como aceptación de la minuta o seguridad/licencias completas.

## Evidencia de compilación

- [Run 46078575131](https://github.com/kl4ne/meetingsplit/actions/runs/46078575131)
- [Recibo, inventarios, licencias y self-check](https://github.com/kl4ne/meetingsplit/actions/runs/46078575131/artifacts/15235574583)
- Fuente: 448a8502521192034e939145d43cc6b18b90898e. ZIP interior 463728021 bytes, 696 archivos verificados.
- CI: 359 pruebas motor, 2 omitidas, 11 navegador y auditoría.
- No Setup, no release/tag/merge, release_allowed=false. El repositorio es público; los artefactos de Actions no tienen privacidad de acceso garantizada.
## Primera prueba del propietario — resultado

El propietario ejecutó 0.8.19 y confirmó funcionamiento NVIDIA excelente. El resultado privado fue revisado localmente: manifest NVIDIA GPU, Whisper medium, 273 segmentos, cinco MP3/checkpoints íntegros y ZIP sin errores. Partes 3–5 silenciosas; señal termina ~24m07s de 58m49s. No repetir la grabación para diagnosticar GPU. La minuta necesita revisión editorial (100 temas, 87 pasajes sin síntesis, 26 review, 2 uncited, 8 avisos compuestos). La próxima reparación se centrará en fragmentos ASR y contexto, sin alterar audio/transcripción GPU. Otros modos, carga larga, recuperación y demás requisitos pendientes. No publicar grabaciones ni texto.
