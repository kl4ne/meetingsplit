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

**Siguiente acción concreta:** QA local aislado 7d747f7b3b9d68208eb8730fd52993b62168b3ff, #46099501926 verde (175 pruebas Windows, ZIP 15245021290 verificado), nuevo --claim-reuse reutiliza extracción reconciliada del ZIP original 0.8.19 con validación literal/metadatos, sin reextracción/audio, 16 intentos máximos, progreso por ventana, métricas de fallos. Paquete fuente verificado SHA interior c37f405b4af1dfae1f76d7774ddd6aad30dc460e4b41b1d73baf0179f7035a49; inspección real del ZIP original 273 filas/39 registros congelados/8 ventanas, 0 llamadas, hash original intacto. Siguiente: entregar herramienta separada; prueba local opcional con consentimiento explícito, enviar resultados privados para evaluar; no inferencia nueva hasta autorización. Consentimiento explícito local para live, sin forzar CPU ni cambiar modelo. No confundir completed con salida temática ni aceptación semántica. Full CPU #46097495438 falló ambos timeouts; reparación determinista e278a57b #46099113043 verde (77 tests, ZIP 15245035393, 18 gaps, plazo/restauración/diagnóstico correctos, cero temas por timeouts simulados). No repetir CPU ni audio, no exigir prueba hasta paquete verificado. 0.8.19 ASUS/default/main/GPU/Whisper/Qwen/gate intactos, no versión/installer/publicación. Leer checkpoint/ledger/plan/aceptación. Commit documental [skip ci].

## Reanudación verificada — 2026-11-28

PR #7 sigue abierto, draft, sin merge; HEAD comprobado antes de este checkpoint documental `3e4c51e39b02db366af91d72e412d1c5b10604e6`, main `de0f22a43a5a1f857ec5d47ded802037b2f34984`. Jobs de Actions #46078498354 (Windows y auditoría), #46099113043 y #46099501926 consultados de nuevo: todos completed/success, sin relanzarlos. El artefacto [15245021290](https://github.com/kl4ne/meetingsplit/actions/runs/46099501926/artifacts/15245021290) sigue disponible y corresponde al commit QA `7d747f7b3b9d68208eb8730fd52993b62168b3ff`. Guía exacta: [PRIVATE_CLAIM_QA.md](https://github.com/kl4ne/meetingsplit/blob/7d747f7b3b9d68208eb8730fd52993b62168b3ff/docs/PRIVATE_CLAIM_QA.md). Herramienta ya presentada al propietario en la conversación anterior; no hay resultado nuevo de --claim-reuse en ASUS verificado. Siguiente acción: recibir resultado privado de esa única comparación opcional si el propietario consiente explícitamente; si no la ejecuta, mantener el bloqueo editorial y no repetir CPU, audio ni extracción. No se inicia inferencia ni se altera el código en esta reanudación. No subir materiales privados ni su hash a GitHub. Sin promoción, nueva compilación, merge, publicación o cambio de versión. Los conteos CI y verificación de paquetes históricos permanecen en el ledger; no constituyen aceptación semántica.
