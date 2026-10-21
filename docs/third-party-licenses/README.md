## Additional exact upstream notices recovered 2026-10-21

The QA report's native file inventory contains
`_internal/tokenizers/tokenizers.pyd` (tokenizers 0.23.3) and 17 Cython
3.3.0 native compiler modules. The third-party collector's wheel metadata
had no original notice file for either distribution. The following source-
version-matched upstream texts are now retained and SHA-256-recorded in
`sources.json`:
- `Tokenizers-0.23.3-Apache-2.0.txt` (upstream tag v0.23.3).
- `Cython-3.3.0-Apache-2.0.txt` and
  `Cython-3.3.0-Pyrex-COPYING.txt` (upstream tag 3.3.0).
These were added **after** the internal QA package workflow
#39695270843 had started, so its frozen artifact must NOT be claimed to
contain them. Future final packaging must include/reconcile these exact
notices, along with missing Chromium and cuDNN licensing material.
The upstream license texts are not approval to distribute the entire
combined application.

---
# Original third-party license texts

These verbatim texts supplement the wheel notices collected in `legal/` in a
frozen build. `sources.json` records the exact upstream URL and SHA-256 for each
file. They do not relicense MeetingSplit's original code or certify distribution
compliance. CTranslate2 4.6.2 uses MIT. MeetingSplit selects LGPLv3 for the Qt
modules that permit it; unused GPL-only Qt modules are excluded from packaging.
The GPLv3 text also accompanies LGPLv3 as required by that license. FFmpeg native
libraries have their own build-dependent terms, distinct from the PyAV wrapper.

Qt shared libraries remain outside the executable in `_internal/PySide6` and
can be replaced with interface-compatible modified builds. Keep the application
closed while replacing a library, preserve a backup, retain the same architecture
and ABI, and include any dependent libraries/resources needed by the modification.
The application does not enforce hashes/signatures on these Qt shared libraries.
MeetingSplit's license expressly permits the reverse engineering needed to debug
such library modifications. This does not require modifying the Windows system
libraries or replacing any file in System32.

Release remains blocked pending the full native inventory, required third-party
copyright notices, matching source/build materials and remaining installer QA.
