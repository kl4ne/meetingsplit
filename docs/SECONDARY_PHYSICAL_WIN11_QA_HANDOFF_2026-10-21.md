# MeetingSplit 0.8.6 — second physical Windows 11 QA handoff (2026-10-21)

**User confirmed access to a SECOND Windows 11 physical computer.**
No agent remote access to that machine exists in this chat; user must execute
the signed-off, read-only preflight and opt-in guided GUI steps locally.
**NO tests have yet been executed on the user's second PC.**

## Verified inputs, unchanged from prior passes

- Exact development-only installer is GitHub Actions #39695270843, artifact **#12391430920**:
  https://github.com/kl4ne/meetingsplit/actions/runs/39695270843/artifacts/12391430920
- Outer artifact ZIP SHA-256 (from GitHub immutable artifact metadata):
  `9217849517b9b47ecaaa9b4d6fdf892593ba007f0b28c05fd73ab38e8065986b`
- Built from commit `90238d621160e05097e7b72c3a1c26b18b4a31cd`,
  historical internal QA version **0.8.6** with 102 tests passed/2 skipped
  and disposable silent installer checks passed.
- Artifact is not a public release, must NOT be redistributed. User needs
  an authorized GitHub login to download while artifact is retained.

## Prepared portable user-side QA kit

A ZIP kit created for the **current conversation**:
`MeetingSplit-Windows11-Segunda-PC-QA-Kit.zip`
SHA-256 `41f5b1b041e78d66f2fe5a0244a96148ed74eb11c929c07852ace4d404dd57d4`,
size 8,334 bytes, tested ZIP CRC; exact files:

- `01-COMPROBAR-PC.cmd` — SHA-256 `d274a7cc4f869c266ce2316fe1a0c3f3a218997c0884a6e9fcb6ecc28e5095c6`
- `02-PRUEBAS-GUIADAS.cmd` — SHA-256 `1d0a240de9bf946481581af1765eb6fe8f6500ad2e9400c7c6e038dd2fe830d5`
- `MeetingSplit-Physical-QA.ps1` — SHA-256 `af2a69df7cf24a26086f90096d1c27ff196457dc0710ef6c7297b01e6534290a`
- `README-LEEME.txt` — SHA-256 `56d8bb136ceaf0031c40793926c241e8d67d0e3daded23392066ea7c5c4de405`

This kit was generated in the conversation workspace and linked there; **the kit
bytes are NOT stored in this GitHub repository**. A new chat should ask the
user to reattach the ZIP or regenerate from these specifications if unavailable.
Do not invent a new sandbox link.

## How the user runs the test, no command-line typing necessary

1. On a fresh test account on the SECONDARY Windows 11 x64 PC, download
   the artifact ZIP from the GitHub Actions artifact link above and the
   separate small kit from the assistant's response.
2. Extract ONLY the small kit. Rename the UNEXTRACTED GitHub installer
   artifact ZIP to `MeetingSplit-QA-installer-artifact.zip` and place next
   to the kit's two `.cmd` files. The SHA verification occurs before
   extraction or installation.
3. Double-click **01-COMPROBAR-PC.cmd** as standard, non-elevated user.
   Preflight checks Windows 11 x64, internal fixed disk/16GiB free, all
   visible HKCU/HKLM MeetingSplit uninstall registrations, standard known
   installation paths, and prints detected GPU; it does NOT extract or install.
4. Only if it prints **PREFLIGHT PASSED**, double-click
   **02-PRUEBAS-GUIADAS.cmd** as standard user. Read prompts and explicitly
   type CONTINUE for opt-in actions. It verifies the artifact SHA, extracts
   under a unique LOCALAPPDATA QA folder and exercises:
   - Real interactive wizard **pre-install cancellation**. The script
     requires Inno Setup exit **2** plus no installed app executable.
     Exit 0 or an error is NOT counted as cancellation.
   - Real interactive clean installation in the isolated QA path, no optional
     CUDA/Ollama task selected, plus exact v0.8.6 frozen self-check.
   - User-observed five views in EN/ES, using synthetic-only data folder.
   - Real interactive uninstallation (requires exit 0), delays for Inno's
     temporary uninstaller clone, verifies EXE removed and synthetic
     data outside application folder preserved.
5. Share only the generated **qa-summary-shareable.json** (no personal
   Windows paths or logs). Do not upload the unredacted Inno Setup logs.

## Safety constraints and uncovered acceptance stages

- No admin/elevated PowerShell, no new software certificates, no CUDA or
  Ollama vendor download, no driver, OS settings, firewall/registry
  modifications outside the normal installer operations, and no personal
  recording should be involved in this FIRST ROUND.
- If preflight detects an existing MeetingSplit installation, DO NOT
  proceed; isolate in a new Windows account / other PC rather than
  overwriting or uninstalling the owner's installation.
- The script will **not** automatically remove its own QA evidence folder.
  The actual app installer/uninstaller may create normal app settings and
  uninstall registry entries **in the disposable test account**, which
  is why the separate test account is required.
- **Inno exit code 2** = user cancelled before install; **exit 5** =
  cancelled during actual installation. Mid-copy cancellation is a
  **separate outstanding task**, not covered by this first-round script.
  Reference: https://jrsoftware.org/ishelp/topic_setupexitcodes.htm
- Real CUDA/Ollama large downloads and network interruption require
  the user's separate vendor-license consent, capable hardware, disk
  capacity and confirmed results from this first stage. The second
  PC may not contain NVIDIA GPU; ASUS GPU hardware acceptance is separate.
- Current source branch contains newer notice, Qt UI diagnostic and
  additional security changes that POSTDATE old QA installer commit; do not
  claim this old candidate certifies the latest source files.
- Release policy remains `qa/release_gate.json` `release_allowed=false`,
  version 0.8.6, PR #1 draft, main unchanged and Integrity untouched.

## Remaining process

Await actual physical preflight/GUI test results from user. In the meantime,
read previous `MASTER_STATUS.md` and `NEXT_ACTION.md`, reuse complete
QA evidence, and do not rerun costly Windows builds needlessly.
