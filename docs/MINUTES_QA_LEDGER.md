# Evidencias de reparación de minutas — registro verificable

Actualizado el 2026-11-27. Repositorio: `kl4ne/meetingsplit`. Los IDs de runs/artefactos corresponden a GitHub Actions. Enlaces de ejecución: `https://github.com/kl4ne/meetingsplit/actions/runs/<ID>`. Los artefactos pueden caducar; no asumir que siguen descargables. No contienen grabaciones personales por diseño. Leer los resultados completos, no solamente la conclusión del workflow.

## Línea base y ramas

| Referencia | SHA / función |
|---|---|
| main al iniciar reparación | de0f22a43a5a1f857ec5d47ded802037b2f34984, 0.8.18, Codex PR #6 ya fusionado |
| PR #7, fix/minutes-editorial-diagnostics | 6b92c8f25ee9314065e3085cc6341d6005bfc30f, último código validado antes de este traspaso documental |
| PR #8 | prueba aislada de extracción selectiva, rama fix/minutes-selective-quote-retry, 95746f9; su cambio ya está en #7, no fusionar de nuevo |
| qa/minutes-varied-long-0819 | 67bda32ab4b73642caf04b13f26d9a658ef3f611, prueba variada activa |
| qa/minutes-final-replay-0819 | 6061b68884406bc3ce2f30b0e9d13f727ed93cdc, replay completo corto |

## Cambios integrados (16 commits de código/pruebas/documentación técnica antes de este handoff)

| Commit (prefijo) | Cambio |
|---|---|
| 2d79cb6 | Trazas QA explícitas y conservar borrador válido si falla revisión. |
| e91e2f9 | A/B sintético corto con referencia y replay. |
| 576b988 | Polaridad de acuerdos, no aprobación distinta de rechazo. |
| e0884ad | Recuperación de párrafos completos verificados. |
| 794acbe, d585f38 | Expectativa de recuperación parcial y títulos de prueba sin números inventados. |
| 7fb2290 | Un reintento acotado de temas rechazados, conserva los aceptados. |
| 95746f9 | Reintento de citas selectivo, IDs afectados y vinculados; no aproximar citas. |
| 4450b91 | Integración de anclas de tema y presentación literal de idioma. |
| f791131 | Estrategia consolidada y clasificación de guía, pendiente y avisos. |
| 37f3879 | Contabilidad de repeticiones descriptivas, advertencias originales, campos de tarea. |
| dccb71d | Integración desktop de localized_editorial, validación y protección de traducciones. |
| 8b78942 | Redundancia de líneas largas y prueba de recuperación adaptada. |
| bf05a2a | Corrección del mock de idioma y diagnóstico explícito de recuperación. |
| 48a3d64 | Propuestas y pendientes en sus secciones, conserva temas originales. |
| 6b92c8f | Discusión explícita se clasifica como tema, no pendiente inventado. |

## Ejecuciones y artefactos principales

| Run | Artefacto ID (si consta) | Resultado observado |
|---|---|---|
| 45950804921 | — | 206 motor, 11 interfaz, 2 omitidas; auditoría limpia. |
| 45951175096 | 15177746760 | A/B real: directo 193.829 s/1 llamada, pipeline 891.066 s/5; ambos con errores semánticos. |
| 45954020095 | — | 215 motor +11 interfaz, 2 omitidas. |
| 45954418778 | — | Fallo de fixture por número en título; corregido sin relajar guarda numérica. |
| 45954649481 | — | 220 motor +11 interfaz, 2 omitidas. |
| 45955097281 | 15178636016 | CI correcta con recuperación acotada de temas. |
| 45955174164 | 15179585459 | Pipeline real reparado: 819.771 s/5 llamadas, 6 temas, cero lagunas editoriales detectadas, un fallback; narrativa omitió dos temas a pesar de IDs. |
| 45959062442 | — | 89 pruebas de extracción selectiva. |
| 45959366639 | 15180376379 (auditoría) | 237 motor +11 interfaz, 2 omitidas, auditoría limpia. |
| 45959540874 | 15180570776 | Replay recuperó 6/6 temas; sin inferencia. |
| 45959825859 | 15180493657 | Consolidado real: 614.171 s/4 llamadas, reintento selectivo 44.798 s vs 252.428 s histórico. |
| 45993971134 | — | Fallo SyntaxError por expansión JS de sustitución de cadena; archivo restaurado desde versión sana y patch literal. |
| 45994422839 | 15195382415 | 100 pruebas, 8/8 checks replay de clasificación. |
| 45994530781 | 15194219125 (auditoría) | 243 motor +11 interfaz, 2 omitidas. |
| 45994579450 | 15196553252 | Largo repetitivo real: 276 filas/11 bloques/36,178 chars, 1735.341 s/16 llamadas; 11/11 hechos correctos, pero 4 bloques vacíos y 15 registros review. Falló aceptación estricta. |
| 46000635732 | 15198380886 (auditoría) | 253 motor +11 interfaz, 2 omitidas. |
| 46000677544 | 15198485540 | 39 pruebas y 5/5 replay repeticiones; 112 filas de 4 bloques y 15 reviews contabilizados, sin borrar diagnóstico. |
| 46001580090 | 15198461769 | 19 pruebas, traducción 3/4, 30.54 s/1 llamada; plazo excluía viernes. |
| 46008752302 | 15201659731 | 24 pruebas, 3/5 traducciones, 27.243 s/1 llamada; 2 plazos rechazados. |
| 46009865198 | 15202657089 | 33 pruebas, 5/5 traducciones en replay offline, restauración acotada de día, hechos y registros originales intactos. |
| 46010385069 | 15203317506 (auditoría) | 276 pruebas, 1 fallo mock de recuperación sin soporte de traducción; 2 omitidas. |
| 46010555628 | 15203432244 | 41 pruebas y replay 7→5 temas, conserva fragmento único y 11 hechos. |
| 46015055749 | 15205557241 (auditoría) | 280 pruebas, 1 fallo recuperación needs_review por frases del mock rechazadas; 2 omitidas. |
| 46015163014 | 15205494850 | Motor integrado real: 41 preflight, 14/14 checks, 875.204 s/4 llamadas, 4557 chars. Un review de discusión; sin fallos de traducción; duplicación. |
| 46023661916 | 15211695482 (auditoría) | 281 motor +11 interfaz, 2 omitidas; recuperación pasa. |
| 46023822998 | 15212165509 | 30 pruebas, replay 6→4 temas mostrados, propuesta/pendiente pasan a sección propia; 4557→3912 chars. |
| 46024213286 | 15212011213 (auditoría) | 283 motor +11 interfaz, 2 omitidas. |
| 46024353373 | 15211181219 | 32 pruebas, exactamente un review de fila 12 recuperado como tema; demás registros iguales. |
| 46024899679 | 15211811984 (auditoría) | Última CI integral: 291 motor +11 interfaz = 302 aprobadas, 2 omitidas; auditoría sin vulnerabilidades conocidas. |
| 46025010689 | 15210253968 | Replay completo con los 4 requests exactos, 9/9 checks, ningún review sin resolver en ese fixture; mantiene revisión obligatoria. |
| 46025742614 | 15214500646 | Falló aceptación: 16/17 hechos, 8/9 temas, 2 traducciones rechazadas; 1831.884 s / 10 llamadas; 71 filas, 3 bloques. |

## Interpretación de rendimiento

- El caso corto directo de 193.829 s no es equivalente a la aplicación: no garantiza fuente, inventó destino de presupuesto, mezcló fechas y trató no aprobación como rechazo.
- Pipeline inicial 891.066 s. Primera reparación 819.771 s. Consolidación 614.171 s (aprox. 31% de ahorro observado en esa prueba). Motor localizado integrado 875.204 s (aprox. 1.8% menos que el inicial). No se garantiza 31%; variación de runner y respuestas. Comparaciones son CPU Linux sobre fixture sintético, no ASUS.
- El reintento selectivo redujo una llamada observada de ~252 s a ~45 s, conservó 10 registros y reintentó 2 IDs. No extrapolar a todas las reuniones.
- El largo histórico de 11 bloques no es el largo original de 29 bloques del ASUS; el caso variado de 71 filas tiene 2h15 de cronología, no de habla continua. La validación larga densa y variada sigue pendiente. Un replay es una reconstrucción de respuestas existentes, no una nueva ejecución del modelo.

## Defectos originales y protecciones relevantes

La extracción original falló porque una cita agregó “los” a “atención a visitantes”. No tolerar aproximaciones. El modelo atribuyó “se acordó preparar ejemplos” a una conversación, y “fue rechazada” a un texto “Not approved.”. La revisión narrativa asignó IDs de confidencialidad y ejemplos al inventario; referencias correctas formalmente no bastaron. Instrucciones del manual con “should” se volvieron propuesta; una pregunta explícitamente sin responsable/plazo se clasificó review. Se corrigieron avisos separados, presupuesto literal, plazos y presentación bilingüe. Traducciones de by Friday/Thursday cambiaban a antes de; se restaura relación exacta solo cuando un caso estrecho permite hacerlo y pasa validación. No tratar todas las paráfrasis como seguras. Las tareas repetidas no se deduplican como simple texto de fondo. Mantener advertencias originales.

## Evidencias históricas que faltan

El handoff técnico original de 0.8.18 indicó 16,037 palabras, 270 filas, 29 bloques, 2h15, 1529.34 s en ASUS RTX 4070, 4 acuerdos/2 tareas/presupuesto correctos, 198 temas aceptados, ocho lagunas y 15 fallbacks en 38 requests, estado needs_review. Los archivos exactos `synthetic-transcript.json` / `expected.json` y salida de QA estaban en la estación Windows del propietario, no en el repo; no se dispone de las respuestas brutas de ese caso. Estos números son contexto reportado, no una verificación independiente. Si se recuperan, fijar hash y origen y volver a evaluar con el motor nuevo. No usar el digest antiguo Qwen3:4B del harness histórico.

Ante un artefacto caducado, este registro y `MINUTES_REPAIR_CHECKPOINT.md` preservan los hechos conocidos, pero no reemplazan las bytes originales. Copiar los resultados sintéticos esenciales y referencias a commits cuando sea posible; nunca guardar secretos o transcripciones reales en repo público.

## Estado de cierre

Código de minutas probado en PR #7; falta resultado del caso variado, validación de volumen denso/semántica, numeración, portable y aceptación ASUS. Release gate permanece cerrado. Ningún paquete nuevo de 0.8.19 se ha creado. No confundir la anterior prueba de paquete 0.8.18 de Codex (#45944749555, artifact 15173838121) con una compilación de estos cambios.

## Varied source QA — result verified (2026-11-27)

Run #46025742614 failed acceptance, artifact 15214500646 downloaded and inspected (result.json, evidence.json, trace.jsonl, minutes.md, transcript.txt, environment.json). 71 rows / 1067 whitespace-separated words / 7612 chars / 3 source blocks, 1831.884 s CPU, 10 requests. 16/17 expected structured outcomes matched; missing notice row 64 ("Se anunció que el material de consulta está disponible en recepción."). False proposal row 36 (description of technical instruction vs pedagogical recommendation), false pending row 67 (fictional example of unresolved question), row 68 classified review from model proposal though source only says "Se habló de preparar ejemplos prácticos…". No ungrounded citations. Only 8/9 thematic sections cited; archive rows 56,57,59,60,61,62 ALL absent from editorial themes despite extracted topic evidence for five of them. Thirteen unique descriptive rows absent across sections; validator reported zero editorial gaps because it detects rejected themes, not uncited input. Important design defect. Two translation rejects: item 4 source "Ana Ruiz will send the visitor guide by Friday.", raw due "by Friday", correct translated "a más tardar el viernes" rejected by literal due display check; item 38 proposal "extend reception hours to Sunday" translated "hasta el domingo" (ambiguous endpoint, not addition of Sunday), correctly leave unresolved rather than relax deadline guard. Four other translations accepted including two protected weekday restorations. Extract block 1 full retry ~341 s because model translated due literal; block 2 full retry ~352 s for numeric mismatch. Actual document also calls discussion proposals in themes and executive summary omits some categories' substantive content. No quality acceptance. Next: fix omitted input accounting and narrow classification/weekday issues; reuse recorded responses, targeted inference only where necessary. Full dense long case and both languages still pending. Main/version unchanged.

| Ejecución nueva | Resultado comprobado |
|---|---|
| 46030916887 | 107 pruebas de regresión aprobadas; candidato 57052f9, no integrado. |
| 46031770427 | 42 pruebas, 8/8 criterios; 17/17 hechos, 9/9 temas, 54/54 filas citadas; 377.62 s/5 llamadas; artifact 15214847836. |

## Varied repair continuation — 2026-11-27

Isolated branch `fix/minutes-varied-coverage-0819`: initial candidate 57052f950620f900d966ab308b3dd5b369070a3c passed 107 focused regressions (run 46030916887). Added narrow schedule-inclusion relation guard (extension of opening hours to include Sunday, not ending on Sunday), four regression cases, and an exact recorded-response reconstruction harness. New head 79007fbe0fe8519eba0f36e81ee07982fff7d437, run 46031770427 / job 140617100203 in progress at latest check. Preflight must pass before model setup. Harness revalidates final successful raw extraction per block, validates old editorial replies against original request then retains only themes fully supported by current input, records uncited excerpts, revalidates old translations by immutable source/category/owner/due identity (not index), and calls pinned Ollama only for omissions and still-missing translations. The earlier 30-minute extraction is NOT repeated. This is a hybrid replay plus targeted inference, not a fresh end-to-end pass. No integration into PR #7 yet. Next: inspect logs and artifact varied-targeted-repair, including varied-offline/plan.json and extraction-replay.json and varied-targeted/result.json, evidence.json, minutes.md, targeted-trace.jsonl. If preflight fails, inspect actual reasons before changing validators. If it passes, assess structured 17/17, all nine sections, unresolved omissions/translations and semantic quality; integrate only validated production files/tests, keep QA workflow isolated. Update docs. Main, version and release gate unchanged.

## Varied targeted recovery — verified and integrated (2026-11-27)

Run #46031770427 succeeded, artifact 15214847836. ZIP actually opened: varied-offline/plan.json and varied-targeted/result.json, evidence.json, minutes.md. 42 focused tests passed; offline extraction replay: all 17 structured facts correct, false proposal/pending/review removed, 14 missing excerpts across sections (6+8+0), four translations reused, one pending. Targeted real inference 377.62 s, 5 requests (4 omission repair, 1 translation), 8/8 automated checks, all nine sections and 54/54 descriptive rows cited, zero unresolved reviews, structural gaps, uncited editorial excerpts or failed localization; no ungrounded citations or unexpected structured decisions/actions/proposals. This is a hybrid replay, not fresh full pipeline. 39 raw themes; rendered Markdown is long (12,999 UTF-8 bytes). Manual reading found semantic failures despite green checks: source 33 “Se habló de preparar ejemplos…” became “Se propuso elaborar materiales…”; source 63 “Se habló de revisar…” became “Se propuso revisar…”. Source 2 mentions accessibility information at the counter but its theme only retains welcome vs registration. Source 4 mentions the entrance ramp but its theme omits that detail; source-ID coverage is insufficient. Some unrelated topics combined; “uno prestablegable” is awkward Spanish; “Aprobación del comité de la lista…” is ambiguous. Executive lead samples six themes and lacks broad representation. Structured facts/notice/plazos are correct; no final editorial acceptance. Integrate tested omission accounting and classification/localization guards into PR #7; full CI required. Next priority is proposal polarity in editorial prose and sub-passage fidelity, not another full 30-minute generation. No package, main or release gate change.

## Editorial modality guard integrated — 2026-11-27

Full CI #46033392154: 305 engine + 11 UI tests passed, 2 skipped, dependency audit no known findings. Offline #46033519061: 55 tests passed, artifact 15214819074; exactly 2 of 39 themes rejected, source 33 and 63; other 37 unchanged. Integrate only tested guard and regression file, no experimental workflow. Independently opened artifact 15214847836 ZIP and read varied-targeted/minutes.md and all 39 themes/sources: confirms missing accessibility at reception counter (row 2) and entrance ramp (row 4), inaccurate proposal modality rows 33/63, unrelated themes joined, awkward language ("prestablegable"), and repeated results/chronological sample in executive overview. Raw proposal row 9 theme additionally describes extension as "hasta el domingo" but rendered structured proposal is correct because theme presentation moves it to its own section. Do not count 39 IDs/themes as semantic coverage. Next: targeted QA on exact 4 theme defects; keep all other source and structured records unchanged; evaluate a global grouping/overview approach separately before production. Full CI on new combined revision pending. No main/version/package change.

## Source-first architecture experiment — 2026-11-27

Combined CI #46034100640 succeeded: 313 engine +11 browser =324 tests, 2 skipped, audit no known findings; source head 82cd9827ba7276e1ee354fd920c5617c10bd55ea. Targeted detail experiment #46034184111 failed after 42 preflight tests: assertion requiring both source references 4/18. Actually opened /mnt/data/github-actions-artifact-15215453414.zip in container and read detail-trace.json. Model request 30.8578 s, requested one combined theme with IDs 4 and 18; returned only [4], translated ramp and accessible routes but omitted privacy-guide distinction of public vs personal contacts (18), paraphrased private contacts generically. Do not append ID 18 artificially, do not count this as a repaired theme. Reopened exact artifact 15214847836 and read all 39 themes; cross-topic combinations include rows 11/26, 15/28, 23/27/29, 37/41, 55/57, etc. Confirms a broader architecture problem, not just four regex cases. Independent human-style reference in qa/minutes-detail-recovery-0819 at d8e9e77, qa/references/varied_long_minutes_es.md.

New isolated experiment qa/minutes-source-first-0819 SHA b70a511a18fcc4e4643cbc369238d7686ff1b30f, run #46036960062 / job 140634676558 (model setup in progress when checked). QA-only: derive descriptive excerpts using actual production editorial_input and existing verified structured events; split complete sentences into individual units, preserve compound clauses and exact source references, literal target-language sentences unchanged, translate only other/uncertain-language units in batches of five with existing validator. Model can choose neutral grouping titles, unit IDs and one representative per group, not rewrite the detailed sentences. Strict partition validation checks every ID exactly once; source originals remain immutable. Expected 54 descriptive rows / 55 sentence units used only for assertions, not prompt or selection. Render grouped statements plus extractive overview with a representative from every group and verified structured outcomes. This is not a generic production repair or semantic entailment proof, may be verbose or fail grouping or translation, and may need a real concise executive synthesis. Do not integrate unless manual comparison and independent tests demonstrate benefit. Eight preflight tests, saved units, translations, diagnostics, grouping plan, minutes and trace. Standard pinned Ollama, no extraction rerun. Next inspect actual run/artifact source-first-editorial-qa; compare against reference and decide on architectural direction, rather than repeatedly patching individual paraphrases. If grouping fails, reuse translated units and repair grouping only. No changes to main/version/package/release gate.

## Source-first grouping repair checkpoint — 2026-11-27

Run #46036960062 failed grouping after 8 preflight tests passed. Exact ZIP 15217992924 opened in container; inspected result.json, source-units.json, translated-units.json, translation-diagnostics.json and raw trace. 55 units, 29 literal Spanish, 26 translated, zero translation validator rejects. All units and their literal original source references preserved; reception counter, entrance ramp, privacy-guide distinction and discussion modality recovered. Translations read: largely faithful, some literal/awkward Spanish (e.g. "direcciones generales", "feedback", "la discusión cubrió"); not professional synthesis. 523.210895 s, six atomic translation calls plus one grouping call. Proposed nine groups; duplicated units 6,8,31,38,39 and omitted 7,18; strict validator correctly rejected plan, no report produced. Remaining fixed assignments not semantically certified; some groups mix subjects. New QA-only repair commit 5cb1490af24865cae327fc53c0704683ee87aec5 on qa/minutes-source-first-0819: retain 48 unique assignments, ask model to assign only seven disputed units to existing groups, neutral titles and nonempty fixed cores checked, strict partition after repair, reject unknown/duplicate/fixed-ID changes. Overview selection falls back to first fixed unit if previous representative was disputed. Two new regression tests, offline plan and exact saved-unit validation precede model setup. Reuse all 26 translations; one new grouping call only. Run #46038580739 (in_progress at check). Next inspect source-first-group-repair artifact (group-offline/plan.json; group-repair/result.json, groups.json, trace.json, minutes.md). Review semantic grouping, verbosity, and summary against reference; do not confuse complete partition with professional prose. No production integration, main, version, package or release-gate change.
