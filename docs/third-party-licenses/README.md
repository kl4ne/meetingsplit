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
