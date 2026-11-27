# Minutes repair — checkpoint 1 (2026-11-27)

Base: de0f22a43a5a1f857ec5d47ded802037b2f34984 (0.8.18). No package, model, UI, transcription, storage, native dependency or release-gate change.

The long Windows case reported 8 editorial gaps and 15 narrative fallbacks; raw long-case responses and individual rejection reasons are unavailable in the repository. Do not infer the cause of all 23 events.

Reproducible code defect: an otherwise valid draft is discarded if its optional review fails. Preserve the draft only if it passes the exact same narrative validator as a revised document. Keep the existing fallback warning and needs_review classification. Invalid drafts still fall back to validated themes. Synthetic regressions exercise invalid citations and a review timeout.

Add explicit in-memory qa_trace callback to summarize_local: per-stage messages, schema, raw completed response, duration, rejection reason, accepted themes and fallback selection. Intended solely for isolated synthetic QA. No desktop caller, automatic persistence, output bundle, public logs, or real meeting trace. Transport metadata (actual model digest, token counts, done_reason on successful streams) still needs a QA adapter. Trace is not a substitute for semantic validation.

Next: reproduce an actual long-case failing section using the exact synthetic fixture and same model/runtime; compare direct chat with application API on the same data; evaluate document quality against a human reference. Do not build an EXE until the source-level editorial problem is demonstrated resolved. 
