# Isolated QA build request for MeetingSplit 0.8.6

This branch is an explicit QA build request, NOT a release. The user's instruction
is to validate the consolidated development installer only, without publishing a
new version or asking the user to install it. The `main` workflow remains
manual-only for installer packaging. This temporary branch enables a single push
trigger with the same gated QA packaging steps and disposable test runner.

- Source checkpoint: 9d41c9b66980eec917c15d3ed36b5858e2e1fbf3
- `qa/release_gate.json` remains `release_allowed:false`.
- The build produces GitHub Actions development-only artifacts.
- No binary or archive is committed to `main` or GitHub Releases.
- No change to Integrity Business Filings.
