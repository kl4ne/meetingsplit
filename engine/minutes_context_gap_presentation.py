"""Presentation-only compaction of exactly duplicated contextual review quotes.

Keep all original gaps, records and diagnostics in the evidence sidecar.
Never reinterpret an omitted source as semantically verified.
"""
from .minutes_context_windows import MAX_GAP_SECONDS,_seconds
from .minutes_evidence import _SENTENCE_BREAK
from .minutes_source_accounting import audit_source_passages

def _key(ref):
    return ref['source_id'],ref['timestamp'],ref['quote']

def compact_context_gaps(blocks,items,themes,gaps,diagnostics,repetition=None):
    rows=[r for b in blocks for r in b]
    byid={r['id']:r for r in rows}
    positions={r['id']:i for i,r in enumerate(rows)}
    gap_ids={r['source_id'] for r in gaps}
    protected=set(diagnostics.get('overbudget_source_ids',()))
    for window in diagnostics['windows']:
        protected.update(window['review_ids'])
        protected.update(window['interruption_review_ids'])
        for rejected in window['rejections']:
            protected.update(rejected.get('source_ids',window['source_ids']))
        for rejected in window['quarantined_themes']:
            protected.update(r['source_id'] for r in rejected['theme']['sources'])
    cited={_key(r) for theme in themes for r in theme['sources']}
    item_ids={r['source_id'] for item in items if item['category']!='topic' for r in item['sources']}
    covered={x['item_index'] for x in (repetition or {}).get('repeated_review_items',[])}
    visible_reviews={_key(r) for i,item in enumerate(items)
        if item['category']=='review' and i not in covered for r in item['sources']}
    repeat_candidates={}
    for ref in gaps:
        i=ref['source_id'];pos=positions.get(i)
        if pos is None or not pos or i in protected or i in item_ids:continue
        current=byid[i];previous=rows[pos-1]
        text=current['text']
        if (previous['id']+1!=i or previous['id'] in gap_ids or previous['id'] in protected or
            previous['id'] in item_ids or not 0<=_seconds(current['timestamp'])-_seconds(previous['timestamp'])<=MAX_GAP_SECONDS or
            text!=previous['text'] or text!=ref['quote'] or ref['timestamp']!=current['timestamp'] or
            not text.endswith(('.', '!', '?')) or len(_SENTENCE_BREAK.split(text))!=1 or
            (previous['id'],previous['timestamp'],text) not in cited):
            continue
        repeat_candidates[_key(ref)]=previous['id']
    # Reuse existing conservative repeat guards. No new lexical classifier.
    trial=[r for r in gaps if _key(r) not in repeat_candidates]
    audit=audit_source_passages(blocks,items,themes,trial)
    eligible={_key(r) for r in audit['entries'] if r['status']=='exact_repeat'}
    visible=[];compacted=[]
    for ref in gaps:
        k=_key(ref)
        if k in visible_reviews:
            compacted.append({'source':ref,'reason':'already_displayed_in_review'})
        elif k in repeat_candidates and k in eligible:
            compacted.append({'source':ref,'reason':'adjacent_exact_repeat_of_cited_row',
                              'earlier_source_id':repeat_candidates[k]})
        else:
            visible.append(ref)
    return visible,compacted
