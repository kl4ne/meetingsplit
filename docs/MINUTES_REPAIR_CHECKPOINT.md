# Minutes repair — checkpoint 1 (2026-11-27)

Base: de0f22a43a5a1f857ec5d47ded802037b2f34984 (0.8.18). No package, model, UI, transcription, storage, native dependency or release-gate change.

The long Windows case reported 8 editorial gaps and 15 narrative fallbacks; raw long-case responses and individual rejection reasons are unavailable in the repository. Do not infer the cause of all 23 events.

Reproducible code defect: an otherwise valid draft is discarded if its optional review fails. Preserve the draft only if it passes the exact same narrative validator as a revised document. Keep the existing fallback warning and needs_review classification. Invalid drafts still fall back to validated themes. Synthetic regressions exercise invalid citations and a review timeout.

Add explicit in-memory qa_trace callback to summarize_local: per-stage messages, schema, raw completed response, duration, rejection reason, accepted themes and fallback selection. Intended solely for isolated synthetic QA. No desktop caller, automatic persistence, output bundle, public logs, or real meeting trace. Transport metadata (actual model digest, token counts, done_reason on successful streams) still needs a QA adapter. Trace is not a substitute for semantic validation.

Next: reproduce an actual long-case failing section using the exact synthetic fixture and same model/runtime; compare direct chat with application API on the same data; evaluate document quality against a human reference. Do not build an EXE until the source-level editorial problem is demonstrated resolved. 

## Checkpoint 2

CI #45950804921 passed: 206 engine tests, 2 skipped, 11 browser tests, dependency audit no known findings. Added a new short bilingual synthetic comparison with a Spanish reference document and ten manual quality criteria. Direct API and application pipeline use identical source and exact Qwen3.5 9B digest / Ollama 0.40.18; their prompts and generation parameters are recorded, not assumed identical. Direct API is not a reproduction of the historical interactive chat. QA-only instrumentation records transport parameters, terminal token counts/timings and completed response/validation events. Offline replay uses recorded completed outputs, never calls Ollama, and rejects a mismatching narrative section. A dedicated isolated Linux CPU workflow runs only on the QA workflow file push; no installer, Windows GPU benchmark, long-case result, or automatic editorial approval. The exact historical long fixture is still outside the repository. No real meeting text is accepted by this harness.
