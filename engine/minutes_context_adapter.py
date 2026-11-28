"""Experimental contextual editorial adapter, selected only by explicit QA strategy.

Extraction, reconciliation, localization, source accounting and rendering remain
in summarize_local. Contextual calls use the same loopback transport and cancel
token, no editorial repair requests; transport CPU fallback remains existing policy.
"""
from .control import JobCancelled
from .minutes_context_windows import plan_context
from .minutes_context_row_citations import row_request,validate_rows
from .minutes_context_interruptions import quarantine_interrupted

def contextual_editorial(blocks,items,language,request,*,cancel=None,
                         progress=lambda msg:None,trace=lambda *a,**k:None,claim_mode=False):
    from .minutes_context_claims import claim_request,validate_claims,recovery_targets
    from .minutes_context_interruptions import interrupted_tails
    plan=plan_context(blocks,items)
    stage='contextual_claim_editorial' if claim_mode else 'contextual_editorial'
    themes=[];gaps={r['source_id']:r for r in plan['overbudget_sources']}
    diagnostics={'strategy':'contextual_claim_qa' if claim_mode else 'contextual_qa','verification':'claim_local_literal_citations_not_semantic' if claim_mode else 'original_row_citation_not_semantic',
        'unit_count':len(plan['units']),'window_count':len(plan['windows']),
        'structured_source_ids':[r['source_id'] for r in plan['structured_sources']],
        'overbudget_source_ids':[r['source_id'] for r in plan['overbudget_sources']],
        'windows':[]}
    for n,units in enumerate(plan['windows'],1):
        if cancel:cancel.check()
        progress(f'Preparando contexto temático / Preparing thematic context: {n}/{len(plan["windows"])}')
        refs=[r for u in units for r in u['sources']]
        scope={'window':n,'language':language,'source_ids':[r['source_id'] for r in refs]}
        messages,schema=(claim_request if claim_mode else row_request)(units,language)
        try:
            raw=request(messages,schema,stage=stage,scope=scope)
            if cancel:cancel.check()
            if claim_mode:
                out=validate_claims(raw,units,language,blocks=blocks,repair_quote_pairs=True,neutralize_partial_titles=True)
                out.update(interruption_review_ids=sorted({i for t in interrupted_tails(blocks) for i in t['source_ids']} & set(scope['source_ids'])),quarantined_themes=[],recovery_target_ids=recovery_targets(units,out))
            else:
                out=quarantine_interrupted(validate_rows(raw,units,language),units,blocks)
            trace(stage,'accepted',scope,themes=out['themes'],gaps=out['gaps'],
                quarantined_themes=out['quarantined_themes'],rejections=out['rejections'])
        except JobCancelled:raise
        except (OSError,RuntimeError,ValueError) as exc:
            out={'themes':[],'gaps':refs,'review_ids':[],'interruption_review_ids':[],
                 'quarantined_themes':[],'rejections':[{'reason':str(exc)}]}
            trace(stage,'section_rejected',scope,error_type=type(exc).__name__,reason=str(exc))
        themes.extend(out['themes'])
        gaps.update((r['source_id'],r) for r in out['gaps'])
        diagnostics['windows'].append({**scope,'accepted_themes':len(out['themes']),
            'gap_ids':[r['source_id'] for r in out['gaps']],
            'review_ids':out['review_ids'],'interruption_review_ids':out['interruption_review_ids'],
            'quarantined_themes':out['quarantined_themes'],'rejections':out['rejections'],
            **({k:out.get(k,[]) for k in ('quote_repairs','neutralized_titles','recovery_target_ids')} if claim_mode else {})})
    if cancel:cancel.check()
    return {'themes':themes,'gaps':[gaps[i] for i in sorted(gaps)],'diagnostics':diagnostics}
