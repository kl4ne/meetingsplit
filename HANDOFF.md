# MeetingSplit — punto de continuidad para el próximo chat

**Actualizado:** 2026-11-27. **Estado:** portable 0.8.19 ejecutado por el propietario en ASUS; GPU/export positivos, calidad editorial aún pendiente.

## Leer primero

Este archivo es la entrada canónica para reanudar el trabajo sin depender del historial del chat.

- [Plan de terminación y criterios de entrega](docs/MEETINGSPLIT_FINISH_PLAN.md): tareas pendientes, decisiones técnicas, pruebas, empaquetado y cierre.
- [Registro técnico de reparaciones](docs/MINUTES_REPAIR_CHECKPOINT.md): defectos, soluciones, incidencias y resultados históricos.
- [Evidencias y ejecuciones](docs/MINUTES_QA_LEDGER.md): commits, ejecuciones, artefactos, mediciones y límites de las pruebas.
- [Evaluación de aceptación editorial](docs/MINUTES_EDITORIAL_ACCEPTANCE.md): decisión vigente de calidad y entrega.
- [Estado general](MASTER_STATUS.md): incluye antecedentes del proyecto, no sustituye el checkpoint actual.

## Qué hacer al abrir una conversación nueva

1. Conectar GitHub y abrir el repositorio `kl4ne/meetingsplit`. Leer estos archivos desde la rama `fix/minutes-editorial-diagnostics`, no desde main. La documentación más reciente estará en el [PR #7](https://github.com/kl4ne/meetingsplit/pull/7), borrador.
2. Consultar el HEAD actual del PR, main y los últimos jobs de Actions indicados al final de este archivo. Leer el último checkpoint y la evaluación de aceptación. El run 46025742614 es histórico; no volver a tratarlo como activo.
3. Última fuente versionada validada por CI: `448a8502521192034e939145d43cc6b18b90898e` (359 pruebas de motor, 2 omitidas, 11 de navegador, auditoría de dependencias, run #46078498354). El checkpoint documental posterior no cambia el código. Main `de0f22a43a5a1f857ec5d47ded802037b2f34984` sigue en 0.8.18. No confundir CI con aceptación editorial; no fusionar main ni publicar.
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
- El propietario autorizó preparar el portable 0.8.19 de revisión con limitaciones. ZIP compilado y validado, disponible en artefacto QA 15236425376. `qa/release_gate.json` conserva `release_allowed: false`. No hay autorización de publicación pública ni de Setup.

**Siguiente acción concreta:** A/B #46095783519 verde, artefacto 15242903218 SHA/CRC y respuestas inspeccionados, 2 llamadas CPU 313.508s, baseline 2 temas/gaps 6,7,8,9, claim 3 temas/5 afirmaciones/gaps 3,4,8,9. Mejora modalidad/secuencia, pérdida de ejemplo histórico por comillas tipográficas (fila 4), antecedente no sustentado por cita propia y título residual, NO-GO semántico. Nuevo QA 2b88db778f1d5aab3557828b0315ecb4f8af2a2c, workflow #46096627138 verde (51 pruebas, replay 0 inferencia, ZIP 15243294845 SHA/CRC verificados): reparación opt-in de par de comillas exclusivamente en fila completa con original exacto, validaciones intactas, replay exacto sin modelo; CI y ZIP inspeccionados, 5→6 claims, gaps 3/4 recuperados, review 8/9 intacto. No más inferencia de este fixture ni recovery automático. Compact overview rama 8747ea6 #46096249121 verde, artefacto 15243129265 verificado, 23 pruebas/513→425 palabras, cuerpo/evidencia intactos; no síntesis independiente. Próximo evaluar integración experimental con evidencia por afirmación y límites de título/antecedente; sin promover default. No nueva prueba de propietario ni versión/EXE/merge/publicación; 0.8.19/GPU/audio/Whisper/Qwen/main/gate intactos. Ver checkpoint/ledger/plan/aceptación. Commit documental [skip ci].
