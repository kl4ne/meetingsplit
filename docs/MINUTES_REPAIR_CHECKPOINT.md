# Minutes repair — checkpoint 1 (2026-11-27)

Base: de0f22a43a5a1f857ec5d47ded802037b2f34984 (0.8.18). No package, model, UI, transcription, storage, native dependency or release-gate change.

The long Windows case reported 8 editorial gaps and 15 narrative fallbacks; raw long-case responses and individual rejection reasons are unavailable in the repository. Do not infer the cause of all 23 events.

Reproducible code defect: an otherwise valid draft is discarded if its optional review fails. Preserve the draft only if it passes the exact same narrative validator as a revised document. Keep the existing fallback warning and needs_review classification. Invalid drafts still fall back to validated themes. Synthetic regressions exercise invalid citations and a review timeout.

Add explicit in-memory qa_trace callback to summarize_local: per-stage messages, schema, raw completed response, duration, rejection reason, accepted themes and fallback selection. Intended solely for isolated synthetic QA. No desktop caller, automatic persistence, output bundle, public logs, or real meeting trace. Transport metadata (actual model digest, token counts, done_reason on successful streams) still needs a QA adapter. Trace is not a substitute for semantic validation.

Next: reproduce an actual long-case failing section using the exact synthetic fixture and same model/runtime; compare direct chat with application API on the same data; evaluate document quality against a human reference. Do not build an EXE until the source-level editorial problem is demonstrated resolved. 

## Checkpoint 2

CI #45950804921 passed: 206 engine tests, 2 skipped, 11 browser tests, dependency audit no known findings. Added a new short bilingual synthetic comparison with a Spanish reference document and ten manual quality criteria. Direct API and application pipeline use identical source and exact Qwen3.5 9B digest / Ollama 0.40.18; their prompts and generation parameters are recorded, not assumed identical. Direct API is not a reproduction of the historical interactive chat. QA-only instrumentation records transport parameters, terminal token counts/timings and completed response/validation events. Offline replay uses recorded completed outputs, never calls Ollama, and rejects a mismatching narrative section. A dedicated isolated Linux CPU workflow runs only on the QA workflow file push; no installer, Windows GPU benchmark, long-case result, or automatic editorial approval. The exact historical long fixture is still outside the repository. No real meeting text is accepted by this harness.

## Checkpoint 3 — observed A/B replay defects

Run 45951175096 completed; artifact 15177746760 inspected. Short CPU test: direct API 193.829 s / one call, pipeline 891.066 s / five calls. Neither document met the reference: direct invented budget allocation, pipeline editorial theme asserted an agreement where the source only discussed preparing examples; the revised narrative removed that false agreement but still described a non-approved proposal as rejected. Original validator rejected both narratives with its broad positive-agreement regex. The revised clause is NOT semantically acceptable as captured.

Targeted fixes: distinguish explicit negation from affirmative agreement, reject affirmative decisions in editorial synthesis as already required in narrative, distinguish unsupported rejection from non-approval, and retain a standalone same-row non-approval with its proposal. Do not flag a negated approval as a missing agreement; a later affirmative approval still triggers coverage. Regression tests use exact captured theme and review clause (citation ID remapped for single-section test), a faithful alternative, and negative controls. No new inference, no EXE, no relaxation of monetary or source constraints. Invalid editorial themes still have literal gaps; further repair is required to recover good prose and test quality end-to-end.

## Checkpoint 4 — selective narrative recovery

CI 45954020095 passed: 215 engine tests, 2 skipped, 11 browser tests. Added conservative recovery of complete independently validated paragraphs after full-section failure. Prefer valid revised paragraphs, then non-overlapping valid draft paragraphs, then original validated themes for uncovered IDs. Never salvage a clause from an invalid paragraph, accept an oversized response, or remove the review warning. A complete validated draft remains preferred over a failed revision. Five deterministic regressions cover partial recovery, invalid clauses, overlapping IDs, limits and integration. Does not prove semantic fidelity or recover rejected editorial themes; no new inference or build. Next: target editorial gaps with a small bounded repair request and test on the short fixture before the long case.

CI #45954418778: 219 passed, 1 failed, 2 skipped. Integration fixture supplied numbered theme titles ('Tema 1', etc.), which the editorial number guard correctly rejected because the source had no such numbers. Use descriptive non-numeric titles; keep the number guard unchanged. Rerun CI before accepting recovery.

## Isolated follow-up: bounded editorial gap repair

Prepared on a separate branch pending CI acceptance of selective narrative recovery. One narrowly scoped retry (up to five unique rejected source IDs per section), only for theme-level validation rejects. Existing valid themes are retained. Clear only gaps for exact source passages cited by a newly accepted nonduplicate repair, with no repeated rejection of that passage. Whole-section failures and failed retries retain their warnings; no recursive retry. This is not semantic coverage proof and does not address silently omitted themes. Five deterministic cases added, pending validation. No real inference or package.

## Isolated optimization candidate — exact quotation retry

Original A/B trace: 273.226 s extraction and 252.428 s retry; first record inserted "los" into "atención a visitantes" while citing rows 1 and 2. Preserve independently validated disjoint records and retry only affected, uncited and linked rows. Maximum five rows and half the input; unknown IDs, other validation errors, or larger scope use the existing retry. Missing targeted rows remain explicit review entries. No approximate matching. Recursive retry strictly shrinks input. Seven deterministic synthetic tests; performance improvement not yet measured. Planned version 0.8.19 only after quality validation if still available.

## Isolated citation and presentation repair (short artifact 15179585459)

Actual result: 819.771 s, five requests, 2432 characters; zero editorial gaps, one narrative fallback. The review used confidentiality and examples IDs in an inventory-only paragraph. Recovery counted those as covered, suppressing both validated themes. Add conservative distinct-word anchor checking to multi-theme narrative validation; it can reject a valid paraphrase and is not semantic proof. Retain warnings and validated source themes. For language presentation, translate only exact standalone budget templates deterministically; label clearly foreign verbatim statements as original quotations, not generated prose. Other arbitrary translations still need validation. Original evidence is unmodified. Five regressions; no inference or build yet. Branch independent of quotation retry.

## Combined validation candidate

Isolated quotation retry run #45959062442 passed all 89 focused regressions. Combined with the citation/presentation repair; full engine/browser/dependency CI must pass before any new real inference. No main change or version change yet.

## Consolidation experiment

Combined CI #45959366639 passed 237 engine tests, 2 skipped, 11 browser tests; dependency audit no known findings. Offline exact artifact replay #45959540874, artifact 15180570776, restored all six accepted themes with the new anchor guard; the prior narrative showed only four. The deterministic title-only overview prototype was insufficiently substantive. This isolated real-model candidate uses full accepted topic descriptions and recorded outcomes in a bounded overview, retains all themes and review warnings, and skips two rewrite calls via an explicit QA-only strategy. Default production strategy remains reviewed. Prior draft+review took 256.998 s of 819.771 s CPU time; actual savings and quality still unmeasured. Known residual defects: the source guidance sentence classified as a proposal, and unassigned pending question classified for review. Do not declare short acceptance solely from a green run. No new version or package.

## Real consolidated short result and classification repair

Run #45959825859 succeeded, artifact 15180493657 inspected. Four calls, 614.171 s vs 819.771 s before and 891.066 s original; 31% less elapsed time than original, CPU runner not ASUS. Selective retry kept ten records, retried IDs 1/2 in 44.798 s; original full retry 252.428 s. Six themes, no recorded editorial gaps. No narrative fallback because this strategy intentionally omits that stage, not proof of semantic acceptance. Defects: guidance misclassified as proposal, explicit notices rendered with source-only placeholder, unassigned question marked review, action paraphrase introduced deadline label. Narrow regression fix uses exact synthetic source patterns, keeps notices literal, and retains original commitment when deadline label unsupported. Still a candidate, not release. Validate against recorded outputs before rerunning model. Full-length QA and user acceptance remain open.

Replay #45993971134 failed during import (SyntaxError line 246). The patch operation interpreted a regex dollar-sign followed by a quote as a replacement expansion, duplicating a suffix of the file. Reconstructed from the exact known-good candidate deb7106, applied literal replacements, checked unique function definitions. No validator change beyond the intended classification repair. Rerun focused tests and exact artifact replay before integration.

## Integration checkpoint

Run #45994422839 passed 100 focused tests and all eight exact-response replay checks; artifact 15195382415. Integrate optional consolidated strategy and source classification repairs into draft PR #7. No production default change until long acceptance. Do not infer full editorial quality from these checks. The original historical 29-block fixture is not in the repo; the reproducible 2h15 / 11-block historical fixture is a different test, and will be used for controlled long source QA. No new package.

## Long synthetic result and repetition accounting

Run #45994579450, artifact 15196553252: 276 rows, 11 blocks, 36,178 characters, 16 calls, 1735.341 s CPU. All 11 historical facts correct; no unexpected decisions/actions/proposals, ungrounded quotes, structural or editorial gaps. Four empty extraction blocks (2,3,4,9; 112 rows) and 15 review records failed acceptance. Exact artifact inspection confirms each of those 112 rows and 15 review quotes repeats an earlier fully cited descriptive passage. Do not delete raw empty IDs or review records. Account for repetitions conservatively only when exact full-row text matches earlier validated topic evidence and contains no detected operational/uncertain markers; retain all diagnostics and a visible note. New text, partial/later citations and operational repetitions remain unresolved. Manifest now accounts for genuinely unresolved empty blocks (previously ignored) and still requires review for review-classified items. Executive brief includes literal owner and deadline fields if absent. Quality still not accepted: long document has repetition, generic themes, English literal citations, and some placeholder descriptions. Offline exact replay next; no model rerun, version bump or package yet.

## Long presentation localization checkpoint

Run #46001580090 passed 19 preflight tests; 3/4 translations accepted, one rejected for changing by Friday to before Friday (artifact 15198461769). Actual translation time 30.54 s, one call. Do not weaken deadline checks. Normalize explicit bilingual weekday relations, distinguish by/before/on/after, and preserve named deadline statements. Reuse three accepted responses only after strengthened validation; retry rejected Ana Ruiz translation and missing Alex Park commitment. Same-language 800 pesos approval restored verbatim; original items immutable. No general semantic certification or production integration yet. Generic/redundant editorial themes still need attention.

## Protected weekday replay

Exact artifact 15201659731: Alex Park response used "antes del jueves" rather than inclusive by Thursday; Ana Ruiz response used "más tardar el viernes" (missing a). 24 tests passed, 3/5 accepted. Restore only a single terminal weekday relation of a single affirmative action using exact source day and relation; require unchanged named actor, same day, one sentence, no detected conditions or negation, preserve commitment verb, run existing translation validator. No changes to original evidence, log before/after. No general semantic guarantee. Offline replay uses both recorded outputs and adds nine regression cases. No new inference or production integration yet.

## Integrated application candidate

Run #46009865198, artifact 15202657089: 33 tests and 5/5 exact recorded translations accepted, source records unchanged, no inference. Reviewed actual Markdown: all eleven expected facts, corrected Thursday/Friday deadlines, no missing amounts. Some generic/repeated themes from synthetic padding remain, and language translation is lexical validation only. Integrate an explicit localized_editorial strategy using existing loopback request and cancel token; select it in desktop job. Keep old reviewed and validated_editorial paths for comparison, immutable evidence items and separate presentation entries. A failed translation retains original quote and visible warning, manifest needs_review; no changes to release gate or main. Full CI and real-model integration QA still required. Do not assume complete editorial quality.

## Isolated long repeated theme presentation

Artifact 15202657089 Markdown inspected: 7 themes; two cite pieces of the same 3,785-character synthetic padding line at 01:12:09, which repeats the earlier complete source sentence. One separate 26-character incomplete fragment at 01:10:49 is not proven redundant and remains visible. Display-only compaction checks contiguous 1800-character source slices sharing timestamp, full concatenation comprised of >=2 prior complete descriptive statements plus at most an exact prefix. Never drop a theme merely for citing a subset of another theme, never remove evidence or raw editorial summaries. Preserve explicit note and diagnostics. Localize standalone weekday in overview too; no new inference. Separate QA branch while integrated application CI runs. No general semantic proof or package yet.

## Integration follow-up

Run #46010555628 passed 41 tests and exact artifact replay: seven themes reduced to five, unique incomplete fragment retained, all eleven facts intact. Artifact 15203432244 inspected: Spanish main descriptions preserve five decisions, four tasks, one proposal, one budget statement; quotations remain in their source languages. Remaining overlap in short topic descriptions is not assumed redundant. Full CI #46010385069: 276 engine tests passed, 2 skipped, one recovery test failed because the mock only supports source_rows and the new translation request uses records. Update test mock to return validated translations for its three known synthetic amounts and assert localized strategy, no rejected localization and unchanged extraction checkpoint behavior. Additional conservative guard requires earlier anchor theme to remain visible. Rerun full CI. No release or installer.

## Integrated short real-model checkpoint

Run #46015163014: 41 focused tests and all 14 automated short criteria passed. Exact artifact 15205494850 inspected (pipeline.md, comparison.json, pipeline-evidence.json): 4 requests, 875.204 s, 4557 characters; six themes; one accepted localization, no rejected localization; one original review record for row 12 (preparing examples), even though the editorial theme preserves it. The short document is materially more readable and captures the expected facts; summary substantially duplicates topic prose and proposal/pending appear in both themes and structured sections. Do not claim final editorial acceptance or guaranteed 31% time saving; the integrated run was only ~1.8% faster than original 891.066 s CPU. CI #46015055749: 280 passed, 2 skipped, one recovery assertion reports needs_review. The stub's two Spanish translations ("Se acordó gastar US$200." / "Se acordó invertir 300 pesos.") contain only one word from the existing language-marker set. Correct the stub with equally faithful natural phrasing ("Se acordó el gasto de US$200." / "Se acordó la inversión de 300 pesos.") and expose actual localization diagnostics on failure. Do not change production validation or expected recovery status. Full CI rerun pending. No new inference required to test fixture. Main and package unchanged.

## Structured event presentation integration

CI #46023661916 succeeded: 281 engine tests, 2 skipped, 11 browser tests; dependency audit no known findings. Recovery passes with the updated fixture. Offline #46023822998 passed 30 tests; exact artifact 15212165509, six raw themes, four displayed topics, 4557 to 3912 characters. Proposal row 8 and pending row 11 now displayed in their own sections. All original themes, items, sources and review diagnostics retained; move records reference original theme indices. No new inference, main or version change. Remaining review row 12 is a topic-discussion statement; preserve classification diagnostic until independently validated. Quality still requires manual comparison.

## Descriptive discussion candidate

Read exact artifact 15205494850 trace: extraction requested review for full row 12 and described it as a preliminary proposal pending formal confirmation. Actual source only says “Al final se habló de preparar ejemplos de atención a visitantes y revisar su claridad antes de la próxima capacitación.” The accepted editorial theme already describes this faithfully. Narrow correction only for single complete explicit discussion sentence with no task metadata, operational/uncertainty markers or amount; never promote to agreement or task. Preserve exact quote, discard unsupported model wording; replay must show exactly one changed item and no other changes. Separate branch, eight deterministic cases, no inference. Not yet integrated or approved.

## Final classification integration checkpoint

CI #46024213286 succeeded: 283 engine tests, 2 skipped, 11 browser tests, dependency audit no known findings. Exact replay #46024353373 passed 32 focused tests; only row 12 reclassified from review to descriptive topic; every other evidence record and source unchanged. Artifact 15211181219. Integrate the narrow correction in draft PR #7. Full validation on the combined revision is still required; no claim of semantic certification or a completed frozen Windows/GPU workload. No public release.

## Independent varied source acceptance

Full CI #46024899679 succeeded (291 engine +11 browser, two skipped); exact full-pipeline replay #46025010689 passed 9/9. This isolated fixture has 54 distinct descriptive utterances in nine thematic sections, 17 explicit expected outcomes, no repeated filler, and timestamps spanning 2h15m. It is intentionally not equivalent to 2h15m of continuous speech, nor the unavailable 29-block original. Uses the same pinned Qwen3.5 9B digest and Ollama 0.40.18, final localized strategy, standard CPU runner, records raw synthetic responses and extraction checkpoints. Strict rubric includes literal sources, expected outcomes, topic presence, no unresolved warnings, no translation failures. No semantic acceptance solely from IDs. No package or release yet.
