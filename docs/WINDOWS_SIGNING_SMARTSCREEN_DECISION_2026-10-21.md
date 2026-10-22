# MeetingSplit — Windows signing and SmartScreen: decision file (2026-10-21)

**Planning only.** Version 0.8.6 QA, not publicly released. No
certificate has been purchased, no owner identity submitted, no
Microsoft Store application created, and no exe has been signed.

## Verified Microsoft documentation

- SmartScreen evaluates both publisher and file-hash reputation; signing
  helps identify the publisher but **does not automatically eliminate
  first-download warnings**.
  https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation
- Microsoft says EV signing certificates no longer bypass SmartScreen
  warnings; purchasing EV *solely* for this purpose is not justified.
  https://learn.microsoft.com/windows/apps/package-and-deploy/code-signing-options
- Microsoft Artifact Signing (formerly Trusted Signing) is an available
  code-signing route for individual developers in the US/Canada and for
  organizations in other eligible regions. It requires identity validation,
  has recurring costs, and does not give instant SmartScreen reputation.
- Store-published MSIX packages are signed by Microsoft. A separately
  distributed Inno Setup EXE needs an appropriate Authenticode signature;
  submitting an EXE/MSI to Store does not mean Microsoft signs the EXE.
- Microsoft also announced cryptographic-signing/trust transitions in
  late 2026. Do not pin publisher trust to a hard-coded Microsoft CA name:
  https://support.microsoft.com/en-us/servicing/os/windows/docs/2026/08/next-generation-code-signing

## Recommended decision — not yet approved by owner

Keep the current development installer unsigned while release is blocked.
Before public distribution choose whether the publisher should be a named
individual or the actual legal business entity, confirm the name the installer
shows, assess Microsoft Artifact Signing versus an OV certificate, and
consider future Microsoft Store/MSIX conversion as a separately scoped
product decision (do not rewrite the existing Inno installer silently).

An authorized signing stage should:
1. Obtain identity-validated signing via the selected provider without
   exposing keys/tokens in repository, logs, issue comments or model text.
2. Sign the FINAL frozen application binaries and installer with a trusted
   SHA-256 Authenticode and an appropriate timestamp.
3. Verify each signature using Windows trust APIs and record the result,
   signer identity, final installer SHA-256 and exact commit/release.
4. Confirm Windows 10/11 installation, SmartScreen messaging,
   accessibility and uninstall behavior on disposable machines.
5. Post source/notice compliance, license review, security review and
   real hardware acceptance before lifting release gate.

**No certificate procurement, signing, public Release, change to main,
version change or hardware operation can be inferred from this plan.**
The user must approve the public-facing publisher identity and expenses.
