"""Conservative interruption review for contextual editorial candidates.

Read original chronological rows, not artificial context-window boundaries.
A dangling grammatical connector at a real timestamp discontinuity or
end of transcript is a narrow review cue, NOT detection of all ASR errors.
Quarantine prose that relies on flagged rows; never complete missing speech.
"""
import re
from .minutes_context_windows import MAX_GAP_SECONDS,MAX_ROWS,MAX_SPAN_SECONDS,_seconds

_TERMINAL=re.compile(r'[.!?…]["»”\')\]]*\s*$')
_DANGLING=re.compile(r'\b(?:de|del|para|con|sin|por|que|porque|aunque|pero|'
    r'and|or|but|because|although|with|without|of|to|from|the)\s*$',re.I)

def interrupted_tails(blocks):
    rows=[r for b in blocks for r in b]
    found=[]
    for i,row in enumerate(rows):
        next_row=rows[i+1] if i+1<len(rows) else None
        if next_row is not None:
            gap=_seconds(next_row['timestamp'])-_seconds(row['timestamp'])
            if next_row['id']==row['id']+1 and 0<=gap<=MAX_GAP_SECONDS:
                continue
        text=row['text'].strip()
        if _TERMINAL.search(text) or not _DANGLING.search(text):
            continue
        start=i
        while start>0 and i-start+1<MAX_ROWS:
            prev=rows[start-1];current=rows[start]
            gap=_seconds(current['timestamp'])-_seconds(prev['timestamp'])
            span=_seconds(row['timestamp'])-_seconds(prev['timestamp'])
            if (prev['id']+1!=current['id'] or not 0<=gap<=MAX_GAP_SECONDS
                or span>MAX_SPAN_SECONDS or _TERMINAL.search(prev['text'])):
                break
            start-=1
        found.append({'source_ids':[r['id'] for r in rows[start:i+1]],
            'reason':'possible_interrupted_clause_at_source_boundary'})
    return found

def quarantine_interrupted(result,units,blocks):
    """Keep original candidate diagnostics; never silently edit a claim.

    All citations of a quarantined theme become review material. Existing
    model rejections and explicit review IDs survive. No extra model call.
    """
    byid={r['source_id']:r for u in units for r in u['sources']}
    tails=interrupted_tails(blocks)
    flagged={i for t in tails for i in t['source_ids']} & set(byid)
    kept=[];quarantined=[]
    gaps={r['source_id']:r for r in result['gaps']}
    for i in flagged:gaps[i]=byid[i]
    for theme in result['themes']:
        affected=sorted({r['source_id'] for r in theme['sources']} & flagged)
        if not affected:
            kept.append(theme);continue
        quarantined.append({'theme':theme,'interrupted_source_ids':affected,
                            'reason':'theme relies on a possible interrupted clause'})
        gaps.update((r['source_id'],r) for r in theme['sources'])
    return {**result,'themes':kept,'gaps':[gaps[i] for i in sorted(gaps)],
            'interruption_review_ids':sorted(flagged),
            'quarantined_themes':quarantined,'review_required':True}
