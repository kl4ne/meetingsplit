# Optional component — Ollama CPU / Componente opcional — Ollama CPU

**CPU-ONLY POLICY / POLÍTICA SOLO CPU (MeetingSplit 0.8.6 development branch)**

Transcription uses Faster-Whisper **small** on CPU (`device='cpu', compute_type='int8'`) even if the PC has NVIDIA graphics. No CUDA, cuDNN, NVIDIA driver, GPU test or GPU download is necessary or offered. Any earlier installation of CUDA libraries is **left untouched** in its original folder; MeetingSplit does not need or activate them.

La transcripción funciona **siempre en CPU** con Whisper `small`, incluso en computadoras con NVIDIA. Ya no se ofrece la instalación de CUDA. Ninguna carpeta existente de CUDA se borra automáticamente. Si una configuración antigua solicita `medium` o `large-v3`, se procesa con `small` y el `manifest.json` registra el modelo solicitado y el modelo real.

## Local minutes (optional) / Minutas locales (opcional)

Ollama 0.40.6 and qwen3:4b remain optional, with explicit download/license consent. All `/api/chat` requests set `options.num_gpu=0`, including when connecting to an existing local Ollama service. The MeetingSplit-managed Ollama process additionally sets `OLLAMA_LLM_LIBRARY=cpu` and hides NVIDIA/AMD adapters from the subprocess through `CUDA_VISIBLE_DEVICES=-1`, `HIP_VISIBLE_DEVICES=-1`, and `ROCR_VISIBLE_DEVICES=-1`. These settings apply only inside MeetingSplit's own process and requests; they do not alter the user's system or an independently running Ollama server.

Ollama puede generar minutas sin NVIDIA; consume RAM y podría tardar más. En cada solicitud MeetingSplit exige `num_gpu=0` y su servidor propio usa la biblioteca de CPU. La transcripción de audio no requiere Ollama.

Ollama runtime archive ~1.4 GiB; qwen3:4b model roughly 2.5 GiB. Only the user-requested optional Ollama/model downloads may access the Internet. Audio, transcripts and summaries remain local and use loopback; vendor/cloud aliases are rejected. If Ollama fails, the audio and transcript remain and the result contains `MINUTA_NO_GENERADA.txt`.

Ollama MIT license: https://github.com/ollama/ollama/blob/v0.40.6/LICENSE
qwen3:4b model Apache-2.0: https://ollama.com/library/qwen3:4b
The model license returned by `/api/show` is saved to `Componentes/QWEN3_LICENSE.txt`. Upstream vendor notices may carry additional third-party obligations.

The optional setup dialog requires user-selected internal C:/D: data folder and explicit license acceptance. USB, network and cloud-synced roots are rejected. No automatic administrator elevation, driver changes or system PATH edits. A failed attempt saves `Componentes/component-setup-report.json`; previously verified optional components and data are retained. At least 12 GiB free is required by setup while further room is recommended for CPU model caches/meeting outputs.

**CPU performance:** the first model download may take time; transcription of a multi-hour meeting can be substantially slower without GPU acceleration. Users may choose shorter recordings or run in segments. Do not promise real-time inference, equal GPU performance or unchanged accuracy. Test actual EN/ES natural speech before release.

**Release status:** 0.8.6 source-only changes on `qa/release-evidence-20261021`; a new Windows binary has NOT yet been validated and is NOT released. Qt/Chromium and native LGPL/NVIDIA binary notice obligations still require review, even if NVIDIA execution is disabled. The public release gate remains blocked.
