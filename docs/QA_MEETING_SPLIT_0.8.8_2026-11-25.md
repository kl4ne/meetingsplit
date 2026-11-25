# Meeting Split: checkpoint de la 0.8.6 a la 0.8.8

**2026-11-25 · Candidato de pruebas de Windows, no versión estable.** El código de esta rama conserva el contenido exacto del candidato portátil. No se adjuntan audio, transcripciones, binarios ni modelos. Este respaldo no modifica `main`; la integración posterior debe partir del `main` vigente y preservar sus cambios de empaquetado y licencias.

| Referencia | Valor |
| --- | --- |
| Base de pruebas 0.8.6 | `85193b89f67d0d60f2e864af60d03690518ca01d` |
| Revisión local con la que se compiló 0.8.8 | `868ce86fee7660d99afffc188199b5cbb825dee1` |
| Árbol Git exacto del código 0.8.8, antes de añadir este documento | `bf23d3df549ce621eb71d2c76b1c0e15705f59cd` |
| SHA-256 del ZIP portátil probado (no publicado aquí) | `82f66ae3e9eeed50571a943fed7ea873c28ea8c4673c42173c0549c149c11f6b` |

## Cambios realizados

El [commit de respaldo en GitHub](https://github.com/kl4ne/meetingsplit/commit/410e742fd8438622a83ebcb632b61f135dd6be89) es nuevo, pero su árbol de código coincide exactamente con el de Windows. Las revisiones cortas de esta tabla identifican los commits originales de Windows. No se verificó una 0.8.7 publicada; los candidatos intermedios conservaron la numeración 0.8.6.

| Revisión original | Cambio |
| --- | --- |
| `68572ba` | Corrigió el cálculo de duración a partir de la pista de audio, la división y las marcas de tiempo y la recuperación de transcripción parcial. Añadió el reintento de minutas locales, sin volver a dividir ni transcribir, con actualización del ZIP, avance visible y pruebas de regresión. |
| `b291a64` | Acotó la extracción estructurada en Ollama, desactivó el razonamiento en esa extracción y permitió subdividir una sección que agotara el presupuesto de salida, conservando las citas a la fuente. |
| `623db74` | Evitó presentar acuerdos ya confirmados como propuestas. |
| `45cfb07` | Preservó la cita literal de importes aunque la descripción bilingüe los cambiara y ajustó la validación de evidencia. |
| `d406b52` | Separó decisiones, propuestas, tareas y datos informativos con base en la evidencia. Marcó lagunas de cobertura y dejó los casos ambiguos para revisión. |
| `868ce86` | Unificó la versión 0.8.8 en escritorio, interfaz bilingüe, autodiagnóstico, manifiesto, instalador, metadatos de Windows y controles de empaquetado. |

## Qué se verificó

- Windows con RTX 4070 Laptop: el EXE extraído abrió y renderizó las cinco pantallas; versión comprobada en el EXE, propiedades de Windows y manifiesto. Suite local: **158 aprobadas y 2 omitidas**.
- Se verificaron división/exportación con audio sintético de tres horas y recuperación de una minuta dentro de un ZIP válido sin volver a procesar audio ni transcripción. Esto no prueba la fidelidad de una minuta de tres horas.
- Con Ollama local y `qwen3:4b`, la regresión de audio dejó la tarea de Louise para el lunes como tarea y el dato de $5,000 como información presupuestaria. El flujo de recuperación con el servidor habitual terminó en aproximadamente 56 s.
- Ollama de Windows se actualizó de 0.40.16 a 0.40.18. Se añadió el `qwen3:4b` oficial al almacén habitual; se conservó el modelo existente y el 9B solo se evaluó en un entorno aislado. Son cambios del entorno de prueba, no del código del repositorio.
- La comparación de 4B y 9B usó 16,384 tokens de contexto, tres casos sintéticos y una ejecución por caso. 4B exportó 3/3 minutas frente a 2/3 de 9B y conservó 8/8 montos frente a 6/8. En el caso bilingüe de 30 intervenciones, 4B recuperó 6/12 puntos (55 s) y 9B 8/12 (183 s). El caso breve de 9B se rechazó por atribuciones sin respaldo. Estos resultados no cubren reuniones reales de 2–3 horas.

## Fallas y límites de la 0.8.8

1. **Las minutas pueden quedar incompletas aunque el ZIP se genere.** En el caso de 30 intervenciones, el 4B solo recuperó 6 de 12 puntos esperados y no separó todas las tareas con sus responsables y plazos.
2. **Omisión reproducida:** en la fila 19 a `00:06:00`, la transcripción sintética dice explícitamente que se aprobó una lista de privacidad. La evidencia estructurada no contiene ningún elemento aceptado que cite la fila; aparece una laguna de cobertura. La minuta muestra «Acuerdo por verificar», pero no registra el acuerdo completo. Se pierde antes de renderizar; todavía no se distingue entre omisión en la respuesta de Ollama y rechazo en la validación.
3. **Riesgo pendiente de probar:** la app envía bloques independientes de hasta aproximadamente 4,500 caracteres y valida citas dentro de cada bloque. Una propuesta y su aprobación, responsable o plazo pueden quedar en bloques distintos. No está demostrado que ese límite haya causado la omisión de la fila 19.
4. **El selector general de Ollama no es un arreglo.** Esta revisión envía `num_ctx=16384` y `truncate=false` de forma explícita. No se ha validado una minuta bilingüe de 2–3 horas de punta a punta; tampoco se verificaron el clic manual en el perfil del usuario ni la transcripción de Whisper por CUDA. Esto último es falta de verificación, no una falla reproducida.

**Próximo paso antes de integrar o liberar:** reproducir el caso exacto y guardar, con insumos sintéticos, las filas entregadas, la respuesta cruda de Ollama, el resultado del validador y la minuta. Corregir la etapa que pierde el acuerdo. Probar en Windows una transcripción bilingüe equivalente a 2–3 horas con decisiones, responsables, plazos y montos conocidos al principio, en el medio, al final y a ambos lados de un corte. Verificar también que no invente ni duplique compromisos y repetir las regresiones de exportación. Hasta entonces, no usar esta versión para emitir minutas oficiales sin verificarlas contra la transcripción.
