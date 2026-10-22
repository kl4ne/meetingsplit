## ACTIVE CPU-ONLY CHECKPOINT — user overrode every earlier GPU requirement (2026-10-22)

- **Owner's final hardware decision:** `olvida esto de usar la nvidia. usemos siempre el cpu`. Do NOT continue CUDA setup, NVIDIA RTX 4060 spouse laptop or RTX 4070 ASUS GPU acceptance. Second PC is not needed for this issue.
- **CPU-only source implementation** now on isolated branch: `engine/transcription.py` never initializes GPU and uses `WhisperModel(...device='cpu',compute_type='int8')`; CPU-small effective for any old medium/large-v3 selection; `engine/job.py` enforces exact CPU device, writes `execution_policy='CPU_ONLY'`, `actual_model`, and truthful CPU progress. `engine/ollama.py` sends `options.num_gpu=0` on EVERY chat request, incl. existing local service; managed process CPU library `OLLAMA_LLM_LIBRARY=cpu` and GPU masked in own environment.
- Native GUI UI/in-app setup/installer now ONLY offer optional Ollama CPU; CUDA opt-in removed, direct legacy `install_gpu()` raises, old GPU library activation no-op, CLI `--cuda-probe` disabled. UI standalone preview rebuilt exactly; no visual font changes. Existing downloaded user files and applications untouched. CTranslate2's upstream DLL bytes may remain inside package until separately audited; they are never initialized by app.
- `qa/release_gate.json` replaced obsolete ASUS GPU tasks with **uncompleted** CPU-only speech, CPU-only Ollama, long-meeting, final frozen acceptance, installer and legal requirements, `release_allowed=false`. v0.8.6 and draft PR #1 retained; main and Integrity unchanged.
- **Lightweight Ubuntu Actions #39723186879 SUCCESS (17 passed / 5 skipped)** with code compile, JS syntax and blocked gate. This job intentionally did NOT install or freeze any Windows binaries.
- **ONE necessary internal Windows frozen QA #39723395202** started at commit `1351b8e53f0498136bd74fa0c13a06e367dd1fe4`, currently completing pinned LGPL FFmpeg+PyAV source build; MUST wait for final conclusion to assert successful EXE/setup. Workflow includes Qt/PyInstaller, scoped Windows actual smoke and checks `frozen-check.json` `checks.cpu_only.ok=true`, `checks.cuda.ok=false`, and packaged HTML without CUDA button. NO PUBLIC RELEASE authorization.
- Work documented `docs/CPU_ONLY_OWNER_DECISION_2026-10-22.md`; PR #1 description superseded older GPU goals.
- Next: inspect final Windows QA run #39723395202 result/logs; only if passed save exact artifact IDs/digests and offer INTERNAL evaluation version (not signed public release); don't retry builds for no reason. If failed, fix precise root cause and rerun only justified scope. CPU 1–3h accuracy/performance, vendor licensing and interactive installer cancellation still pending.
- No further requests for spouse's laptop. Do not claim changes are installed on ASUS; source-only until Windows binary is built and owner installs chosen candidate later.

---
## LATEST LIVE SECOND-PC PROCESSING OBSERVATION — 2026-10-22

- User's short real meeting on secondary Windows 11 with RTX 4060 Laptop had not finished; user BELIEVED it was using CPU. Investigation of **actual original packaged source** showed unconditional `En CPU el primer fragmento puede tardar varios minutos` progress message, even for `NVIDIA GPU`; **there is NO verified CPU fallback yet**. Check live `manifest.json` key `device` in that meeting's output folder (written during processing, safe to read); no need to upload personal audio or raw manifest.
- Setup previously passed GPU `small` inference and Ollama local qwen3:4b; real selected `medium`/`large-v3` gets separately GPU-probed, may truly fall back; manifest `device=CPU` and `warnings` distinguish from merely misleading text.
- QA-only isolated source fixes: `engine/job.py` truthfully shows GPU vs CPU in transcribe progress; persists initial model/probe CUDA fallback `gpu_fallback.stage=model_initialization_or_probe`, also lazy inference CUDA fallback `stage=live_transcription`; backward-compatible `on_fallback` optional callback in `engine/transcription.py`; `ui/app.js` translates the new bilingual progress; new synthetic-only tests `tests/test_gpu_progress_truth.py`. **No Windows QA executed or packaged yet**; `[skip ci]` and no new Actions minutes, current user-running app unchanged.
- Diagnostic root detail and step instructions: `docs/SECOND_PC_GPU_STATUS_AMBIGUITY_2026-10-22.md`. Do not claim fix shipped. Continue after device manifest result or final processing outcome. Do not repeat large CUDA/Ollama downloads or restart actively progressing meeting.
- Keep v0.8.6, release_allowed=false, QA draft PR #1, main/Integrity unchanged.

---
## LATEST PHYSICAL SECOND-PC DIAGNOSTIC (2026-10-22)

- User uploaded `MeetingSplit-Diagnostico-Compartible.json` from SECOND Windows 11 PC after describing an error/repeated Prepare button. Actual GPU listed: **NVIDIA RTX 4060 Laptop GPU** plus Intel UHD (not ASUS 4070).
- CUDA four packages and Ollama 0.40.6 each have present folders and **schema-2** receipts. **Receipt presence is not a freshly rehashed manifest.**
- **CUDA validation `ok=true`, `device=cuda`** (synthetic silence inference only).
- **Ollama validation `ok=true`, `status=complete`, `model=qwen3:4b`**. Both dedicated reports are present.
- The original transient GUI error's specific text/stage remains unobserved. Original shipped GUI lacks a generic report, hence `last_gui_attempt=null` and `setup_report_exists=false` are explained by the OLD candidate. New report persistence code is only on QA branch and has not been rebuilt/tested; it did not produce the user's result.
- **No further download/reinstall is warranted now**. Next physical action: short end-to-end dummy English/Spanish speech GUI meeting and generated local minutes check, ideally without uploading any personal recordings. This requires user at PC. Real 1–3h and target ASUS 4070, full legal and UI GUI cancel remain blocked.
- Complete evidence in `docs/SECONDARY_PC_CUDA_OLLAMA_DIAGNOSTIC_SUCCESS_2026-10-22.md`. No Actions minutes spent; no main merge; 0.8.6 release gate remains FALSE.

---
## NEW USER-OBSERVED PHYSICAL TEST FAILURE — 2026-10-21

- User on SECOND physical Windows 11 machine reported optional component failure after selecting CUDA+Ollama, repeatedly showing “Prepare selected components” upon retry, and no expected QA report. **Exact error, GPU and which install stage failed UNKNOWN; do not guess or mark either vendor runtime working.**
- Diagnosed source: original frozen 0.8.6 Qt `desktop/component_setup.py` only displayed failure in a QLabel, then re-enabled Prepare; no general persistent result. CUDA GPU inference runs BEFORE Ollama setup, so CUDA failure can prevent Ollama's report from existing. Dedicated physical installer QA `qa-summary-shareable.json` is ONLY produced by `02-PRUEBAS-GUIADAS.cmd`, not by the GUI's Prepare button.
- Created user-downloadable read-only diagnostic `MeetingSplit-Diagnostico-Opcionales-Win11.zip` SHA256 `ff4047ecef106ccdb033673b74d929ab84b412ec3c2c8ae33c507e097374115f`, showing GPU model, presence of vendor receipts, `cuda-validation.json`, `ollama-validation.json` status and redacted error (if any). User must choose their existing MeetingSplit DATA folder and return ONLY `MeetingSplit-Diagnostico-Compartible.json`. The ZIP is a conversation artifact, not checked into GitHub.
- Patched ONLY isolated QA branch `desktop/component_setup.py`: durable atomic `Componentes/component-setup-report.json` stage/result (including failure/cancel), human-readable message and Qt Open Report button. Added `tests/test_component_setup_reports.py`. **New source NOT built nor Windows-tested**; it is NOT on the second PC's current installer. DO NOT claim issue fully fixed until user diagnostic, targeted tests and package validation.
- Existing official QT license notice source/earlier 685/685 sha and native 211 still good for OLD candidate; no further GitHub Actions minutes used.
- Detailed checkpoint `docs/SECONDARY_PC_OPTIONAL_SETUP_FAILURE_2026-10-21.md`. Await diagnostic rather than repeat installation/downloads. Preserve data, receipts and test machine; no deletion, no driver/system/path changes. Release `0.8.6`, `release_allowed=false`, main/Integrity unchanged.

---
## ACTIVE CHECKPOINT — SECOND PHYSICAL WINDOWS 11 QA KIT READY (2026-10-21)

- User CONFIRMED access to a second physical Windows 11 computer. No remote access to it is available and **no test has actually run on that machine yet**. Do not claim physical installer results or ASUS acceptance.
- Prepared a **small 8,334-byte** chat-downloadable secondary-PC test kit `MeetingSplit-Windows11-Segunda-PC-QA-Kit.zip` SHA256 `41f5b1b041e78d66f2fe5a0244a96148ed74eb11c929c07852ace4d404dd57d4`; kit ZIP CRC verified. Kit includes `01-COMPROBAR-PC.cmd`, `02-PRUEBAS-GUIADAS.cmd`, readme, and `MeetingSplit-Physical-QA.ps1` SHA256 `af2a69df7cf24a26086f90096d1c27ff196457dc0710ef6c7297b01e6534290a`. **Kit bytes exist in current conversation artifact, NOT in GitHub**. Preserve the exact link as a conversation attachment, or have user reattach if a later chat loses it; never invent it.
- The script verifies the **existing** official internal QA installer artifact #12391430920, SHA-256 ZIP `9217849517b9b47ecaaa9b4d6fdf892593ba007f0b28c05fd73ab38e8065986b`, from successful Windows QA run #39695270843 / old frozen commit `90238d6`. No additional GitHub Actions minutes, package rebuild or source merge.
- Non-admin read-only **Preflight** checks Windows 11 x64, internal fixed LOCALAPPDATA disk and at least 16GiB free, existing MeetingSplit uninstall registry keys/known paths; prints GPU name read-only. **Guided** opt-in test checks Inno pre-copy wizard cancellation via verified exit code 2, no installed app; then isolated real GUI install, frozen app self-check, manual five screens EN/ES with synthetic-only data, real GUI uninstall and external data survival. Manual confirmation and test account required. No CUDA/Ollama network download or Windows driver modifications.
- Official Inno exit code 2 is pre-copy cancellation, 5 is mid-copy cancellation. This script does **not** test mid-copy cancellation or GPU/Ollama live downloads; those remain separate later acceptance steps. User must execute on the second PC and return `qa-summary-shareable.json` only; installer logs could contain names/local paths. Full handoff/guardrails in `docs/SECONDARY_PHYSICAL_WIN11_QA_HANDOFF_2026-10-21.md`.
- Prior independent 685/685 frozen file hashes and 211 PE headers PASSED; CTranslate2 wheel/DLL origin matched; full native legal compliance, certificate signing, and ASUS natural-language GPU/Ollama validation still OPEN.
- Release remains **0.8.6 / release_allowed=false**; branch QA only, PR #1 draft, main and Integrity unchanged.

---
## VERIFIED MASTER CHECKPOINT — 2026-10-21, independent portable and PE audits

- One independent, **non-GitHub-Actions** extraction and stream SHA-256 audit of complete official internal QA portable artifact **#12390996760** was completed using the prior run #39695270843 inventory. GitHub artifact ZIP SHA-256 `b0c2c678e311c19dcd0a9565474bf417e62a4b71cdbf00a83e8758037bfb0b3b` MATCHED. All **685/685 actual frozen files** (total **1,159,013,662 uncompressed bytes**, **211 native binaries**) matched the independent source inventory hashes exactly, no unexpected, missing, duplicate or changed files. Evidence: `docs/INDEPENDENT_FROZEN_PORTABLE_HASH_AUDIT_2026-10-21.json`. Windows ZIP directory placeholders were properly excluded from file count.
- Offline native PE header audit also checked **all 211/211 binary headers: all AMD64 PE32+, zero malformed**. **103** have a PE certificate table; **108** do not. The **unsigned development `MeetingSplit.exe`** has no certificate table. QtWebEngineCore.dll, QtWebEngineProcess.exe and bundled cuDNN DLL have certificate tables, but this does **NOT** establish the embedded signatures are valid or trusted. Evidence: `docs/INDEPENDENT_FROZEN_PE_SECURITY_METADATA_2026-10-21.json`. Code signing of the final app/installer is OPEN.
- Wheel-DLL provenance independently verified via **one cheap Ubuntu Actions #39698897754**: official CPython 3.11 Windows ctranslate2 4.6.2 wheel digest `ce7880fa5d2e1b36329998c711cb764c621a4d2a199b251b1ad02e770b641e91` matched, bundled `cudnn64_9.dll` original wheel SHA `c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05` matched exact frozen bytes, 14 source tests PASSED. No other Actions rebuild is justified now.
- Added original Chromium 140 BSD license with SHA-256 `368cca1106be99d39ecd32a38d8305585d802a475effb66380b91ffc9bcf709b` in the **source QA branch**, included in the now **eight** required source-notice receipts. This is post-compiled and NOT in the older binary. Full Chromium/Qt and FFmpeg source/notice legal clearance remains open. Upstream Qt WebEngine 6.140 source's CHROMIUM_VERSION describes base Chromium 140.0.7339.264 patched through 155.0.8059.85; exact frozen vulnerability review remains open.
- `ui/app.js` now lets the user see the real `MINUTA_NO_GENERADA.txt` local-Ollama diagnostic that was already created and allowed in the Python bridge. Current bundled QA EXE **predates this fix**; no misleading claim that it has shipped.
- Acceptance plan `docs/FINAL_RELEASE_ACCEPTANCE_PLAN_2026-10-21.md`; signing `docs/WINDOWS_SIGNING_SMARTSCREEN_DECISION_2026-10-21.md`. Critical external blockers remain **GUI-capable disposable Windows interactive installer + real vendor download QA, ASUS RTX 4070 final exact-binary natural speech/GPU/Ollama testing, full native CVE/legal notices and legal sign-off, publisher choice and signing**. Do not rebuild full Windows app until these and notices are batched.
- Draft PR #1 open; branch `qa/release-evidence-20261021`; `main` must remain unchanged; MeetingSplit v0.8.6, `release_allowed=false`; Integrity repo untouched.

---
## ACTIVE VERIFIED CHECKPOINT — 2026-10-21 — vendor provenance and readiness (NO further packaging)

- No repeated Windows/PyAV build. Existing successful 0.8.6 frozen QA #39695270843 still definitive for snapshot `90238d6` (102 passed, 2 skipped). Current QA source branch has *later* legal/JS source changes not yet included in its binary.
- **One low-cost Ubuntu job #39698897754 PASSED: 14 source tests** and downloaded the exact official PyPI CTranslate2 4.6.2 CPython 3.11 Windows wheel, SHA-256 `ce7880fa5d2e1b36329998c711cb764c621a4d2a199b251b1ad02e770b641e91`. Its `ctranslate2/cudnn64_9.dll` (438,840 bytes) SHA-256 `c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05` EXACTLY matches the frozen native-inventory DLL. Evidence `docs/CT2_CUDNN_ORIGIN_VERIFIED_2026-10-21.json`; archived Actions artifact #12391304966, ZIP SHA256 `0c95d2b23462a89cffbeb368ed3427613c46b1c6b91443175ee37fc24ac3886f`. Origin is VERIFIED; governing NVIDIA DLL version/EULA compliance and actual redistribution signoff remain OPEN.
- NVIDIA cuDNN 9.1.1's official SDK EULA cuDNN supplement expressly allows runtime `.dll`/`.so` redistribution *under the agreement and its conditions*; no blanket distribution approval. Official source: https://docs.nvidia.com/deeplearning/cudnn/backend/v9.1.1/reference/eula.html
- Qt WebEngine `6.140.0` source `CHROMIUM_VERSION` (Git blob `af94dd121710fc8df04db6182bc27a1faf7d83e6`) states base Chromium 140.0.7339.264, patches through 155.0.8059.85. Corresponding PySide6 WebEngine wheel `6.12.0.140`. Actual frozen Chromium binary matching and complete third-party notice texts / source fulfillment still OPEN.
- New exact original Chromium 140 BSD notice `docs/third-party-licenses/Chromium-140.0.7339.264-BSD-3-Clause.txt` SHA-256 `368cca1106be99d39ecd32a38d8305585d802a475effb66380b91ffc9bcf709b` from GitHub upstream tag was added and recorded in `sources.json`; manifest now requires **eight** upstream notice hashes. This file was added AFTER the 14-test job and AFTER the last frozen package; no claim it is inside earlier artifact, and no claim it completes Chromium's extensive other notices.
- `qa/vendor_legal_manifest.py` now enforces source hashes; `qa/collect_licenses.py` writes embedded pinned receipts; `qa/audit_package.py` verifies bytes actually frozen. `ui/app.js` corrected results screen to expose `MINUTA_NO_GENERADA.txt` Ollama failure file previously written and exposed by Python bridge. New source-only code isn't in existing frozen package. No repeated CI merely for these small late-stage source/docs additions.
- Signing decision research and no-cost future execution steps saved in `docs/WINDOWS_SIGNING_SMARTSCREEN_DECISION_2026-10-21.md`; acceptance plan `docs/FINAL_RELEASE_ACCEPTANCE_PLAN_2026-10-21.md`. Microsoft states OV/EV certificates do not instantly avoid SmartScreen; signing requires identity and owner authorization. No signing identity, fee or certificate submitted.
- Remaining true blockers: complete build-specific Qt/Chromium third-party notices / matching source/relinking, FFmpeg/PyAV LGPL source materials, exact NVIDIA SDK license conditions and native vulnerability/qualified legal approval; GUI Windows cancellation and real opt-in vendor interruption on disposable VM; final exact ASUS GPU/Ollama natural speech and 1–3h acceptance; final binary after these changes, publisher decision. Version 0.8.6, release gate false, PR #1 DRAFT and main/Integrity untouched.

---
## LATEST VERIFIED TECHNICAL CHECKPOINT — 2026-10-21 — pinned 0.8.6 rebuild PASSED

- **Internal QA frozen Windows build #39695270843 SUCCEEDED** at source commit `90238d621160e05097e7b72c3a1c26b18b4a31cd`. Exact SHA-pinned LGPL FFmpeg 8.1.3 / source-built PyAV passed. Build tests: **102 PASSED, 2 SKIPPED, 1 pytest warning**. PyInstaller frozen self-check, Qt WebEngine, ffmpeg/ffprobe, Faster-Whisper import/CPU fallback, disposable Windows **silent clean install, same-version reinstall, uninstall and external test-data preservation** passed. This does NOT constitute interactive installation cancellation, GPU/Ollama-on-ASUS, or natural-meeting accuracy acceptance.
- Official workflow reports artifact **#12390712114** SHA-256 `0a2af630e25772402c332f38b771ab151b1aafd5eaba98b199913cf67db52376`. Verified downloaded report archive and all its internal counts, pinned source receipts, exact FFmpeg build log hash and **118 matched included legal-file SHA-256 entries**. Frozen inventory **685 files / 211 native**, 1,159,013,662 bytes. No x264/x265 named native file; no `--enable-gpl` / `--enable-nonfree` found. The frozen native EXE/DLL binary bytes themselves were not in this report ZIP, so independent executable rehash is not claimed.
- Internal-only installer artifact **#12391430920** (GitHub ZIP digest `9217849517b9b47ecaaa9b4d6fdf892593ba007f0b28c05fd73ab38e8065986b`). Internal portable artifact **#12390996760** (GitHub ZIP digest `b0c2c678e311c19dcd0a9565474bf417e62a4b71cdbf00a83e8758037bfb0b3b`). These are NOT user releases and MUST NOT be presented as definitive installers.
- Original vendor license notices for tokenizers 0.23.3, Cython 3.3.0 and historical Pyrex are added with SHA-256 receipts; source-only Windows notices run **#39696118269 PASSED**. Those additional docs were committed AFTER QA snapshot `90238d6`, so the new QA binary does not yet contain them. Do NOT mark notice coverage complete.
- Earlier authentic v0.8.5 -> 0.8.6 upgrade #39598790616 PASSED for prior pinned QA installer; the new component-integrity build tested same-version reinstall, not that old->new upgrade again. Interactive installer cancellation #39694379638 remains **inconclusive due hosted runner inaccessible GUI**.
- **Still pending:** Chromium/Qt/FFmpeg complete matching source and notices, cuDNN bundled NVIDIA permission, native vulnerability/security/legal sign-off, optional CUDA/Ollama real interrupted downloads and interactive UI cancellation in disposable GUI Windows, final ASUS 0.8.6 combined GPU/minutes + natural EN/ES/mixed and sustained 1–3h acceptance, release-signing decision.
- No more QA rebuilding merely to repeat success; revisit binary packaging after remaining source/notice or runtime material changes. Version **0.8.6**, `qa/release_gate.json` `release_allowed=false`, draft PR #1 unmerged, `main` unchanged, Integrity untouched.

---
## CHECKPOINT — live Actions handoff after additional native notice work (2026-10-21)

- QA branch `qa/release-evidence-20261021`, draft PR #1. Do not merge or publish.
- **Source-only Windows notice verification #39696118269 PASSED (1 test)**: exact original Tokenizers 0.23.3 Apache-2.0, Cython 3.3.0 Apache-2.0 and Cython/Pyrex COPYING texts are committed and SHA-256-pinned alongside earlier upstream notices. Git source refs are recorded. These newer docs were committed **after** build #39695270843 started and are not part of its frozen snapshot.
- **One justified consolidated full QA rebuild #39695270843** is actively running from snapshot `90238d621160e05097e7b72c3a1c26b18b4a31cd`. Pinned LGPL media preparation and source PyAV compilation PASSED; frozen PyInstaller/installer phase is running at the last check. Retrieve **actual conclusion, logs, artifacts** before claiming this run completed. It is a development-only QA build, not a public Release.
- Windows focused source test run #39694809814 already PASSED (26). An authentic interactive Inno cancellation attempt #39694379638 was inconclusive because GitHub's runner had no visible desktop; do not repeat on the same headless runner.
- Version 0.8.6, `release_allowed=false`, Integrity untouched. Remaining legal/ASUS/interactive release blockers unchanged.

---
## ACTIVE CHECKPOINT — 2026-10-21 — optional components and Windows QA verified

- Last known original main HEAD: `c292ad5d375ed63b581823b1754ab1064ef67cd8`. Continue on `qa/release-evidence-20261021`, not the divergent historical consolidated QA branch. No main changes or releases in this continuation.
- New Windows isolated QA run **#39694809814 PASSED: 26 tests** (new UI/installer-optional fault matrix, in-memory interrupted/retry download, actual Qt QThread cancellation/retry, extracted-component file manifest tamper rejection, inherited native report integrity and Ollama failure receipt regressions). No NVIDIA/Ollama real downloads or installer packaging in this run. Read-only fail-closed release-gate invocation printed expected missing categories.
- Replaced the unsafe reuse assumption for *newly installed optional vendor component folders*: `desktop/components.py` now records hashes/sizes of extracted files in version-2 receipts and verifies them on reinstall/reuse, including refusal of extra executable/DLL files or modified bytes. Prior receipts are honored with an explicit legacy-unverified warning rather than silently removing/invalidating previous user installations. This is QA code, not an ASUS GPU integration validation. Tests are in `tests/test_component_integrity_receipts.py`.
- Earlier affected regression run #39694427670 PASSED: 21 tests. One previous run #39694132723 had **all 21 tests pass** but failed its own workflow step because PowerShell treated the expected release-blocking exit code 2 as a job failure; this was fixed by asserting the exit code inside Python. Do not repeat or call this an app defect.
- Authentic **interactive Inno Setup** cancellation was attempted using the already validated pinned QA installer artifact #12346625631, whose GitHub ZIP digest was verified; Actions #39694379638 downloaded correctly but could not discover a visible wizard window in the hosted Windows runner, so **interactive cancellation remains INCONCLUSIVE** (not a confirmed success or installer defect). Do not rerun on this same headless runner; use a GUI-capable disposable Windows interactive session, never overwrite user's current ASUS install.
- Existing QA run #39599798144 passed the pinned LGPL 0.8.6 full installer/MP3/M4A/WAV stack (82 passed, 2 skipped). Isolated authentic 0.8.5 -> 0.8.6 upgrade #39598790616 passed. Main tests-only #39602465892 passed (84 passed, 2 skipped).
- New `docs/REDISTRIBUTION_EVIDENCE_MATRIX_2026-10-21.md` correlates exact packaged SHA-256 files with separate Qt 6.12 / WebEngine/Chromium, FFmpeg/PyAV, CTranslate2 bundled cuDNN, NVIDIA, Ollama and Qwen corresponding-source/licensing obligations. The source archive and model/license questions are **not cleared** by documentation alone. Need native binary provenance and legal review.
- Remain **0.8.6**, `release_allowed=false`. Interactive installer & live optional-network tests, ASUS exact-package GPU/minutes/natural meeting acceptance, native security and third-party legal clearance are still OPEN. Do not touch Integrity.

---
## CURRENT VERIFIED CHECKPOINT — 2026-10-21 — post-timeout recovery / evidence-only QA

- Starting point: latest `main` was `c292ad5d375ed63b581823b1754ab1064ef67cd8`; original QA `qa/consolidated-20261021` was `e545348d2ad0d0e689876637d77f83072f3a73bc`. They diverged (QA +13 / behind main 6), so this isolated `qa/release-evidence-20261021` branch was created from latest main; neither old branch nor main was force-updated.
- Previously pending GPL-free SHA run #39598629560 **FAILED SAFELY** because commit `7183257` fetched FFmpeg `releases/download/latest/ffmpeg-n9.0-latest...` while comparing its bytes to the pinned **8.1.3** SHA. The later dated 8.1.3 asset URL fixed this mismatch without disabling SHA-256 checking. Subsequently run #39599256740 failed a NumPy peak-value test; commit `e545348` fixed it. Both historical failures have passing successors.
- Exact pinned LGPL Windows QA run **#39599798144 SUCCESS** (82 passed, 2 skipped), including actual MP3/M4A/WAV encode+PyAV decode, frozen WebEngine/self-check, disposable clean/reinstall/uninstall. Authentic isolated **0.8.5 -> 0.8.6 upgrade #39598790616 SUCCESS** with external test data retained. Main tests-only run **#39602465892 SUCCESS** (84 passed, 2 skipped).
- Independent review of the existing QA reports archive (SHA-256 `428a5540b90ef049ccd0eb24b51cd082bc4507a457a94feb43fbb53288df1db3`) verified the internal inventory totals **680 files / 211 native**; embedded legal-file SHA-256 entries; FFmpeg -version log; FFmpeg dated archive SHA `453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a`; PyAV upstream source SHA `dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf`. Six isolated evidence-manipulation tests passed locally. No duplicate public QA builds were triggered.
- This reports ZIP does **not** contain frozen EXE/DLL bytes, so those per-file hashes are inventoried claims from the Windows builder, not independently rehashed here. It does NOT certify malware-free binaries or redistribution compliance.
- Confirmed release blockers from the actual inventory: `Qt6WebEngineCore.dll` present but no Chromium-named third-party notice file; bundled `_internal/ctranslate2/cudnn64_9.dll` SHA `c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05` needs specific NVIDIA provenance/license examination. Corresponding-source/LGPL replacement instructions and full native audit also remain open.
- Added `qa/verify_release_evidence.py`, `tests/test_release_evidence.py`, and `docs/QA_NATIVE_EVIDENCE_AUDIT_2026-10-21.json` to this QA branch. Report validation passing is **not** app acceptance. The new files have local focused tests; they have not undergone a new Windows CI run.
- Remaining: interactive Windows installer cancellation, optional CUDA/Ollama interruption/retry/full-disk acceptance, exact consolidated ASUS GPU/Ollama/natural speech end-to-end, and legal/security sign-off.
- **Version remains 0.8.6, `qa/release_gate.json` release_allowed=false, no public Release/user delivery, no modifications to Integrity Business Filings.**

---
## Continuity checkpoint — timeout recovery / main integration 2026-10-21

- **Main HEAD:** `c3af16d` before this documentation-only checkpoint.
- Isolated pinned LGPL stack successfully merged to `main`, without a
  public Release or installer for users. This includes source-built
  PyAV 16.0.1, BtbN FFmpeg 8.1.3 LGPL/shared (pinned SHA-256),
  manual-QA-only workflow, audio exports, legal receipts, and
  fail-closed native codec checks.
- Windows tests-only CI **#39602465892 PASSED: 84 passed, 2 skipped**.
  This run skipped executable packaging and installer uploads as intended.
- Latest full pinned Windows package QA #39599798144 PASS:
  82 tests passed, 2 skipped, frozen app, MP3/M4A/WAV,
  installation/reinstall/uninstall; no known GPL codec DLLs.
- Authentic 0.8.5 to 0.8.6 isolated upgrade #39598790616 PASS.
- Pinned QA evidence archive saved to Library:
  `/Proyectos/MeetingSplit/MeetingSplit-pinned-LGPL-QA-reports-2026-10-21.zip`.
- Exact frozen Windows package contains Qt WebEngine/Chromium and a
  bundled CTranslate2 `cudnn64_9.dll`. Their redistribution provenance
  and the complete third-party source/notices must be reviewed. These
  material findings are documented in `docs/THIRD_PARTY_REVIEW.md`.
- Remaining blocker flags in `qa/release_gate.json`: complete
  interactive install/cancel/optional component acceptance and
  third-party license/security review. Final pinned package on the ASUS
  with GPU + Ollama still requires confirmation.
- VERSION REMAINS 0.8.6; `release_allowed=false`. Do not offer a
  definitive installer or public release. Integrity untouched.

## 2026-10-21 — pinned LGPL media integrated into main (DEVELOPMENT, NO RELEASE)

- Verified packaged code from isolated branch `qa/consolidated-20261021`
  Windows Actions #39599798144: **82 passed, 2 skipped**; PyInstaller,
  installer/portable, frozen self-check, Qt WebEngine, MP3/M4A/WAV
  export-and-PyAV decode, silent install/reinstall/uninstall all passed.
- Pinned FFmpeg 8.1.3 LGPL shared asset SHA-256:
  `453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a`.
  PyAV 16.0.1 is built from pinned official source and repaired against
  that exact FFmpeg runtime. Native QA inventory: **680 files / 211 native**,
  no libx264/libx265 detected and no --enable-gpl or --enable-nonfree.
- Authentic **0.8.5 -> 0.8.6 upgrade** passed on throwaway Windows
  Actions #39598790616 (install old 22 s, upgrade new 22 s,
  uninstall 2 s, external data preserved).
- Main workflow retains **manual-only** installer packaging; new
  LGPL media preparation is conditional on manual QA packaging.
  Temporary QA branch workflows have NOT been merged into main.
- Work remaining before distribution: native LGPL/Qt/Chromium legal
  compliance evidence, interactive cancel/retry and optional component
  acceptance, ASUS check of exact consolidated build, signing decisions.
- **release_allowed=false**, version remains 0.8.6. No new user
  installer or GitHub Release produced by this code integration.

## Verified LGPL-native QA checkpoint — 2026-10-21

- The GPL-enabled old media stack was replaced **on QA branch only** by
  source-built PyAV and LGPL-shared FFmpeg 8.1, Windows QA **PASSED**.
- Frozen Windows native inventory: 679 total files / 211 native files;
  no x264/x265 or FFmpeg GPL/nonfree flags. See
  `docs/QA_LGPL_2026-10-21.md`, run #39595255314 and artifact #12343733718.
- Vendor digest now pinned to immutable dated release for a *future QA run*;
  that exact archive is not yet tested in a consolidated installer.
- Authentic previous-version upgrade run #39596746344 still executing.
- **Main executable dependencies are not switched yet**; no user Release,
  no version bump and `release_allowed=false`.

## LGPL-native rebuild checkpoint — 2026-10-21 — RELEASE STILL BLOCKED

- Isolated branch: `qa/consolidated-20261021`. Do not merge untested
  binary/dependency changes or publish a new user installer.
- QA Windows run #39594879663 **FAILED SAFELY**: PyAV 16.0.1 compiled
  against BtbN n9.0 LGPL FFmpeg headers failed on removed
  `AVCodec.supported_*`/pixel-format fields. No package was published.
- Next QA Windows run #39595255314 successfully completed the
  **LGPL FFmpeg 8.1 / source-built PyAV 16.0.1 preparation** and proceeded
  to PyInstaller. Its packaged self-check and artifact review are still
  PENDING until the workflow completes.
- Experimental code under `qa/consolidated-20261021`:
  `scripts/prepare_lgpl_media.ps1`,
  `qa/validate_lgpl_media.py`, `tests/test_validate_lgpl_media.py`,
  `docs/QA_LGPL_PLAN.md`, and stricter package audit.
  Local negative-gate tests: 5/5 passed.
- The GPL-enabled Gyan/Chocolatey FFmpeg and official PyAV wheel are NOT
  replaced in `main` yet. An authentic v0.8.5->0.8.6 isolated upgrade
  script is staged as `qa/windows_upgrade_from_v085.ps1` but unexecuted.
- The BtbN `latest` URL is mutable; freeze an exact source and SHA-256
  before promoting the LGPL build. Full third-party license review,
  upgrades/cancellation and ASUS acceptance remain open.
- Version stays 0.8.6; `qa/release_gate.json` remains
  `release_allowed=false`. Integrity Business Filings untouched.

## Consolidated Windows QA execution — 2026-10-21

- Isolated QA run #39592132218 **SUCCESS** (development only):
  https://github.com/kl4ne/meetingsplit/actions/runs/39592132218
- Actual Windows disposable install/reinstall/uninstall and frozen UI checks passed.
- SHA-256 manifest: 670 package files / 205 native binaries / 950,475,677 bytes.
- **New confirmed redistribution blocker:** shipped FFmpeg 9.0.2 has
  `--enable-gpl --enable-version3 --enable-static`; PyAV separately bundles
  native x264/x265 codec DLLs. Resolve corresponding source/build/notice duties
  or replace with compliant packages before distribution.
- Details: `docs/QA_CONSOLIDATED_2026-10-21.md`.
- User's actual v0.8.5 upgrade, interactive cancellation, optional download
  failure matrix and final ASUS acceptance remain untested for this package.
- Main version stays 0.8.6; release_allowed is false. QA artifacts were
  uploaded to Actions, not published as a GitHub Release.

# Pre-installer QA checkpoint — 2026-10-21 — RELEASE HOLD

- Latest code checkpoint: `fba16d8`; the application remains **0.8.6**.
- Tests-only Windows CI #39590281003: **72 passed, 2 skipped**, no installer.
- Tests-only Windows CI #39590849581: **75 passed, 2 skipped**, no installer.
- Added `qa/native_inventory.py` (SHA-256 manifest of actual frozen native files and
  conservative FFmpeg GPL/nonfree flag detection), included in future manual QA package reports.
- Added failure-injection tests for vendor downloads, cancellation, disk exhaustion,
  occupied Ollama port and reuse of an existing service.
- Ollama setup receipts now distinguish `complete`, `cancelled`, `failed`;
  the interrupted state is no longer misleadingly reported as `testing`.
- Native manifest **cannot be populated or legally approved until a consolidated
  Windows QA package exists**. Full Qt/Chromium, FFmpeg/PyAV, CTranslate2, NVIDIA
  and Ollama notices/source compliance, installer matrix and natural-meeting
  accuracy still require validation.
- `qa/release_gate.json` remains false. No production Release or new installer delivered.

## Pre-installer development checkpoint — 2026-10-21

- Added a frozen-package SHA-256 inventory and conservative FFmpeg build-flag review.
- Added offline regression tests for interrupted vendor downloads, timeouts,
  low disk space, an occupied managed Ollama port and existing Ollama reuse.
- `qa/native_inventory.py` passed 5 local synthetic Python tests. Optional
  component fault-injection tests require Windows CI validation.
- Only a future manually authorized **QA build** can collect a report from
  actual frozen Windows binaries; NO new installer or public Release has been created.
- The release gate stays BLOCKED and the application version remains 0.8.6.

# CURRENT checkpoint — 2026-10-21 — RELEASE HOLD

Latest observed updates:
- Local frozen EXE tested on the actual ASUS RTX 4070: CUDA/medium synthetic
  speech passed EN (0.78 s) and ES (0.62 s); Ollama qwen3:4b completed synthetic
  minutes EN (100.31 s) and ES (87.48 s). Both retained Ana/Friday and Luis/Monday.
  These are short synthetic checks, not general accuracy or sustained-speed claims.
  EXE SHA-256: 8c6616ca02b7c54983d3841e650915153d187125dee0500e0754f4479e9e1831.
  Frozen Qt/FFmpeg/Whisper self-check and hidden five-screen WebEngine load passed.
  This tested binary predates the subsequent general prompt/legal-text changes;
  the final consolidated installer still requires acceptance before any delivery.
- Fixed local packaging contamination: unrelated host Poppler ICU was shadowing
  Windows ICU and breaking frozen QtCore. Build PATH is process-scoped. Custom
  Qt hooks exclude unused QML/debugger/virtual-keyboard modules; native package
  audit passed with no blocked unused Qt modules. This does not close native licensing.
- Real generated English minutes used "None" for an unspecified pending section.
  Generalized production instructions now request "Not specified" for absent
  section information and no longer mention example draft tasks. Separate source
  evaluation passed in 128.42 s with Priya/reserve room/Tuesday, Marco/confirm
  capacity/Wednesday and $200; no Ana/Luis/draft tasks appeared, absent sections
  used "No especificado". Minor generated wording still warrants human review.
- Original MIT/LGPL/GPL texts missing from exact installed wheel notices are now
  retained with upstream URLs/hash receipts. License explicitly preserves LGPL
  library modification/replacement and debugging rights. Full corresponding-source,
  Chromium/native notice and security review remains OPEN.
- Local full regression before packaging: 71 passed, zero skips (126.23 s).
  Latest targeted component/storage/build regression: 32 passed (4.32 s).
- Previous development runs 39541919344, 39542617600, 39543320166 and 39543467751
  completed successfully. Disposable CI installer clean/reinstall/uninstall smoke
  passed on the earlier source; it does not test a real 0.8.5 upgrade or cancellation.
- User explicitly requested conserving Actions minutes. No Actions run started
  during this continuation. Installer builds now require manual QA dispatch; commit
  markers no longer trigger packaging. Superseded runs cancel automatically,
  optional Inno tooling only installs for packaging, duplicate tests are removed,
  job timeout reduced to 40 min and frozen startup check bounded to 60 s.
  Save this checkpoint with [skip ci]; do not dispatch another build speculatively.
- One-hour synthetic repeated EN/ES workload completed on ASUS CUDA/medium in
  339.3 seconds: 7 exported clips, 622 transcript segments, subtitles and ZIP.
  This is workload evidence, not natural-meeting accuracy or a three-hour test.
- Actual missing-library CPU recovery passed in a fresh process without application
  CUDA folders: cublasLt64_12.dll absent, CPU transcribed both EN/ES test samples.
- Finished English and Spanish synthetic minutes reviewed: Ana/send/Friday and
  Luis/review/Monday preserved; unknown meeting date not invented, attendance not
  assumed, headings/statuses localized. Spanish succeeded alone in ~96 s after a
  concurrent GPU stress run had caused a bounded timeout. Production unloads Whisper
  before starting Ollama; generated text always still requires human review.
- Optional minutes failure now preserves completed transcript/audio/SRT/ZIP and
  exposes MINUTA_NO_GENERADA.txt in Results; integration regression passed.
- Existing Ollama weights must also have an API-reported source path validated as
  internal and unsynced before reuse. Unknown/USB/cloud paths and remote aliases
  are not reused; a separate managed installation remains available.
- Original NVIDIA license texts and Ollama MIT notice included for review before
  optional download. Exact Qt/FFmpeg source and native licensing/security obligations
  remain open.
- First development build 01343bb: Windows compilation, frozen self-check, Setup
  and portable archive passed (run 39541919344). c415e18 disposable installer
  smoke QA also passed (run 39542617600). No new version or Release.
  Artifact downloads have a 512 MiB connector limit; future portable/setup/reports
  are uploaded separately for internal inspection.

Continue `kl4ne/meetingsplit` main from `434651f`. Keep app version **0.8.6**.
NO Release, new version number, user delivery or installation request until CUDA,
optional Ollama, installer QA, regressions, security and licenses are evaluated.
Commits/development CI are allowed. Do not touch `kl4ne/integrity-business-filings`.
All older next-step/delivery instructions below are historical and superseded.

Implemented in this checkpoint:
- Pinned Faster-Whisper 1.2.1 / CT2 4.6.2 / PyAV 16.0.1, patched setuptools and
  tested Qt/build versions. Testing found real dependency breaks: CT2 4.6.0 needed
  removed pkg_resources; PyAV 19 removed metadata_errors required by Faster-Whisper.
- Optional NVIDIA cuBLAS 12.4.5.8, CUDA runtime/NVRTC 12.4.127 and cuDNN 9.1.1.17:
  official SHA-256/size pinned archives, safe extraction, internal storage validation,
  retained licenses and cancellation. No driver/admin/global PATH/System32 changes.
- Complete split cuDNN preflight and isolated bounded lazy-inference probe; existing
  small/int8 CPU fallback retained. Whisper released before Ollama to free VRAM.
- Unchecked optional component wizard from Inno Setup and Settings; base package
  has no NVIDIA/Ollama archives or model weights.
- SHA-pinned Ollama 0.40.6 standalone; reuse ready existing qwen3:4b on 127.0.0.1:11434,
  otherwise own temporary server on 127.0.0.1:11435 with models in selected internal
  folder. Never pull into an existing server with unknown storage location. No
  system service/startup/global environment changes. Loopback only, no proxies or
  redirects, fixed model, progress/cancellation, bounded reads, cold-load handling,
  license/digest receipt and synthetic minutes test. Reject empty/truncated output.
- Existing five EN/ES pages, enlarged fonts, direct PayPal and plain credit retained.
  Custom/corporate OneDrive roots additionally blocked; USB security retained.
- Explicit fail-closed qa/release_gate.json and license inventory collection.
  Normal pushes test only; installer builds require explicit manual workflow input.
  CI has no Release permission. Use [skip ci] for locally validated checkpoints
  when no new runner evidence is needed.

Observed here on the actual ASUS (source environment; no private meeting audio):
- Hardware: ROG Strix G614JI, RTX 4070 Laptop 8188 MiB, driver 617.42.
- Official NVIDIA archives downloaded/hash verified under ignored work/hardware.
  CUDA inference passed with silence and Windows TTS EN/ES samples (~10 s each),
  small and medium. Final CT2 4.6.2 medium CUDA int8_float16: ~0.72 s EN / ~0.61 s ES
  after preparation. These short warm tests do not establish long-recording or
  frozen-installer acceptance. Medium preserved Ana/Luis and stated $5000 budget;
  small confused some names, reinforcing manual review.
- CPU small/int8 also transcribed both synthetic speech samples. User's previous
  six-clip CPU/~11 min success remains the real-meeting baseline.
- Read-only actual drive checks: internal C:/D: accepted, J: rejected as USB.
- Regression batch: 55 passed, 1 skipped before final added tests; browser/optional
  security batch: 26 passed. Final counts/CI recorded in NEXT_ACTION when available.
- Python dependency audit after CT2/setuptools/pip correction: no known advisories
  from pip-audit. Native licensing/security review remains pending.
- Ollama runtime/model downloaded; endpoint, model and license validated. Initial
  minutes tests exposed cold-load timeout and a model declaring thinking.values=[true].
  Disabling thinking was not supported. The corrected client enables its separate
  thinking channel, discards that field, reserves adequate context/output budget,
  and rejects truncation. A finished English synthetic minute was generated and
  reviewed; explicit locale/task rules corrected mixed-language headings and an
  omitted task. Corrected English output includes both Ana/Friday and Luis/Monday,
  no invented date and no claim of confirmed attendance. Spanish QA also passed;
  see latest updates above.
- Full local regression with final pinned dependencies: 68 passed (no skips),
  including browser EN/ES navigation. Subsequent small fixes require targeted checks.

Remaining: corrected EN/ES minutes assessment, frozen EXE/installer end-to-end GPU
and Ollama, clean/upgrade/cancel/uninstall, long-recording/resource tests, complete
native dependency and GPL/LGPL redistribution evaluation. Keep release gate closed.
See docs/OPTIONAL_COMPONENTS.md and docs/THIRD_PARTY_REVIEW.md.

---
## Historical checkpoints (superseded next steps)

## MeetingSplit v0.8.6 — Windows CI SUCCESS
- Github Actions run #39537216562: https://github.com/kl4ne/meetingsplit/actions/runs/39537216562
- **37 tests PASSED, 1 skipped** in Windows (job ran tests twice); PyInstaller EXE self-check passed; portable ZIP and Setup EXE verified; upload-artifact completed.
- Artifact ID **12317478170**: `MeetingSplit-v0.8.6-Windows-build-unvalidated-on-user-hardware` (~654 MB, retention 14 days).
- Large readable typography (+2 scale steps) across all five EN/ES pages published. Acceptance on ASUS Windows hardware remains pending; this is still a development build, not a production Release.
- User confirmed v0.8.5: internal D: accepted, CPU fallback transcribed six clips correctly in ~11 minutes, GPU CUDA 12 library missing. No changes to working audio engine in v0.8.6.

## VERIFIED USER ACCEPTANCE — MeetingSplit v0.8.5 (2026-10-20)
- User confirmed internal D: was ACCEPTED.
- User confirmed all six audio segments were successfully transcribed on CPU, taking approximately 11 minutes.
- Windows CUDA acceleration is still unavailable because cublas64_12.dll cannot load; CPU fallback works. No GPU fix claimed.
- User requested that all UI fonts be TWO STEPS LARGER, on every screen. v0.8.6 implements only layout/typography and version metadata, preserving working audio functions and storage security.
- Chromium QA visually checked five EN/ES screens at 1366x768, 1440x900, 1920x1080, 2560x1440. Windows CI and ASUS approval pending.

## v0.8.6 typography checkpoint
- User confirmed v0.8.5 accepted internal D: and transcribed 6 audio segments on CPU successfully in approximately 11 minutes.
- CUDA 12 is still missing cublas64_12.dll; fallback is functional but GPU acceleration is not fixed.
- User requested ALL UI letters two typographic steps larger, implemented in CSS for v0.8.6. Pending Windows CI and visual acceptance.

# MeetingSplit v0.8.5 — Checkpoint

User-reported v0.8.4 behavior: D: rejected after slow check; GPU DLL failure recovered to CPU but stayed on transcription 1/6 for a long period; Start Processing gave inadequate immediate feedback. Split-only mode succeeds.

The v0.8.5 source modifies storage querying, CPU performance mode and visual feedback. Actual acceptance on user ASUS is NOT yet confirmed. CUDA acceleration is not repaired; it is deliberately avoided when missing libraries.

Next: GitHub Windows CI, inspect build artifact, then verify C: and D: drives on ASUS, CPU transcript (2–5 min) and spinner/timer. Do not allow USB J: or synced folders; no Integrity modifications.

# MeetingSplit — MASTER_STATUS

**Version in development:** 0.8.5. **Repository:** public `kl4ne/meetingsplit`, `main`.

## Verified from previous run
- GitHub Actions run #39522806473 built v0.8.3 Windows portable and installer successfully. GitHub self-check/CI passed, but ASUS testing exposed two runtime issues.
- On ASUS Windows 11, internal D: selection was rejected; C: selection inside a cloud sync folder was rejected; C: root subfolder worked. The original drive verifier relied too heavily on `Get-Partition | Get-Disk`.
- ASUS CUDA transcription failed with `Library cublas64_12.dll is not found or cannot be loaded` after processing began.

## New v0.8.5 corrections awaiting hardware confirmation
- Use Windows CIM to classify drive D: if Storage module lacks BusType, with USB/PNP override and no network/USB exceptions.
- LocalAppData is starting folder for chooser; OneDrive/Google Drive remain intentionally excluded.
- GPU DLL preflight and lazy CUDA runtime failure retry via CPU, preserving transcript integrity.
- Unit and integration regressions added. Check GitHub CI before claiming Windows acceptance.

## Gates
- Build and verify v0.8.5 GitHub Actions.
- Validate D: selection and C: non-synced folder on actual ASUS; confirm removable J: is rejected.
- Validate GPU preflight CPU fallback without missing cublas error, then evaluate legitimate CUDA 12/cuDNN 9 installation for GPU.
- Validate actual transcriptions, model download, installer, 1–3h runs, license notices. No public Release until then.
- Do not touch Integrity Business Filings; do not upload audio or credentials to GitHub.
