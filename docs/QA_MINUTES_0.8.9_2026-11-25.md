# Meeting Split 0.8.9 · Checkpoint de minutas en Windows

Base de trabajo `89d65358c4ebdff3d2466f1ed0e034eed04cc7df` de `main`. Se mantuvo cerrado el control de publicación. Todas las entradas de audio y texto de esta prueba son sintéticas.

## Causa reproducida en 0.8.8

En la fila 19, a `00:06:00`, la transcripción dice “The board approved the privacy checklist for the internal review.” La fila estaba íntegra en las dos solicitudes para el primer bloque. Ollama 0.40.18 ejecutó `qwen3:4b` con `num_ctx=16384`, temperatura 0 y sin truncamiento de entrada. Ambos JSON terminaron normalmente y ninguno incluyó una cita de la fila 19. El validador rechazó el primero por una cifra ajena a sus citas y aceptó el segundo sin la fila. La cobertura detectó el verbo sin cita y la minuta escribió “Acuerdo por verificar”. El acuerdo se omitió en la extracción del modelo. La reproducción no demuestra que el corte de bloque causara esta omisión concreta.

La evidencia sintética se conservó localmente en `synthetic.txt`, `metrics.json` (solicitudes y respuestas), `validation.json` (respuesta cruda y aceptación o rechazo) y `minutes.md`.

| Archivo | SHA-256 |
| --- | --- |
| `synthetic.txt` | `3a784f99d0bead1c1db649449d7454c12bc9d02c9d17abb6e33b3c45eb8a7a29` |
| `metrics.json` | `a2f566767219cc4364d3be0028e2ffec42109b6ab4f4953e29fb283c66bbae92` |
| `validation.json` | `10f67a179d8879774f3979bf50ddff5ed0239ebb5eefceaae4857f7cfed3f397` |
| `minutes.md` | `f8b0810ca3e5625d686fd3084b492853d8b69d1228c2ca5febd43e533e2eaab0` |

## Reparación

Una pasada independiente recorre todas las filas en orden y conserva afirmaciones explícitas en citas literales. Puede enlazar una aprobación que se refiere a la propuesta inmediatamente anterior o un plazo que identifica expresamente la tarea anterior, incluso si la segunda cita quedó en otro bloque. El enlace exige cercanía temporal. Se conserva el texto original cuando no hay una interpretación validada. Las propuestas sin aprobación explícita conservan su categoría. Los casos condicionales, negados o sin referencia suficiente requieren revisión.

La conciliación separa hechos explícitos que el modelo agrupó y evita que una interpretación con citas de contexto duplique el registro respaldado. La reproducción con exactamente las respuestas crudas de 0.8.8 devuelve una decisión con la cita completa de `00:06:00`, sin advertencia de cobertura para esa fila.

## Pruebas

- Suite del motor en Windows: 165 aprobadas, 2 omitidas. Las dos suites Playwright no se ejecutaron. Se incluyeron pruebas de omisión del modelo, citas suplementarias, propuestas no aprobadas y enlaces que atraviesan ventanas.
- `qa/minutes_long_acceptance.py` genera un caso bilingüe con marcas de tiempo hasta `02:15:00`, 276 intervenciones, 11 bloques y 11 hechos puntuados. Verifica citas, categoría, unicidad, responsables, plazos y montos.
- La primera ejecución de la reparación recuperó los 11 hechos y duplicó tres en el bloque final. La verificación de la conciliación corregida sobre esa salida recuperó los 11 sin duplicados. La corrida de aceptación del portable final se completó.


## Resultado de la aceptación final

Windows 11, Ollama local 0.40.18, `qwen3:4b` con contexto de 16.384. La prueba comparó la misma transcripción sintética de 36.178 caracteres, 276 intervenciones y marcas de tiempo de 2 h 15 min. El candidato se probó con los módulos empaquetados en el EXE extraído.

| Comprobación | 0.8.8 | 0.8.9 |
| --- | --- | --- |
| Hechos correctos, únicos y con los campos y citas esperados | 6/11 | 11/11 |
| Aprobación enlazada entre bloques | Quedó como propuesta | Citó propuesta y aprobación |
| Plazo de la tarea enlazado entre bloques | Ausente | Respaldo en ambas citas |
| Hechos duplicados al final | 3 | 0 |
| Citas ajenas al texto sintético | 0 | 0 |
| Tiempo de la minuta larga | 327,78 s | 334,99 s |

El binario extraído pasó el autodiagnóstico y abrió las cinco pantallas en la prueba de Qt WebEngine sin ventana personal, con versión 0.8.9. Dividió un WAV sintético de tres horas y doce muestras adicionales en 20 partes, con cobertura continua, duración de cada parte comprobada, archivo original intacto y ZIP de resultados válido. El flujo de escritorio de recuperación, con Ollama real, conservó el compromiso de Louise como tarea para el lunes y el presupuesto de $5,000 como tema. Generó la minuta y el ZIP en 9,97 s sin reescribir audio ni transcripción.

El ZIP portátil completo pesa 459.789.829 bytes. SHA-256 `0bb57dcb86be852664dd5d99881f6cb101b9a211bf120c51a984b551d0a5b337`. SHA-256 del EXE `004ac72c6f88be33f888e25d79b4aef62928f65f9b0f76a861fb38d9e7297a83`.

La prueba larga comienza con una transcripción sintética, con intervenciones espaciadas, y la división y recuperación se comprobaron por separado. No cubre una grabación continua de una reunión real, transcripción por CUDA de Whisper, clics en la sesión personal, ni instalación/actualización/desinstalación.
