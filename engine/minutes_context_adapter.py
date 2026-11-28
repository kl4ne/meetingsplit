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
                         progress=lambda msg:None,trace=lambda *a,**k:None):
    plan=plan_context(blocks,items)
    themes=[];gaps={r['source_id']:r for r in plan['overbudget_sources']}
    diagnostics={'strategy':'contextual_qa','verification':'original_row_citation_not_semantic',
        'unit_count':len(plan['units']),'window_count':len(plan['windows']),
        'structured_source_ids':[r['source_id'] for r in plan['structured_sources']],
        'overbudget_source_ids':[r['source_id'] for r in plan['overbudget_sources']],
        'windows':[]}
    for n,units in enumerate(plan['windows'],1):
        if cancel:cancel.check()
        progress(f'Preparando contexto temático / Preparing thematic context: {n}/{len(plan["windows"])}')
        refs=[r for u in units for r in u['sources']]
        scope={'window':n,'language':language,'source_ids':[r['source_id'] for r in refs]}
        messages,schema=row_request(units,language)
        try:
            raw=request(messages,schema,stage='contextual_editorial',scope=scope)
            if cancel:cancel.check()
            out=quarantine_interrupted(validate_rows(raw,units,language),units,blocks)
            trace('contextual_editorial','accepted',scope,themes=out['themes'],gaps=out['gaps'],
                quarantined_themes=out['quarantined_themes'],rejections=out['rejections'])
        except JobCancelled:raise
        except (OSError,RuntimeError,ValueError) as exc:
            out={'themes':[],'gaps':refs,'review_ids':[],'interruption_review_ids':[],
                 'quarantined_themes':[],'rejections':[{'reason':str(exc)}]}
            trace('contextual_editorial','section_rejected',scope,error_type=type(exc).__name__,reason=str(exc))
        themes.extend(out['themes'])
        gaps.update((r['source_id'],r) for r in out['gaps'])
        diagnostics['windows'].append({**scope,'accepted_themes':len(out['themes']),
            'gap_ids':[r['source_id'] for r in out['gaps']],
            'review_ids':out['review_ids'],'interruption_review_ids':out['interruption_review_ids'],
            'quarantined_themes':out['quarantined_themes'],'rejections':out['rejections']})
    if cancel:cancel.check()
    return {'themes':themes,'gaps':[gaps[i] for i in sorted(gaps)],'diagnostics':diagnostics}
