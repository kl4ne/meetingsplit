# Evaluación de aceptación editorial — 2026-11-27

Estado: **NO-GO para numeración/empaquetado de 0.8.19 según los criterios vigentes**. No modificar el gate ni declarar terminada la versión. Esta evaluación de artefactos sintéticos anteriores no equivale a una ejecución fresca del código integrado final.

## Evidencia estructural reproducible

Código de contabilidad validado por CI: 40fdcea96599634966a9824ce8810d07aa957cdb, blob `0ddd29a9049819cf1e0a54cdfdf12bc362a76d9a`. Se abrieron los cuatro ZIPs exactos y se ejecutó el módulo copiado con las definiciones de fuente y expresiones regulares del mismo commit. No se invocó Ollama. El script `qa/minutes_source_accounting_replay.py` permite repetir el cálculo importando directamente el código del repositorio, si se conservan los ZIPs.

| Caso / artefactos | Frases | Citas editoriales | Estructurados/revisión | Sin cita |
|---|---:|---:|---:|---:|
| Varied inicial 15214500646 | 74 | 39 | 22 | 13 |
| Varied targeted 15214847836 con transcripción inicial | 74 | 55 | 19 | 0 |
| Dense original 15228757968 | 111 | 97 | 14 | 0 |
| Dense, metadatos 15230466749 + temas antiguos 15228757968 | 111 | 97 | 12 | 2 |

Sin cita inicial varied: IDs 19, 22, 23, 27, 29, 53, 55, 56, 57, 59, 60, 61, 62. Dense corregido: IDs 26 y 39, explicación de funciones distintas de instrucción/recomendación y comparación de comentarios/propuestas. El resultado inicial dense tenía citas pero categorías falsas; cero gaps no fue éxito. Las dos frases recuperadas no han sido reagrupadas/traducidas en una generación final.

SHA-256 de ZIPs:
- 15214500646: 4c61d337384d0944471da49522d0977020069490400157bfbf7e00f38bc9ab0f
- 15214847836: 7695b9acdcda014b24d0ab9f2ffe77a839abfbc170f5a902560558bd58bb1188
- 15228757968: a66585053037375de8a6cd8dd92a16f8c3b658c4083ea9878a7fac0150d6ae42
- 15230466749: 6c87b8920965502be3b35c440cfd6bc86d8d87c5344b2f9b425e6e24dea630a1
- 15210253968 (corto replay): 9a78255ecded3b6ed9b4629468689f6d38cb89d87ec0ca248572a8ec97c588a1

## Revisión editorial de artefactos existentes

| Criterio | Resultado de la evidencia disponible |
|---|---|
| Corto: hechos, avisos diferenciados, USD 2,400, compromiso viernes, propuesta no aprobada, sin responsable inventado | Correcto en replay #46025010689; texto redundante y algo rígido. |
| Corto: resumen sustantivo y minuta profesional | Parcial: conserva temas y resultados, pero repite párrafos y registros; comparación con reference.md más concisa. |
| Varied: 17 hechos y nueve secciones | Correcto en replay híbrido #46031770427; no equivale a una inferencia nueva. |
| Varied: todos los detalles sustantivos | Fallo demostrado: fuente 2 requiere información de accesibilidad disponible en mostrador; síntesis solo distingue bienvenida/registro. Fuente 4 indica uso de la rampa; síntesis menciona rutas accesibles, no la rampa. Ambas fuentes tienen cita completa. |
| Varied: modalidad | Salida anterior cambia "Se habló de preparar ejemplos" (33) y "Se habló de revisar" (63) a "Se propuso". Guard posterior de modalidad está integrado, pero esta salida no fue regenerada; no atribuir el error como reproducido en el HEAD actual sin prueba. |
| Dense: 10 hechos y cobertura | Replay corregido preserva los diez hechos, sin falsas operaciones; faltan dos frases en la salida vieja; no es nueva ejecución de localized_editorial. |
| Dense: prosa y agrupación | Parcial/fallo: párrafos extractivos muy largos, títulos de archivos que contienen formación y temas de privacidad mezclados con inventario. |
| Inglés y BOTH | No comprobado integralmente en motor final; #46057746118 valida traducción focal pero no certifica prosa; #46069647403 y #46073480297 fallaron aceptación de estrategias alternativas. |
| Modos summary/minutes/both | CI de código aprobado #46070560237; ajuste adicional a summary-only pendiente de CI. No evaluación editorial completa de tres modos sobre inferencia final. |
| Carga real cercana a 16k palabras/29 bloques | No comprobada. Simulación de capacidad no equivale a inferencia. |
| Portable y hardware | No comprobados; no build 0.8.19. |

La corrección de resumen-only propuesta no añade inferencia: muestra títulos adicionales en vez de remitir a una sección que no existe. No hace que una síntesis de títulos sea equivalente al contenido profesional solicitado.

## Decisión

Mantener `localized_editorial` como integración mejor comprobada. No promover las estrategias experimentales, no repetir las inferencias ya fallidas ni seguir ampliando guardas de fixture sin evidencia. Falta demostrar que las afirmaciones de una minuta profesional son fieles y que todos los temas sustantivos se conservan en texto, además de evaluar el motor final en EN/ES/BOTH y carga larga. La cita estructural y un CI verde no satisfacen esos criterios.

Si se solicita un portable de revisión antes de cumplirlos, requiere una decisión explícita del propietario sobre aceptar un borrador privado con estas limitaciones, sin autorización de publicación ni cambio de `release_allowed=false`. De lo contrario, conservar NO-GO de empaquetado. Próximo paso operativo: validar el arreglo summary-only, luego seleccionar un cambio sustancial con un criterio independiente de aceptación o reconocer el bloqueo de calidad con Qwen3.5 9B y los límites actuales.

## Actualización: revalidación del código integrado

CI a13c474ac7b4182cf613720630dea1aceae7469b verde #46074876355 (340 + 11; 2 omitidas; auditoría). Run diagnóstico [46075439142](https://github.com/kl4ne/meetingsplit/actions/runs/46075439142), artefacto 15234354072 SHA-256 a1a66be3b321f346120f729dde40adeed60d65c3abf5faba2cb5dcc9e549d5e8, revisado. Reproducción estricta no completa: corta faltó la solicitud exacta de traducción 9; varied faltó la nueva solicitud de reparación de 33. Revalidación separada de etapas: 17/17 hechos, 37 temas, 2 gaps 33/63, cero traducciones rechazadas y cero sin cita adicional. Se comprueba que el guard vigente rechaza las falsas propuestas antiguas. Fuentes 2 y 4 todavía pierden información en el texto editorial. No equivale a inferencia final. Corrección de relación de plazo en campo visible pendiente de CI. NO-GO se mantiene; próxima evaluación debe enfocarse en los cuatro pasajes demostrados y no reabrir las comparaciones fallidas.

## Actualización: plazos y cuatro fuentes

CI 6cb0dcd36459889984213e3f518a8aa8c2945626 #46075602257 verde, 353 motor, 2 omitidas, 11 navegador, auditoría. Revisión directa del ZIP 15234354072 confirma que fuente 4 comparte tema con 18; no descartar esa información. Candidato aislado 16abf0da9e3d825316c7df50f0c0d2b0ae7d10cc / #46076686990 prepara detalles literales para 2/33/63 y traducción de 4 por frases. No es detección automática ni reescritura profesional; no elimina las alertas. Resultado pendiente. Puerta editorial NO-GO.

## Actualización: recuperación focal de cuatro fuentes

Run #46076686990 verde: artefacto 15234809448, SHA-256 ba8d3e74ec2577717c75ccae71275c6756dc3378e55e0b36980c5610175b1522 verificado. Revisión manual de 3 citas ES y 2 traducciones de frases EN confirma recuperación de los cuatro pasajes seleccionados; una solicitud, 19.171 s, 17 hechos archivados. Es suplemento de revisión, no detector automático ni minuta profesional regenerada. Nuevo guard genérico de citas compuestas conserva originales cuando coincidencia léxica baja o idioma distinto; pendiente de CI y evaluación exacta. No garantiza significado ni repara prosa, NO-GO se mantiene.

## Decisión de cierre de la ronda actual de ingeniería

**Código integrado validado:** a85cd3e502e55f48b7bf8e7815e44fe2e9733c47, #46077071845, 358 pruebas motor, 2 omitidas, 11 navegador y auditoría aprobada. **Auditoría exacta:** #46077626196, a8944138ccf1b0d549d23786fb458dcfe429240b, ZIP 15236061286 SHA-256 ecb6d531bf0c9847164093fd70c68d2f7c22035e46378baa5bd5febe96531e87, bytes y Markdown inspeccionados, cero solicitudes al modelo.

| Caso | Citas compuestas en revisión | Resultado |
|---|---:|---|
| Corto | 0 | No crece; aún hay repetición entre resumen y minuta. |
| Variado | 2 | Fuentes 2 y 4, +75 palabras por modo; siguen gaps 33 y 63; las citas no sustituyen prosa fiel. |
| Denso anterior/corregido | 1 | Fuente 37 correctamente traducida; aviso conservador. Metadatos corregidos conservan dos pasajes no citados. |

Se conserva el mecanismo de protección. No es verificador semántico y no se modificará el umbral para hacer pasar estos fixtures. La prueba densa usa source_first antiguo, no el motor final. EN/BOTH, carga densa real cercana a 16k palabras y calidad final siguen sin certificación. No hay un EXE 0.8.19.

**Puerta de entrega actual: NO-GO.** No se justifica repetir otro experimento de prompt/regex equivalente. Se requiere decisión del propietario: mantener la calidad editorial como condición previa y aprobar una evaluación de arquitectura materialmente diferente (cualquier cambio de modelo requiere autorización), o aceptar un portable privado expresamente identificado como borrador de revisión, con estas limitaciones, para probar el motor ya mejorado en ASUS. Recomendar la segunda como hito práctico solo si acepta el alcance. No confundir un candidato privado con versión definitiva o release pública; en ambos casos release_allowed permanece false, main intacto. Sin decisión explícita, no numerar ni compilar. El usuario no ha autorizado reducir requisitos con la orden genérica de continuar.

## Autorización posterior del propietario — 2026-11-27

El propietario autorizó expresamente preparar el portable privado 0.8.19 para pruebas, aceptando las limitaciones editoriales documentadas y sin publicación pública. Se habilita el candidato de revisión (numeración y empaquetado QA); **NO-GO editorial y NO-GO de publicación** siguen vigentes. No se ha certificado calidad profesional, generación final bilingüe/larga ni hardware. No cambiar modelo ni falsear requisitos. Fuente versionada 448a8502521192034e939145d43cc6b18b90898e; #46078498354 y #46078575131 pendientes de resultado al checkpoint. No existe aún ZIP verificado.

## Candidato de revisión disponible — 2026-11-27

CI #46078498354 y compilación #46078575131 aprobadas; ZIP verificado 15236425376, 696 archivos y self-check obligatorio Windows. La autorización del propietario habilitó esta entrega de QA, no la aceptación editorial ni publicación. Sigue pendiente evaluación en ASUS del ejecutable exacto, fidelidad profesional, carga larga y salida EN/BOTH. Ver docs/PORTABLE_0819_QA.md. Gate público NO-GO.
## Resultado de primera evaluación real en ASUS — 2026-11-27

El propietario confirma excelente funcionamiento NVIDIA. Manifest 0.8.19 y checkpoints corroboran NVIDIA GPU / Whisper medium, 273 segmentos, generación local completada y ZIP íntegro; Qwen3.5 9B seleccionado. 58m49s de audio exportado, señal hasta ~24m07s, resto silencioso; no es una prueba de 59 min de habla. Sin diagnóstico de utilización GPU o tiempo por etapa. No confundir GPU de transcripción con GPU de Ollama.

Editorial: 100 temas, 87 excerpts sin síntesis (121 iniciales), 26 registros review, 2 uncited, 8 avisos compuestos; 4197 tokens por espacios en el documento vs 2982 palabras de transcripción sin marcas, advertencia needs_review. Lectura del texto contra fuentes confirma exceso de micro-temas, reiteración, pérdida de contexto de fragmentos, atribuciones y significado no respaldados. Dos avisos separados, sin decisión/tarea estructurada inventada. **No aceptación editorial.** Protección expone defectos pero no sustituye síntesis. Usar fixture sintético de ASR fragmentado y contexto para próxima reparación; no publicar contenido de la reunión ni requerir repetición idéntica. El código y el portable permanecen congelados a 0.8.19 hasta una mejora probada. NO-GO público, no fusionar main ni marcar otros gates.

## Nueva evaluación de diseño: fragmentos ASR

Candidato aislado 81ae72fd1497ae5e8d2553218a8967eb1e2050d9 (run #46087671575, in_progress), sin inferencia ni datos privados: agrupación contextual cronológica con fuentes originales y género según contenido. Un ID de unidad no certifica cada cláusula. Preflight estructural y rúbrica independiente pendientes de inspección. No se modifica 0.8.19 ni se declara resuelta calidad editorial.

Preflight contextual #46087671575 verde (14 regresiones; 36 referencias preservadas); A/B focal d446f7184d305501d39a43b0364d8a05f26cd324, run #46087774311, in_progress. Tres llamadas como máximo; aceptación semántica pendiente. No modifica candidato 0.8.19.

A/B contextual #46087774311 revisado (ZIP 15240565472): método anterior timeout; cinco temas contextuales, preservación de ideas principales con matices más fuertes; cita ficticia en revisión y fragmentos 19/20 contabilizados sin representarse. No se prueba superioridad en rendimiento ni semántica. Refinamiento aislado 746ec3c739f37aea8803b94cd6737f186f7ad298 (#46089422183, in_progress) usa citas originales/review_ids, una llamada focal. 0.8.19 y puerta editorial intactos.

#46089422183 revisado, ZIP 15240801926 con hash verificado: 28 regresiones, una solicitud, 130.016 s. Citas originales no bastaron para evitar relación inventada en 19/20; caso ficticio aún rechazado, cuatro gaps. Protección experimental de interrupción 13583ac3fdfbeb4719621a6601d21a125b48d2ec (#46089994282, completed / success), replay sin inferencia; conserva dudas, no certifica significado ni arregla calidad final. No cambio de portable ni gate.

Replay #46089994282 verde, 34 pruebas, ZIP 15240797595 verificado: cuarentena de interpretación de 19/20, citas preservadas; no certifica calidad de prosa restante. No volver a inferir el mismo fixture. Siguiente adaptador aislado y caso independiente. 0.8.19/gate intactos.

Adaptador integral contextual_qa aislado e012dacacd565e3647ad79c3455601a7bc20a15c (#46090234942, in_progress); validación estructural sin modelo y nuevo fixture independiente. Pendiente ejecución real y evaluación editorial; no cambio de portable/default/gate.

Adaptador contextual_qa preflight #46090234942 verde (92 pruebas, contratos mock); ejecución real independiente 09378690b2b356c6c2dad0c7b8531bb1080d9672 (#46090327742, in_progress) bajo presupuesto. Pendiente lectura de la salida. No certifica calidad ni cambia 0.8.19.

Comprobación privada de capacidad: funciones de planificación reproducidas localmente sobre la transcripción real 0.8.19, 273 filas exactas contabilizadas (38 unidades, ocho ventanas, sin pérdidas ni overbudget), cero llamadas. No es una nueva minuta ni aceptación editorial. #46090327742 sigue en ejecución al checkpoint. No contenido privado publicado.

Prueba independiente #46090327742 verde, ZIP 15240789431 verificado: 14 criterios estructurales, 4 hechos correctos, 5 temas, 5 llamadas y 388.45 s, tres gaps. Fidelidad parcial: pierde posibilidad de "puede reducir", repite íntegramente síntesis en overview, añade matices, no inventa operaciones. No aceptación profesional. QA 7bad8132c29f33d2c66d892fb7d707a763444f4c (#46093000998, completed / success), solo compactación visual exacta, replay estricto sin modelo. Próximo hito real privado sujeto a consentimiento/entorno. NO-GO editorial/público intacto.

Replay completo #46093000998 verde, 98 pruebas, ZIP 15242335814 verificado. Cinco respuestas reproducidas, cero llamadas, evidencia original preservada; 12/13 compactados visualmente, 505→513 palabras por explicación. No resuelve modalidad o síntesis ejecutiva. Próximo hito privado real, sujeto a consentimiento y entorno local. NO-GO editorial/público intacto.

Herramienta QA local a6e2d50ca6c6bd38a835b13d867f3ac2e43b55c8 (#46093403762 en progreso) preparada para comparación con ZIP real existente bajo consentimiento explícito, sin audio ni descargas. CI mock no equivale a aceptación editorial; Python y Ollama local activo son requisitos por verificar. NO-GO editorial/público intacto.

#46093403762 verde, 110 pruebas mock; paquete fuente verificado 15242266995. CLI exacto inspeccionó ZIP real privado (273 filas/38 unidades/8 ventanas) sin inferencia ni modificarlo. Comparación real pendiente en ASUS con consentimiento y entorno local existente. No se certifica mejora editorial ni se cambia 0.8.19; gate público cerrado.

## Comparación real contextual en ASUS: mejora parcial, no aceptación

Propietario completó comparación autorizada local; 21 solicitudes/275.44 s, 642 referencias verificadas, 16 temas vs 100, 2376 palabras vs 4197, 72 vs 87 gaps, 57 nuevos IDs, 26 review, dos avisos conservados, cero uncited, 12 avisos compuestos. Tres rechazos operativos; texto bruto no disponible. La revisión independiente de fuente confirma errores de atribución de sujeto, asociación de citas a ejemplos, detalles y omisiones importantes. No equivalencia entre cobertura literal y significado. Mantener NO-GO editorial/público, no promover default ni nueva versión. Próxima reparación de atribución y recuperación acotada sin relajar guardas, resumen no duplicativo. Sin contenido privado publicado.

QA caab2eed8ff1338aff5518d2b0bef591ee07cfc3 (#46095408082, 140825486321 in_progress): atribución por afirmación, motivos específicos, protección de originales y planificación de recuperación, sin relajar guardas. Preflight offline pendiente de inspección; no equivale a aceptación semántica ni modifica versión 0.8.19.

Claim-attribution preflight #46095408082 job 140825486321 completed success. Actual logs: 66 regressions passed (0.25 s), independent fictional fixture passed with zero inference. Artifact 15243031850, Actions-reported SHA-256 a3992d115dabfbfee47c10e0723ad454acd73dcb209ed43fcc3c8c9efcf25754. Verified workflow/logs, not downloaded archive. Structural-only acceptance. Before any new inference, inspect fixture/result and set bounded independent claim-fidelity comparison and recovery plan; no new user trial, no semantic claim.

## Frozen fictional claim attribution A/B — 2026-11-28 UTC

Downloaded and independently inspected exact artifact 15243031850 from #46095408082. Archive SHA-256 a3992d115dabfbfee47c10e0723ad454acd73dcb209ed43fcc3c8c9efcf25754 matches Actions; ZIP CRC clean, six files. result.json confirms 11 rows, one window, zero model calls, recovery target [7]. Mock result preserves claim 1/2 with correct actor and original refs, rejects invented before qualifier on row 7, keeps all 3–10 gaps and 8/9 review, no raw rejected body. Nine rubric criteria and exact source frozen. This is mock evidence, not semantic model evaluation.

New QA-only commit 87501549a53167359babe7d6aa69b11913dd35ec (parent caab2eed8ff1338aff5518d2b0bef591ee07cfc3) on qa/minutes-context-windows-0819, workflow #46095783519 in_progress. New qa/minutes_context_claims_live.py verifies frozen artifact plan, prompt/schema, rubric and exact source; two calls max (one row-level baseline, one claim-local candidate) to loopback pinned Ollama 0.40.18 and Qwen3.5:9b exact digest on CPU, same Spanish context, same transport with JSON schema temperature 0; per-call cap 300 s, cooperative overall 610 s, no retries or recovery inference. Uses existing pinned synthetic CI setup, no external paid inference or owner data. Isolated runner downloads model; no owner machine changes. Both arms retain raw synthetic output and validated result, literal/accounting checks, interrupted sources, actual notice separate, review and candidate recovery targets. No full report or overview generation. A/B compares prompt plus schema strategy together, not isolated effect of one parameter. Must inspect both raw and validated outputs against nine frozen manual criteria, including actor/quote/modality, substantive omissions and warnings. Structural pass is not semantic acceptance. Do not automatically execute any recovery until actual eligible rejection inspected. If missing run or failed setup, inspect status/logs before deciding retry; do not trigger duplicate experiment. No owner rerun, version change, default change, installer, merge or public release. Overview remains outstanding.

## Independent combined-overview presentation experiment — 2026-11-28 UTC

Claim-level focal A/B #46095783519 job 140826683164 still in progress at last check, pinned Ollama/model preparation completed and two-call step running. Do not duplicate or alter that branch during execution. Independent QA branch qa/minutes-compact-overview-0819 based on 87501549a53167359babe7d6aa69b11913dd35ec, new commit 8747ea6cbb82c2cdc34db412dc6ef3a211c00769, workflow #46096249121 in_progress. Implements opt-in deterministic compact combined overview in engine/minutes_overview.py and selects it only for contextual_qa plus mode both. Instead of repeating full narrative and notice paragraphs, displays up to five distinct existing titles (360-character inventory bound), transparent sampled count and structured record counts, not unique events. No new factual prose, no new model calls. Explicitly a navigation digest, NOT a truly independent executive synthesis; cannot correct prior semantic errors. All detailed themes, structured outcomes, references, review and evidence must remain intact. Summary-only and minutes-only rendering, production default and portable unchanged. Seven new focused tests, contextual adapter regressions, strict archived five-response replay using original synthetic run #46090327742 and compaction replay #46093000998. Replay must compare entire evidence object and byte-identical document from detail heading onward, measure word count change; fails if output is not shorter. No private inputs or new inference. Next inspect both runs and artifacts. Evaluate A/B manually first, assess compact overview as presentation alternative only, not final editorial acceptance. No production/default merge, version change, package, installer or publication; preserve release gate.

Compact overview #46096249121 job 140828137472 completed success. Actual logs: 23 passed (0.18 s), exact archived five-response replay, zero model calls, evidence object unchanged, byte-identical detail/review from heading onward. 513→425 whitespace tokens, section before detail 178→90 (includes heading/warning). 17.2% total and 49.4% opening reduction in this synthetic case only. Artifact 15243129265, Actions-reported SHA-256 7b452216c64dddacbb5c974951c3f685c70432695994eb2e7ff3b7d00f229636; logs verified, archive not independently downloaded. Presentation navigation digest remains alternative, not independent synthesis. Claim A/B #46095783519 140826683164 in_progress; next inspect both arms when terminal, no duplicate inference. No private data or changes to portable/default/main/gate.

## Focal A/B inspected and narrow quote-pair repair — 2026-11-28 UTC

#46095783519 job 140826683164 completed success. Downloaded exact artifact 15242903218, SHA-256 77e43add6d6ba24096381d8baa243d635afde6642ac5702de852757b4cf735f4 matches Actions, ZIP CRC clean, 12 entries. Read frozen 11-row source, rubric, raw and validated outputs, result, calls and items. Two CPU model calls (row 105.341s, claim 208.164s; total 313.508s), 8/8 vs 9/9 structural checks; no recovery. Claim strategy slower in this small CPU case, not a speed claim. Row baseline 2 themes, gaps [6,7,8,9], one rejected theme IDs 6/7/8 due unsupported operational assertion (raw added before qualifier without matching source). Claim candidate 3 themes/5 accepted claims, gaps [3,4,8,9], rejections nonliteral_quote (3/4) and possible_interrupted_clause (8/9), zero eligible recovery targets. Manual nine-criterion review: both correctly preserve repair actor, historical-not-current distinction at least partially, do not complete interrupted measure, distinguish clean vs replace, and retain one notice. Baseline loses explanatory sequence and pigment possibility; candidate preserves both but strengthens discussion to need, loses explicit historical instruction and coordinator because ASCII double quote substituted original guillemets on full row 4. Candidate row 5 claim borrows an antecedent from 3/4, not supported by own citation; title retains mention of interrupted communication after claim quarantine. The accepted text is somewhat verbose and neither arm earns independent semantic acceptance; claim-specific literal references are not semantic entailment. Do not relax operational guard or launch automatic recovery. No more inference for this fixture.

Also downloaded and inspected compact overview artifact 15243129265, SHA-256 7b452216c64dddacbb5c974951c3f685c70432695994eb2e7ff3b7d00f229636 matches Actions, CRC clean, three entries. 513→425 whitespace tokens, opening 178→90, five responses replayed, no model calls; exact evidence and detail invariant reported by replay. Actual report has sampled title inventory and category counts, separate full detail and review; not independent executive synthesis; prior semantic issues remain.

New QA-only commit 2b88db778f1d5aab3557828b0315ecb4f8af2a2c on qa/minutes-context-windows-0819, workflow #46096627138 in_progress. Explicit opt-in repair_quote_pairs, default false: only restores original full-row text if exactly two changed characters are a single paired straight double quote replacing one original guillemet or curly double quote pair; requires identical length and all other characters, no multiple/nested pairs, no partial spans, no normalization of words, whitespace, accent, numeric or other punctuation. Actual original immutable source is emitted, never generated quote. Metadata only IDs and indexes, accepted repairs only. All existing validation (including operational guard and interruptions) still runs on original source. Regression tests exact and negative cases; strict replay exact archived raw response and old validated object, expects 5→6 claims and gaps [3,4,8,9]→[8,9] with review 8/9 unchanged, all other claims and notice preserved; no model calls. Need inspect actual CI and artifact before claiming outcome. Next evaluate whether to integrate narrowly improved claim QA into experimental adapter with claim-level evidence maintained and title/antecedent limitation explicit; no general automatic semantic repair. Compact presentation remains separate validated option. No user rerun, private data, release/default/main/portable changes.

Quote-pair replay #46096627138 job 140829343754 completed success, 51 tests passed in 0.18s, zero inference. Exact artifact 15243294845 independently downloaded, SHA-256 c48cb2b2a25bf2bab177789ffeae49069f71a9dca01a650289517fcc7040cb5b matches Actions, CRC clean, two files inspected. Claims 5→6, gaps [3,4,8,9]→[8,9], review [8,9] intact; only row 4 paired typographic repair, original text restored exactly, all other claims unchanged, notice intact. Historical instruction recovered without new model call. Remaining issues: anaphoric detail still not fully supported by claim 5's own row; title mentions rejected interrupted communication; stronger wording on need to review labels and verbosity; independent semantic acceptance remains false. No more inference for this fixture. Next evaluate experimental integration of claim validation with opt-in exact quote repair and compact combined presentation, retain distinct claim-level evidence and review and avoid title carrying rejected claims; tests with synthetic archived responses only where useful. No production promotion or owner retest until material quality improvement.

## Integrated opt-in claim QA — 2026-11-28 UTC

New isolated QA commit 2ab2e7c265716ac6a4a3450042867b2ec57c6b1d on qa/minutes-context-windows-0819, workflow #46097088516 in_progress. Explicit new narrative_strategy=contextual_claim_qa integrates claim-local exact citations, opt-in full-row paired typography restoration and compact combined overview. Existing contextual_qa and production localized_editorial remain separate and unchanged in behavior. Uses existing extraction/reconciliation/localization/cancellation and structured notice preservation. Claim adapter records per-window repairs, neutralized titles and recovery target IDs; recovery is planning only, no extra requests. A partially rejected theme gets neutral localized heading instead of letting unsupported title survive; accepted individual claim evidence remains nested in editorial_themes JSON with union refs for existing accounting. Deliberately disables theme removal and gap compaction in claim strategy so rejected/partial source rows and distinct claims remain visible. Compact overview only combined mode, title/count navigation, not independent semantic synthesis; summary-only keeps existing path. This can increase review length; generic headings lose specificity. Claim-local literal evidence does not resolve unsupported antecedents/modality automatically. Added 9 mode/language combinations and failure/cancel tests, previous regressions and replay of exact archived fictional claim response (mocked empty extraction, deterministic notice, not full archived pipeline). No model inference or private material. Verify CI, inspect artifact, resolve actual failures only. Do not ask owner to rerun or promote default/portable/installer/public release yet. No version changes.
