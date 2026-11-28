# Comparación privada de afirmaciones (QA, no nueva versión)

Paquete independiente del portable 0.8.19. Reutiliza la transcripción y el registro de extracción reconciliado del ZIP original, verificando IDs, tiempos, citas y metadatos. No vuelve a ejecutar Whisper ni la extracción con Qwen. Se conserva la clasificación de origen: esto aísla la síntesis y no prueba semánticamente la extracción. Mantiene los avisos de revisión y los límites de la estrategia experimental. No sustituye la aplicación.

Extraer en otra carpeta interna, no sincronizada; Python 3 ya instalado, no pip. Ollama debe estar activo en loopback con el modelo local/digest exacto (Qwen3.5 9B); no instala, descarga ni inicia servicios. No se abre ni extrae el audio. Usar el ZIP original 0.8.19, no el JSON del candidato anterior.

Inspección sin conexión o escritura:
    
    py -3 qa\minutes_private_compare.py "D:\ruta\RESULTADOS_COMPLETOS.zip" --claim-reuse

Si la inspección funciona y acepta procesar localmente la transcripción, cierre trabajos MeetingSplit activos, deje Ollama activo, seleccione carpeta existente interna no sincronizada:

    py -3 qa\minutes_private_compare.py "D:\ruta\RESULTADOS_COMPLETOS.zip" --claim-reuse --run-local --output-parent "D:\QA" --consent ACEPTO-PROCESAMIENTO-LOCAL

La comparación utiliza hasta 16 intentos de transporte, 300 segundos por llamada y 3600 segundos de presupuesto cooperativo; no son estimaciones. Muestra el progreso por ventana, no el texto privado. Ctrl+C solicita cancelación. No ejecutar comparaciones simultáneas, ni reintentar ciegamente. Ollama elige aceleración; CPU no forzada salvo opción explícita o fallback existente. La prueba integral por CPU anterior agotó ambas ventanas; no se garantiza rendimiento ni calidad en el ASUS. Se crea una carpeta MeetingSplit-claim-QA-* con CANDIDATO_CONTEXTUAL.md, CANDIDATO_EVIDENCIAS.json, COMPARACION_TECNICA.json. Si el presupuesto se agota puede quedar solo el diagnóstico. completed=true indica documento escrito, no aprobación; thematic_output_present y windows_without_themes muestran fallos de síntesis. La vista ejecutiva combinada es un panorama de títulos y conteos, no síntesis independiente. Las referencias literales no certifican sujeto, significado o modalidad.

El ZIP original se verifica antes y después y no se sobreescribe. No publique transcripciones, citas, audio ni evidencias privadas en GitHub. Puede compartir los resultados revisados en privado. Sin argumento --claim-reuse se conserva el comparador contextual histórico, no es la prueba nueva. No cambie de modelo o instalación si hay bloqueo.
