# Meeting Split 0.8.9 · Checkpoint de minutas en Windows

Base de trabajo `89d65358c4ebdff3d2466f1ed0e034eed04cc7df` de `main`. Se mantuvo cerrado el control de publicación. Todas las entradas de audio y texto de esta prueba son sintéticas.

## Causa reproducida en 0.8.8

En la fila 19, a `00:06:00`, la transcripción dice “The board approved the privacy checklist for the internal review.” La fila estaba íntegra en las dos solicitudes para el primer bloque. Ollama 0.40.18 ejecutó `qwen3:4b` con `num_ctx=16384`, temperatura 0 y sin truncamiento de entrada. Ambos JSON terminaron normalmente y ninguno incluyó una cita de la fila 19. El validador rechazó el primero por una cifra ajena a sus citas y aceptó el segundo sin la fila. La cobertura detectó el verbo sin cita y la minuta escribió “Acuerdo por verificar”. El acuerdo se omitió en la extracción del modelo. La reproducción no demuestra que el corte de bloque causara esta omisión concreta.

La evidencia sintética se conservó localmente en `synthetic.txt`, `metrics.json` (solicitudes y respuestas), `validation.json` (respuesta cruda y aceptación o rechazo) y `minutes.md`.

| Archivo | SHA-256 |
| --- | --- |
| `synthetic.txt` | `3a784f99d0bead1c1db649449d7454c12bc9d02c9d17abb6e33b3c45eb8a7a29` |
| `metrics.json` | `a2f566767219cc4364d3be0028e2ffec42109b6abba4f4953e29fb283c66bbae92` |
| `validation.json` | `10f67a179d8879774f3979bf50ddff5ed0239ebb5eefceaae4857f7cfed3f397` |
| `minutes.md` | `f8b0810ca3e5625d686fd3084b492853d8b69d1228c2ca5febd43e533e2eaab0` |

## Reparación

Una pasada independiente recorre todas las filas en orden y conserva afirmaciones explícitas en citas literales. Puede enlazar una aprobación que se refiere a la propuesta inmediatamente anterior o un plazo que identifica expresamente la tarea anterior, incluso si la segunda cita quedó en otro bloque. El enlace exige cercanía temporal. Se conserva el texto original cuando no hay una interpretación validada. Las propuestas sin aprobación explícita conservan su categoría. Los casos condicionales, negados o sin referencia suficiente requieren revisión.

La conciliación separa hechos explícitos que el modelo agrupó y evita que una interpretación con citas de contexto duplique el registro respaldado. La reproducción con exactamente las respuestas crudas de 0.8.8 devuelve una decisión con la cita completa de `00:06:00`, sin advertencia de cobertura para esa fila.

## Pruebas

- Suite del motor en Windows: 165 aprobadas, 2 omitidas. Las dos suites Playwright no se ejecutaron. Se incluyeron pruebas de omisión del modelo, citas suplementarias, propuestas no aprobadas y enlaces que atraviesan ventanas.
- `qa/minutes_long_acceptance.py` genera un caso bilingüe con marcas de tiempo hasta `02:15:00`, 276 intervenciones, 11 bloques y 11 hechos puntuados. Verifica citas, categoría, unicidad, responsables, plazos y montos.
- La primera ejecución de la reparación recuperó los 11 hechos y duplicó tres en el bloque final. La verificación de la conciliación corregida sobre esa salida recuperó los 11 sin duplicados. La corrida de aceptación del portable final todavía está en curso.

