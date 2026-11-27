"""Presentation-only accounting for exact repeated long source lines.

Never discard a theme merely because it cites a subset of another theme:
the two summaries can contain different details. Only recognize a line
that was split at the source window and is entirely repeated earlier
descriptive source text, with no new tail.
"""
from .minutes_evidence import (_AMOUNT,_AGREEMENT,_UNCERTAIN,_PROPOSAL,_NOTICE,
    _RESERVED_SCHEDULE,_ANNOUNCED_START,_PENDING,_DISAGREEMENT,_IMPLEMENTATION,
    _COMMITMENT,_DEADLINE_QUALIFIERS)

def compact_repeated_theme_sources(blocks,themes):
    rows=[row for block in blocks for row in block]
    by_id={r['id']:r for r in rows}
    guards=(_AMOUNT,_AGREEMENT,_UNCERTAIN,_PROPOSAL,_NOTICE,_RESERVED_SCHEDULE,
            _ANNOUNCED_START,_PENDING,_DISAGREEMENT,_IMPLEMENTATION,_COMMITMENT,*_DEADLINE_QUALIFIERS)
    candidates={}
    for index,theme in enumerate(themes):
        for ref in theme['sources']:
            row=by_id.get(ref['source_id'])
            text=ref['quote']
            if (row and text==row['text'] and 40<=len(text)<1800
                    and text.endswith(('.','!')) and not any(p.search(text) for p in guards)):
                candidates.setdefault(text,[]).append((row['id'],index))
    repeated={}
    pos=0
    while pos<len(rows):
        start=pos
        while (pos+1<len(rows) and len(rows[pos]['text'])==1800
               and rows[pos+1]['timestamp']==rows[pos]['timestamp']
               and rows[pos+1]['id']==rows[pos]['id']+1):
            pos+=1
        group=rows[start:pos+1]
        pos+=1
        if len(group)<2:
            continue
        whole=''.join(row['text'] for row in group).strip()
        for text,refs in candidates.items():
            prior=[(i,t) for i,t in refs if i<group[0]['id']]
            if not prior or not whole.startswith(text):
                continue
            rest=whole
            count=0
            while rest.startswith(text):
                count+=1
                rest=rest[len(text):].lstrip()
            if count>=2 and (not rest or text.startswith(rest)):
                earlier_id,theme_index=min(prior)
                for row in group:
                    repeated[row['id']]={'earlier_source_id':earlier_id,'earlier_theme_index':theme_index,
                                         'repeat_count':count}
                break
    kept=[];omitted=[];kept_indices=set()
    for index,theme in enumerate(themes):
        refs=theme['sources']
        matches=[]
        for ref in refs:
            previous=repeated.get(ref['source_id'])
            row=by_id.get(ref['source_id'])
            if (previous is None or row is None or ref['quote'] not in row['text']
                    or previous['earlier_theme_index'] not in kept_indices):
                matches=[]
                break
            matches.append({'source_id':ref['source_id'],**previous})
        if matches:
            omitted.append({'theme_index':index,'matches':matches})
        else:
            kept.append(theme)
            kept_indices.add(index)
    return kept,omitted
