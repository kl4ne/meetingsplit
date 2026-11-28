# Comparación contextual privada (herramienta de QA, no nueva versión)

Esta herramienta experimental utiliza el ZIP original de resultados 0.8.19.
No modifica MeetingSplit.exe, no instala software, no abre los MP3, no ejecuta
Whisper y no comparte la transcripción con servicios externos. El paso de
inspección no se conecta a Ollama. El paso de inferencia requiere consentimiento
explícito mediante su comando y un servicio Ollama **ya activo** en 127.0.0.1:11434,
con Qwen3.5 9B local y el digest exacto de las pruebas. No inicia servicios ni
descarga modelos. Se aceptan 0.40.6 (runtime del portable, distinto al runner) y
0.40.18 (runner QA); la diferencia se registra, no se afirma equivalencia.

## Requisitos y ejecución

Solo Python ya instalado (preferentemente 3.14.10 como CI); módulos de biblioteca
estándar, sin pip. Extraiga este pequeño paquete de QA en una carpeta local interna
no sincronizada, distinta de la del portable. No requiere instalar MeetingSplit.
Si Python o el servicio/modelo verificado no están disponibles, deténgase y
comunique el bloqueo; no cambie su instalación ni descargue componentes.

En PowerShell, desde la carpeta extraída, con rutas reales entre comillas:

    py -3 qa\minutes_private_compare.py "D:\ruta\RESULTADOS_COMPLETOS.zip"

Esto solo imprime métricas y comprueba las citas de la versión original. No
genera archivos. Para autorizar la comparación real, cierre cualquier trabajo
activo de MeetingSplit; compruebe que su Ollama local ya está disponible y que
la carpeta de salida existe en un disco interno no sincronizado. Ejecute solo
si desea procesar localmente la transcripción privada:

    py -3 qa\minutes_private_compare.py "D:\ruta\RESULTADOS_COMPLETOS.zip" --run-local --output-parent "D:\QA" --consent ACEPTO-PROCESAMIENTO-LOCAL

Se crea una carpeta única MeetingSplit-contextual-QA-* con CANDIDATO_CONTEXTUAL.md,
CANDIDATO_EVIDENCIAS.json y COMPARACION_TECNICA.json. No se copia ni extrae audio
ni se sobreescribe el ZIP anterior. Se verifica el hash del ZIP antes y después.
Se limita a 32 invocaciones de transporte (incluyendo reintentos), 300 segundos
por llamada y 3600 segundos de presupuesto agregado, con cancelación cooperativa.
Esos límites son de seguridad, no estimaciones; el servidor puede tener latencias
de parada. Ctrl+C solicita interrupción de la ejecución. Si falla, el diagnóstico
registra el tipo de error; no repetir automáticamente. No debe ejecutar dos
comparaciones a la vez. La GPU de Ollama es independiente de la GPU de Whisper;
no se fuerza CPU salvo la opción explícita --cpu-only o el fallback existente.

No suba audio, transcripciones ni evidencia privada a GitHub. Compare la nueva
minuta con la anterior y con la fuente; los conteos no prueban calidad. Puede
compartir el diagnóstico técnico revisado en privado, si lo desea. La revisión
de significado, alcance y redacción sigue siendo imprescindible. Este paquete
es exclusivamente QA, no sustituye el portable 0.8.19.
