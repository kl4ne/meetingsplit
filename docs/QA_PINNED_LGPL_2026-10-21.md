# MeetingSplit LGPL consolidation — Windows verified QA evidence

- Checkpoint date: 2026-10-21.
- Pinned Windows QA run: https://github.com/kl4ne/meetingsplit/actions/runs/39599798144
- Result: **success**. Source code test suite 82 passed, 2 skipped; frozen
  Qt/Whisper/FFmpeg self-check, native package audit, three audio formats and
  automatic install/reinstall/uninstall on disposable Windows passed.
- QA reports artifact ID `12346137559`; installer ID `12346625631`;
  portable ID `12346545817`. These are QA only; 14-day retention.
- Included packaged inventory: 680 files / 211 native /
  1,158,981,253 uncompressed bytes. No x264/x265 DLLs detected.
- LGPL FFmpeg upstream dated release source URL:
  https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-10-20-13-08/ffmpeg-n8.1.3-18-g46d899d7a0-win64-lgpl-shared-8.1.zip
  SHA-256 `453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a`.
- PyAV 16.0.1 upstream source SHA-256
  `dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf`.
- FFmpeg build `--enable-shared --disable-static --enable-version3`,
  `--disable-libx264 --disable-libx265 --disable-libxvid`.
  No enable-gpl or enable-nonfree in recorded configuration.
- Upgrade test run https://github.com/kl4ne/meetingsplit/actions/runs/39598790616:
  authentic prior `MeetingSplit_Setup_v0.8.5.exe` -> consolidated
  `MeetingSplit_Setup_v0.8.6.exe`, preserving external synthetic data;
  silent uninstall succeeded.
- Windows CI has no NVIDIA GPU. User hardware tests conducted previously
  do not automatically qualify this final changed LGPL package.
- A SHA-256 inventory and absence of known GPL codec names are evidence,
  not a formal legal or security certification.
- `release_allowed` remains false; no public Release.

