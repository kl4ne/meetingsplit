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
