# Optional components / Componentes opcionales

CPU transcription needs neither component. Both options are unchecked by default.
La transcripción CPU no necesita estos componentes. Ambas opciones empiezan desmarcadas.

NVIDIA: official cuBLAS 12.4.5.8, CUDA runtime/NVRTC 12.4.127 and cuDNN 9.1.1.17 archives. About 1.1 GiB download; several GiB expanded. These are application scoped libraries, not a driver or a full CUDA Toolkit. An existing compatible NVIDIA driver and Microsoft Visual C++ x64 runtime are required. Driver installation/restart is never automatic. Library loading alone is not proof of acceleration. Setup performs an isolated small-model inference test and saves its result locally; real speech and performance still require assessment.

NVIDIA: archivos oficiales de cuBLAS, runtime CUDA/NVRTC y cuDNN. No instala controladores ni cambia el PATH. El informe CUDA distingue la prueba sintética de la aceptación con voz real.

Licenses / Licencias NVIDIA (review before accepting / revisar antes de aceptar):
https://docs.nvidia.com/cuda/eula/index.html
https://docs.nvidia.com/deeplearning/cudnn/backend/v9.1.1/reference/eula.html
Original vendor license and notice files are retained with each extracted archive. Downloading from NVIDIA is not a grant to redistribute arbitrary Toolkit files. MeetingSplit's base installer contains no NVIDIA archives.

Ollama 0.40.6: optional standalone Windows x64 distribution, SHA-256 pinned to the official release asset. About 1.4 GiB download, plus qwen3:4b about 2.5 GB. Existing service on 127.0.0.1:11434 with this exact model is reused. Otherwise a separate, temporary server is started on 127.0.0.1:11435, storing models in the selected internal folder. A busy port fails safely. No service, login task, user environment or existing Ollama installation is changed. Remote/cloud model names are rejected. Original runtime notices are retained.

Ollama: detecta un servicio existente con qwen3:4b. Si falta, descarga el componente independiente y guarda los modelos en la carpeta interna elegida. No modifica otra instalación de Ollama. La descarga necesita Internet; las minutas se generan por loopback. Se prueba con texto ficticio, sin grabaciones personales.

Ollama is MIT licensed: https://github.com/ollama/ollama/blob/v0.40.6/LICENSE
Its included native dependencies carry separate licenses/notices in the archive.
qwen3:4b is Apache-2.0: https://ollama.com/library/qwen3:4b
The exact model license returned by /api/show is saved as QWEN3_LICENSE.txt.
The pinned qwen3:4b currently declares thinking-only operation: reasoning is received
in its separate API field and discarded. Only the final answer is saved. Truncated
generation is rejected. A failed optional minute keeps audio/transcript/subtitles
and adds a visible MINUTA_NO_GENERADA.txt diagnostic to Results. Existing Ollama
weights are reused only if their reported source path is verified internal/unsynced.
Generation tests save a synthetic minutes example and model digest. They do not certify factual accuracy; review all names, dates and agreements.

Free disk space / Espacio: at least 12 GiB for setup, preferably more for Whisper and meeting outputs. C: and D: must be verified internal drives. USB (including fixed USB SSDs), network and cloud folders are rejected. Incomplete downloads can be retried; completed verified components are kept. No component or model is removed when uninstalling the base app, because they are user data in the chosen folder. Delete that folder explicitly only when its contents are no longer needed.

Cancel / Cancelar: downloads check cancellation between bounded reads (20-second stalled network timeout); model pulls show progress. A started model pull may leave reusable partial blobs. CPU remains available after failed/cancelled optional setup.

Release remains on hold until GPU, Ollama, installer, regressions and licenses have all been evaluated. / La publicación sigue bloqueada hasta evaluar GPU, Ollama, instalador, regresiones y licencias.
