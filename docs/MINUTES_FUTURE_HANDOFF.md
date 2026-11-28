# MeetingSplit 0.8.19 — Cierre técnico y reanudación futura

**Fecha: 2026-11-28. Estado: PAUSADO por decisión del propietario. Aceptación editorial: NO-GO.** No hay autorización para continuar experimentos, eliminar Ollama, fusionar el PR ni publicar una versión. Este documento prevalece sobre las instrucciones históricas de continuar pruebas en el ledger, plan y checkpoints.

## 1. Punto de partida y alcance conservado

- Repositorio: [kl4ne/meetingsplit](https://github.com/kl4ne/meetingsplit). Rama de reparación: `fix/minutes-editorial-diagnostics`, [PR #7](https://github.com/kl4ne/meetingsplit/pull/7), borrador abierto sin fusionar.
- Main 0.8.18: `de0f22a43a5a1f857ec5d47ded802037b2f34984`.
- Fuente exacta del portable de revisión 0.8.19: `448a8502521192034e939145d43cc6b18b90898e`; CI #46078498354: 359 pruebas de motor, 2 omitidas, 11 navegador, auditoría aprobada.
- Build aislado `qa/portable-0819-review-448a850`, SHA `d50567c222c91fab13faacef44431eda83a526f3`, run #46078575131. Portable validado en Windows runner, 696 archivos inventariados, SHA-256 ZIP interior `d93c2334a1a2a81d26ef02a89d92952f268cb7695c3dd587fc1d80ba08ba05e5`. Sin Setup ni release. `qa/release_gate.json`: release_allowed=false.
- Mantener audio, NVIDIA, Whisper, CPU fallback, ZIP, interfaz, privacidad y reanudación. No declarar que todos los requisitos de liberación están aprobados: licencia/seguridad, instalador y otros casos de aceptación siguen pendientes.
- El propietario ordenó conservar Ollama y el motor de minutas para una futura solución. La casilla existente **Minuta automática local con Ollama**, desmarcada por defecto, es suficiente para trabajos nuevos sin Ollama. `ui/index.html`, `ui/app.js` y `engine/job.py` se verificaron idénticos a la fuente del portable. No se añade otro control ni se reconstruye. Solo dividir excluye Whisper y Ollama; Dividir + Transcribir con casilla desmarcada no solicita generación; una reanudación/reintento explícito de minutas puede invocar Ollama. La casilla no detiene un servicio independiente.
- Modelo histórico fijado: Qwen3.5:9b, digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`; Ollama 0.40.18 en QA controlado. No sustituir automáticamente, descargar ni enviar datos a servicios externos. Un futuro cambio de modelo requiere decisión y comparación separada.

## 2. Qué se hizo y por qué no se aprobó

| Estrategia / etapa | Evidencia clave | Resultado y aprendizaje |
|---|---|---|
| Directa vs pipeline original | #45951175096, artefacto 15177746760 | 193.829 s/1 llamada vs 891.066 s/5 en CPU. Directa inventó destino presupuestario; pipeline confundió discusión con acuerdo y no aprobación con rechazo. |
| Borrador/revisión, extracción selectiva, consolidación y traducción | #45955174164, #45959825859, #46009865198, #46015163014, #46025010689 | Conservación de borrador válido, trazas QA explícitas, recuperación acotada, citas exactas y distinción de avisos/plazos mejoradas. Consolidado 614.171 s/4 llamadas; localizado integrado 875.204 s/4; corto 14/14 checks y replay 9/9. No prueban calidad semántica. |
| Largo repetitivo | #45994579450, artefacto 15196553252 | 276 filas/11 bloques; 1735.341 s/16 llamadas. 11/11 hechos, 4 bloques vacíos y 15 review; no aceptación. |
| Variado y recuperación | #46025742614 y #46031770427, artefactos 15214500646 y 15214847836 | Inicial 16/17 hechos, 8/9 temas, dos traducciones rechazadas, 1831.884 s/10 llamadas. Reparación híbrida 17/17, 9/9, 54/54 filas citadas, 377.62 s/5 llamadas, pero falsas propuestas y detalles omitidos. Citar filas no prueba cubrir significado. |
| Source-first denso / agrupación y síntesis acotada | #46059887920, #46064492706, #46069171479 | Denso 1899 palabras/40 filas, 24 llamadas/848.779 s; 10 hechos esperados pero 2 propuestas falsas y 1 review. Replay clasificatorio conserva unidades y elimina falsos estructurados; no es inferencia nueva. Coste y prosa siguen sin resolver. |
| Auditoría de contabilidad, presentación y portable | #46077626196, #46078498354, #46078575131 | Cobertura estructural, categorías, advertencias, formatos y empaquetado mejorados. Pruebas verdes y self-check no certifican fidelidad editorial. |
| Ventanas contextuales ASR / referencias originales | #46087671575, #46087774311, #46090327742, #46093000998 | Agrupación cronológica preservando IDs/citas; referencias de unidad demasiado amplias, luego IDs de fila. Comparación focal baseline timeout y candidato 5 temas, 3 gaps. Integral contextual 14/14 checks, 388.45 s/5 llamadas, pero omisiones/modalidad. Replay conserva evidencia; compacción solo cambia presentación. |
| Atribución por afirmación, pares tipográficos y panorama compacto | #46095783519, #46096627138, #46096249121, #46097162360 | Row baseline 105.341 s vs claims 208.164 s; ambos sin aceptación. Reparación tipográfica exacta offline 5→6 claims, advertencias intactas; panorama 513→425 palabras, no resumen independiente. Integración 86 regresiones, replay con extracción simulada, no aceptación. |
| Pipeline completo claim QA / timeout | #46097495438, #46099113043 | Dos ventanas agotaron 300 s, 854.666 s total/4 solicitudes; 0 temas, 20 gaps, 12/17 checks. Replay determinista repara período final/plazo inclusivo, diagnóstico y resumen duplicado; 77 tests, 18 gaps, 0 temas por timeout simulado, sin nueva inferencia. |
| Comparador privado reutilizando extracción | #46099501926, artefacto 15245021290 | 175 tests Windows con transporte simulado; paquete fuente verificado. Reutiliza 39 registros del ZIP original, sin repetir Whisper ni extracción. Consentimiento explícito local, tope 16 solicitudes, conserva fuente. |
| Última generación simplificada | #46142308455, artefacto 15262042793 | Una solicitud CPU, 131.539 s, 410 palabras, structure_pass=true, semantic_acceptance=false. Prosa más natural, pero omitió presupuesto USD 2,400, inventó acuerdo a partir de discusión, alteró abril y sábados del mes, omitió tarea/pendiente del resumen. Incluso con etiquetas y resultados congelados manualmente, no es apta. Se detuvo la experimentación. |

Todos los valores de tiempo y contabilidad corresponden a sus respectivos fixtures y estrategias, no son benchmarks comparables entre hardware, carga, longitud y tipo de prueba. Los replays no son nuevas inferencias. El caso histórico 0.8.18 de 29 bloques/16,037 palabras no tiene sus archivos exactos disponibles en el repo; no confundirlo con casos de 11 bloques, variantes sintéticas o la prueba privada real.

## 3. Pruebas del propietario: evidencia agregada, sin publicar contenido privado

| Indicador | Portable 0.8.19 original | Contextual QA | Claim QA con extracción congelada |
|---|---:|---:|---:|
| Palabras del documento | 4197 | 2376 | 4391 |
| Temas | 100 | 16 | 18 |
| Lagunas editoriales | 87 | 72 | 263 |
| Review | 26 | 26 | 26 |
| Avisos | 2 | 2 | 2 |
| Pasajes sin cita | 2 | 0 | 0 |
| Solicitudes | Sin medición comparable | 21 | 8 |
| Tiempo | No consta | 275.44 s | 608.002 s |

Original: 273 fragmentos, 2982 palabras, 7 bloques, 39 registros (11 temas, 26 review, 2 avisos); cinco exportaciones/checkpoints y ZIP íntegros. Usuario confirmó NVIDIA; manifest corroboró Whisper medium/NVIDIA GPU. No hay telemetría independiente de utilización GPU por Ollama. Últimos clips silenciosos por silencio digital observado en exportaciones; no se dispone del audio fuente para atribuir origen. Contextual QA conserva referencias y resultados, pero omite o altera contenido. Claim QA: 57 afirmaciones aceptadas, 5/8 ventanas sin temas, 116 rechazos (115 citas no literales, 1 relación operativa no sustentada), 14 de 18 encabezados neutralizados, cero reparaciones. ZIP original intacto según comparador. No se dispone de todas las respuestas crudas rechazadas de la prueba privada; no inventar causas específicas. No guardar audio, transcripciones, citas, nombres, hashes privados ni archivos de reunión en este repo público.

## 4. Ramas y ubicación del código experimental

- `fix/minutes-editorial-diagnostics`: PR #7; producción de revisión usa `localized_editorial`. Los caminos históricos `reviewed` / `validated_editorial` permanecen. Archivos centrales: `engine/summarize.py`, `engine/minutes_evidence.py`, `engine/minutes_brief.py`, `engine/minutes_narrative.py`, `engine/minutes_localization.py`, `engine/minutes_overview.py`, `engine/minutes_theme_presentation.py`, `engine/job.py`. Revisar `qa/`, `tests/`, workflows y guía Owll.
- `fix/minutes-varied-coverage-0819`: candidato 79007fbe0fe8519eba0f36e81ee07982fff7d437 (recovery focal).
- `qa/minutes-bounded-synthesis-0819`: 7059816e30c733644002e597d190b5f9b6953550.
- `qa/minutes-context-windows-0819`: 7d747f7b3b9d68208eb8730fd52993b62168b3ff (comparador final); antecesores 81ae72fd1497ae5e8d2553218a8967eb1e2050d9 (ventanas), 09378690b2b356c6c2dad0c7b8531bb1080d9672 (pipeline contextual), 87501549a53167359babe7d6aa69b11913dd35ec (A/B claims), e34734f779dd2579bd6667029d963a58f3ff65ee (timeout), e278a57b1a4782698ac901060c237c27d2658e4a (replay de fallos). Consultar `engine/minutes_context_*.py`, `engine/minutes_claim_frozen.py`, `qa/minutes_private_compare.py` y `docs/PRIVATE_CLAIM_QA.md` en la rama/commit correspondiente, no asumir que están en main.
- `qa/minutes-compact-overview-0819`: 8747ea6cbb82c2cdc34db412dc6ef3a211c00769.
- `qa/minutes-final-bounded-0819`: d06c770ce213af6cbc7de07824ac23d14e7bfaee, `qa/minutes_final_bounded.py`, workflow `minutes-final-bounded.yml`. Solo experimento, no motor integrado.
- No fusionar ramas QA para recuperar historial. Git conserva cada commit; verificar ref/HEAD y diferencias al retomar. Ledger conserva las demás ramas, SHAs y fallos corregidos.

## 5. Causa observada, hipótesis y reglas para una futura solución

Hechos: exactitud literal, validaciones JSON y cobertura de IDs no aseguran quién actuó, modalidad, negación, temporalidad, relevancia ni síntesis. El modelo reprodujo ruido ASR como hechos y perdió significado incluso cuando sus citas eran válidas. Exigir reescritura literal a cada afirmación multiplicó rechazos y lagunas; el método directo y la prosa simplificada también fallaron. El presupuesto temporal en CPU y escalabilidad son limitaciones demostradas. No afirmar que todas las causas pertenecen exclusivamente a Qwen o al prompt: los errores de clasificación, render y arquitectura también están documentados.

Si el propietario autoriza reanudar en el futuro:
1. Leer este cierre y las fuentes citadas; conservar el portable funcional y abrir rama QA aislada.
2. Reutilizar los artefactos sintéticos/replays exactos antes de repetir generación. Una idea futura no implementada es referenciar IDs por afirmación y recuperar texto original por código; la estrategia por fila ya probó IDs y no aseguró semántica. No presentarla como solución demostrada ni reducir controles por conseguir CI verde.
3. Formular una hipótesis nueva y una rúbrica manual independiente **antes** de inferencia. Comparar modelos solo si autorizados, fijando modelo/digest/runtime/prompts/esquemas/límites. Usar casos corto, denso/variado y largo realista; ES, EN, BOTH; summary, minutes, both; cancelación y recuperación.
4. Requerir resumen ejecutivo sustantivo, minuta temática natural sin redundancia, todas las cifras/fechas/plazos, decisiones y tareas únicamente explícitas, avisos diferenciados, citas inmutables, advertencias honestas. Distinguir enseñanza/ejemplo/discusión de acuerdos; no inventar nombres, asignaciones o modalidad. No confundir silencio de fuente con omisión de salida. Medir calidad manual, cobertura semántica y latencia; estructural verde no implica aceptación.
5. Establecer un presupuesto de solicitudes/tiempo y una regla de parada. No repetir trabajo ya pagado. Nada de nueva prueba en ASUS hasta evidencia material positiva; si se usa material privado, consentimiento específico, loopback y copia local sin audio/reextracción cuando sea posible. No descargar modelos ni transmitir datos sin autorización.
6. Integración, nuevo portable, pruebas de hardware y liberación son hitos diferentes. Exigir aprobación del propietario y gates completos antes de publicar. No reanudar automáticamente por leer este documento.

## 6. Evidencias permanentes y respaldo

- [MINUTES_QA_LEDGER.md](MINUTES_QA_LEDGER.md): cronología detallada de ejecuciones, commits, checks, errores, tiempos, resultados y artefactos.
- [MINUTES_REPAIR_CHECKPOINT.md](MINUTES_REPAIR_CHECKPOINT.md): implementación, decisiones y limitaciones técnicas.
- [MEETINGSPLIT_FINISH_PLAN.md](MEETINGSPLIT_FINISH_PLAN.md): criterios y planes históricos (suspendidos).
- [MINUTES_EDITORIAL_ACCEPTANCE.md](MINUTES_EDITORIAL_ACCEPTANCE.md): lectura editorial y motivos NO-GO.
- [MINUTES_EVIDENCE_INDEX.json](MINUTES_EVIDENCE_INDEX.json): 81 IDs de ejecución y 63 IDs de artefactos registrados, con secciones de referencia; no equivale a verificar nuevamente todos los runs. Selección de 25 archivos descargados.
- Se preparó un respaldo adicional para entrega al propietario: `MeetingSplit-0.8.19-respaldo-evidencias-2026-11-28.zip`, 1,553,388 bytes, SHA-256 `715d0bd794b45854520cb3e1b7637457130a85a3ee1528ab7b1e6150e09c5850`. Incluye 25 ZIP originales de Actions, verificados mediante CRC y SHA-256, manifiesto y LEEME. No incluye el portable grande ni todos los artefactos históricos; no está almacenado como binario en el repo. El propietario debe conservar una copia local de este respaldo y del portable. La caducidad de artefactos originales empieza el 4 de diciembre de 2026; los links pueden dejar de funcionar. No regenerarlos solo por caducidad. El repositorio conserva documentación y código, pero no sustituye los bytes de evidencia no archivados.

**Conclusión:** se documenta el trabajo, no se declara resuelto el problema editorial. Conservar Ollama como opción, sin experimentos nuevos y con la versión de revisión actual intacta.
