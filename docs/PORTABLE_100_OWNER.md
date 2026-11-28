# MeetingSplit 1.0.0 — portable para uso del propietario

Fecha: 2026-11-28. El propietario solicitó un ejecutable versión 1.0. La numeración técnica es 1.0.0. Se conserva íntegro el motor del portable 0.8.19, fuente validada 448a8502521192034e939145d43cc6b18b90898e; cierre documental 0ae748ad5673b69910027866c9f400c1b7d93b0e. Cambios de versión, recursos Windows, metadatos, pruebas de consistencia y documentación solamente. Ollama sigue opcional y desmarcado por defecto; las minutas no tienen aceptación editorial. No reiniciar la investigación. Consultar [cierre técnico](MINUTES_FUTURE_HANDOFF.md).

El alcance es portable Windows x64, MeetingSplit.exe con su carpeta _internal y dependencias, no instalador, no publicación, no merge a main. release_allowed=false y todos los requisitos de liberación permanecen sin aprobar. La numeración 1.0.0 no certifica aceptación de minutas ni autorización de release.

Compilación: usar flujo aislado en GitHub Actions, FFmpeg/PyAV fijados, pruebas de motor, inventario nativo, self-check del EXE y comprobación del ZIP extraído. La entrega debe incluir checksum. No repetir inferencias reales ni pruebas privadas.
