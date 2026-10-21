# MeetingSplit v0.8.6 — Typography QA

Request: two-step font enlargement across all five screens, English and Spanish.

Changes: 89 explicit font-size declarations enlarged, 7 responsive display clamped values scaled, layout/sidebar/topbar/panels/selects/CTAs reflowed for readability. Original audio pipeline, PayPal destination, storage policy and author privacy unchanged.

Visual Chromium QA: 5 screens x 2 UI languages x 4 screen sizes (1366x768, 1440x900, 1920x1080, 2560x1440) = 40 navigation/viewport combinations. No JavaScript page errors and no global horizontal overflow were reported. Shorter viewports use an internal scroll only where needed, while screens remain independent.

Regression tests: 13 selected automated tests passed (typography, storage, CUDA fallback regression). Full Linux suite exceeded timeout; no approval based on an incomplete execution. Windows GitHub Actions release build remains required.

Known remaining issue: RTX 4070 CUDA 12 dependency cublas64_12.dll is missing; user confirmed v0.8.5 fallback to CPU successfully processed six clips in ~11 minutes and D: was accepted.

No modification to Integrity Business Filings.
