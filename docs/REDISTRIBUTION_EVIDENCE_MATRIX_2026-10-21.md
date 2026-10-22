## Additional package audit findings and source references (2026-10-21)

The 680-file inventory also contains 17 native Cython 3.3.0 compiler modules
and `_internal/tokenizers/tokenizers.pyd` from tokenizers 0.23.3. These
are not represented by original license files in the previous collector
output. Exact upstream Apache-2.0 and Cython historical Pyrex COPYING
texts have now been added to `docs/third-party-licenses/` with SHA-256
receipts, but **not** to the already running QA package #39695270843.
Review and include them in a subsequent final distribution package.
`flatbuffers` appeared as a metadata-only dependency with no corresponding
shipped package file, and does not require treatment as a bundled binary
on the current evidence; reassess if it is later included.

Qt's own SBOM documents can be generated in SPDX 2.3 and are installed in
a Qt Online Installer `sbom/` folder, but those SDK build records MUST NOT
be misrepresented as exact PySide6 wheel binary provenance unless matched:
https://doc.qt.io/qt-6.12/sbom.html

For WebEngine's separate release/versioning (Chromium baseline vs Qt 6.12),
match upstream's `CHROMIUM_VERSION` to the shipped module instead of
assuming the PySide6 Python package version identifies the exact Chromium
security patch level:
https://wiki.qt.io/QtWebEngine/ChromiumVersions

---
# MeetingSplit 0.8.6 — exact native redistribution evidence matrix (2026-10-21)

**Scope:** Internal QA source/binary provenance review, NOT legal approval. No
public Release, change of version, commercial license purchase, or redistribution
is authorized. This file addresses the frozen LGPL development build from
GitHub Actions #39599798144 (source branch `e545348d`) and the verified
report archive `MeetingSplit-pinned-LGPL-QA-reports-2026-10-21.zip`
(SHA-256 `428a5540b90ef049ccd0eb24b51cd082bc4507a457a94feb43fbb53288df1db3`).

## What has already been evidenced

- Pinned BtbN FFmpeg n8.1.3-18-g46d899d7a0, shared Windows LGPL build,
  source asset SHA-256 `453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a`.
  Configure flags are saved in `build/legal/ffmpeg-build.txt`, including
  `--enable-version3 --enable-shared --disable-static`; none of the tested
  `--enable-gpl`, `--enable-nonfree`, `--enable-libx264`/x265 flags
  appear. Windows MP3/M4A/WAV encode+decode succeeded. This is *not* proof
  of licensing for every linked library.
- PyAV 16.0.1 compiled from the official source tarball SHA-256
  `dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf`;
  repaired wheel digest `37b60cb5cc79acf539611601ac7a9a4f17cfbf8fed3a672b1eea1aa5c9a8bcaf`.
- Report enumerates **680** frozen files, **211** native and no x264/x265
  named binary; embedded notices match the report's per-file SHA-256 records.
  The EXE/DLL bytes are NOT in the report ZIP: native checksums beyond the
  included notice files could not independently be rehashed here.
- Exact binary inventory includes:
  - `_internal/PySide6/Qt6WebEngineCore.dll` SHA-256
    `54488cfc8fea4057377302cec5a1fb1100fb4bc4231cd7e60f43e4fcff28e89e`;
  - `_internal/PySide6/QtWebEngineProcess.exe` SHA-256
    `91560b137a26e89df4a148479aa830a915870a5b1b3c46715b2c13a7ba21388b`;
  - `_internal/ctranslate2/cudnn64_9.dll` SHA-256
    `c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05`.

## Specific outstanding deliverables, not automatically cleared

| Exact library group | Evidence already present | Required BEFORE public distribution |
| --- | --- | --- |
| FFmpeg 8.1.3 shared CLI + PyAV FFmpeg DLLs | Pinned archive and PyAV source hashes; configure flags; dependency paths | Supply matching upstream **source commit and all third-party source/build scripts**, local change diff (if any), copyright/license texts, exact reproduction instructions, user-visible LGPL acknowledgement, library-replacement instructions, and legally appropriate source access. Match *actual linked* libraries, not just the CLI. |
| Qt 6.12/PySide6 6.12 | Frozen DLL inventory, Qt LGPLv3 notice | Capture exact Qt/PySide source and patches, applicable LGPLv3 texts, distribution notice, and proof that Windows users can replace/relink compatible Qt DLLs and run the modified combination. |
| Qt WebEngine/PDF 6.12.0.140 / Chromium | Qt6WebEngineCore.dll and QtWebEngineProcess.exe hashes | Obtain **actual compiled WebEngine/Chromium version and complete third-party notices** (including bundled licenses), matching code/source offers and evidence of associated Chromium security fixes. No Chromium-named notice file was detected in the frozen inventory. |
| CTranslate2 4.6.2 with bundled cuDNN | MIT text and exact cudnn64_9.dll hash | Determine embedded cuDNN version, binary origin and precise NVIDIA SDK redistribution rights, including notices. Optional separately downloaded CUDA consent must not be treated as license for the **base bundled DLL**. |
| Optional CUDA / cuDNN | Pin + opt-in download receipts, vendor license text; no included archives in base installer | Independently verify each original asset, permitted installation/redistribution pattern, archive notices, extraction license, driver compatibility, data folder permissions and runtime tests. |
| Ollama 0.40.6 + Qwen3 4B | SHA-pinned optional runtime + fetched model receipt/Apache-2.0 claim | Check exact runtime archive 3rd party notices, model tag/digest/license returned by `/api/show`, non-network generation and human review of minutes. |
| All other native modules (WebEngine, CT2, AV, Qt plugins) | Hashed package inventory | Native vulnerability assessment of actual binary versions/PE signatures and libraries, and an SBOM mapping shipped file hash to upstream product/version. |
| MeetingSplit original custom freeware LICENSE | Explicit carve-out for LGPL library modification/relinking | Owner/qualified counsel review for contradictions and final EULA wording, and required prominent third-party notices. |

### Authoritative vendor materials consulted

- FFmpeg licensing and its **corresponding-source checklist**:
  https://ffmpeg.org/legal.html
- Qt 6.12 version-aware module licenses, Chromium/WebEngine third-party code:
  https://doc.qt.io/qt-6/licenses-used-in-qt.html
- Qt's LGPLv3 requirements and user replacement/relinking rights:
  https://www.qt.io/development/open-source-lgpl-obligations
- Qt's September 24, 2026 explanation of separate Qt WebEngine versioning:
  https://www.qt.io/blog/qt-webengine-will-release-separate
- NVIDIA SDK licenses are distinct from its other software license; inspect exact
  cuDNN/CUDA EULAs (do NOT infer permission from a generic community-product license):
  https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-licensing-overview-and-faq/
  https://docs.nvidia.com/cuda/eula/index.html

**Technical gate:** Running `qa/verify_release_evidence.py` and unit tests
does NOT imply the above deliverables exist or that independent legal/security
review passed. Keep `qa/release_gate.json` with `release_allowed=false`.
