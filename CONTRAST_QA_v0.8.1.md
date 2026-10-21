# MeetingSplit v0.8.1 — Contrast accessibility patch

## User report
Pale text was hard to read on white/light cards.

## Implementation
- `ui/styles.css`: reusable, explicit dark-ink, secondary and high-contrast accent colors for light surfaces.
- `MEETINGSPLIT_PREVIEW_v0.8.1.html`: matching styles for a standalone navigation demo.
- PayPal support, original recording engine, bilingual UI, footer signature and local processing remain unchanged.

## Visual/browser audit
- Chromium at 1366 × 768 using Playwright `page.set_content` with zero network access.
- All five views (Home, Import, Settings, Processing, Results) inspected in English and Spanish.
- 38 text-to-white contrast comparisons passed the WCAG AA numeric threshold 4.5:1.
- At least one visible example of each modified category was checked; **this is not a full independent WCAG certification**.
- Body did not scroll vertically and no JavaScript page error occurred during this audit.
- `qa/contrast_audit.py` reproduces this local check if Chromium and Playwright are available.

## Limitations
- Windows/Qt WebEngine real-device validation and NVIDIA transcription remain pending.
- PayPal's hosted checkout iframe is styled by PayPal and is not changed by this CSS.
- The full historical test suite sometimes hits timeout in this runtime; visual/contrast audit completed separately.
