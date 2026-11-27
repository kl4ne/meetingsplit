# MeetingSplit — punto de continuidad para el próximo chat

**Actualizado:** 2026-11-27. **Estado:** reparación de minutas en desarrollo; candidato objetivo 0.8.19, todavía no numerado ni empaquetado.

## Leer primero

Este archivo es la entrada canónica para reanudar el trabajo sin depender del historial del chat.

- [Plan de terminación y criterios de entrega](docs/MEETINGSPLIT_FINISH_PLAN.md): tareas pendientes, decisiones técnicas, pruebas, empaquetado y cierre.
- [Registro técnico de reparaciones](docs/MINUTES_REPAIR_CHECKPOINT.md): defectos, soluciones, incidencias y resultados históricos.
- [Evidencias y ejecuciones](docs/MINUTES_QA_LEDGER.md): commits, ejecuciones, artefactos, mediciones y límites de las pruebas.
- [Estado general](MASTER_STATUS.md): incluye antecedentes del proyecto, no sustituye el checkpoint actual.

## Qué hacer al abrir una conversación nueva

1. Conectar GitHub y abrir el repositorio `kl4ne/meetingsplit`. Leer estos archivos desde la rama `fix/minutes-editorial-diagnostics`, no desde main. La documentación más reciente estará en el [PR #7](https://github.com/kl4ne/meetingsplit/pull/7), borrador.
2. Consultar el HEAD actual del PR, main y los jobs de [Actions #46025742614](https://github.com/kl4ne/meetingsplit/actions/runs/46025742614). Última comprobación: job `140596549351` ejecutando la inferencia del caso temático variado. No asumir que sigue activo ni que pasó. Descargar el artefacto `varied-long-localized-qa` cuando exista y leer `result.json`, `minutes.md`, `expected.json`, `environment.json`, `evidence.json` y `trace.jsonl` antes de decidir.
3. El último código validado integralmente es `6b92c8f25ee9314065e3085cc6341d6005bfc30f` (291 pruebas motor + 11 navegador; 2 omitidas). El commit que incorpora este documento es posterior y exclusivamente documental. Main era `de0f22a43a5a1f857ec5d47ded802037b2f34984`, versión 0.8.18. No fusionar main ni publicar.
4. Seguir el orden y los criterios de salida del plan. Si una prueba falla, examinar la respuesta y el código exactos, reproducir offline antes de repetir inferencia, corregir con regresiones y continuar. Si es posible avanzar con trabajo independiente, hacerlo sin cancelar la prueba activa. No quedarse en reportes de estado si hay una tarea ejecutable.
5. Al terminar cada bloque, actualizar este archivo (siguiente acción, HEAD, ejecución/artefacto y resultado verificado) y los registros relacionados. Guardar commits pequeños, con mensajes y evidencia. Mantener el historial; no reescribirlo.

## Objetivo del usuario

Entregar una aplicación Windows portable que genere un resumen ejecutivo sustantivo y una minuta profesional similar en utilidad a Owll, fiel a reuniones en español, inglés o ambos; no solo pasar validaciones de JSON. El usuario sufrió más de doce horas de iteraciones con Codex y versiones 0.8.6–0.8.18. Eligió continuar la reparación con ChatGPT; el usuario quiere avances concretos, aprovechar pruebas ya pagadas en tiempo y evitar compilaciones prematuras. Al finalizar esta reparación ha autorizado un número nuevo (objetivo 0.8.19, verificar disponibilidad). Prefiere continuar sin pausas innecesarias y trabajar durante Actions cuando no interfiera.

**No cambiar sin motivo:** Whisper/transcripción, soporte NVIDIA y CPU, audio y cortes, UI, ZIP organizado RESULTADOS_COMPLETOS, reanudación, privacidad local y dependencias ya verificadas. El modelo elegido sigue siendo Qwen3.5 9B; no sustituirlo por Qwen3:4B ni usar servicios de IA externos. No introducir servidores de pago ni gastos no autorizados. Los runners estándar utilizados son de un repositorio público; no prometer ausencia absoluta de costes por almacenamiento o futuras políticas. No solicitar una prueba del ASUS hasta disponer de un candidato que merezca esa comprobación. No pedir al usuario información ya disponible en GitHub.

## Estado actual en pocas líneas

- El motor nuevo está **integrado en el borrador PR #7**, no en main. `engine/job.py` selecciona `localized_editorial`; las estrategias históricas `reviewed` y `validated_editorial` siguen disponibles para comparación. El modelo y el servicio siguen locales.
- Prueba corta real integrada: 14/14 criterios automáticos (run 46015163014). Replay completo posterior: 9/9, cero registros de clasificación sin resolver en ese fixture (run 46025010689). Aún no equivale a una aceptación editorial independiente: redacción algo extensa y repetitiva, algunas frases poco naturales.
- Prueba larga repetitiva: 11/11 hechos esperados, pero falló requisitos de bloques vacíos y registros review. El replay contabiliza repeticiones sin borrar advertencias, la posterior presentación traduce cinco entradas y reduce siete temas a cinco. No presentar estos replays como una inferencia nueva del motor final.
- Prueba temática variada actual: run 46025742614, rama `qa/minutes-varied-long-0819`, SHA `67bda32ab4b73642caf04b13f26d9a658ef3f611`, 71 intervenciones distintas (54 descriptivas, 17 resultados), nueve temas, cronología de 2 h 15 min, **no** equivalente a 2 h 15 min de habla continua. Terminó con fallo de aceptación; véase último checkpoint y ledger. 16/17 hechos, 8/9 secciones, dos traducciones rechazadas.
- Falta un caso largo denso y variado, y validación del portable exacto en Windows/ASUS. El fixture histórico de 29 bloques no está disponible en el repositorio. No confundirlo con los otros casos.
- No se ha incrementado versión ni construido EXE en esta reparación. `qa/release_gate.json` conserva `release_allowed: false`. No hay autorización de publicación pública ni de relajar requisitos.

**Siguiente acción concreta:** CI de 6cb0dcd36459889984213e3f518a8aa8c2945626 #46075602257 verde: 353 motor, 2 omitidas, 11 navegador y auditoría. Nuevo candidato aislado qa/minutes-four-source-repair-0819 SHA 16abf0da9e3d825316c7df50f0c0d2b0ae7d10cc; [run #46076686990](https://github.com/kl4ne/meetingsplit/actions/runs/46076686990) en progreso. Cuatro pasajes 2/4/33/63 verificados en ZIP 15234354072; tres citas españolas literales y una única traducción de dos frases inglesas de 4, sin reescritura ni reintento. Ver preflight y artefacto four-source-detail-qa, cotejar checklist, no promover como síntesis profesional ni borrar gaps. Calidad editorial NO-GO; no numerar, compilar ni modificar main/gate. Leer último checkpoint/ledger/plan/aceptación. Commit documental [skip ci] no cambia el código validado.
