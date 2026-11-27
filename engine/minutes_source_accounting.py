"""Structural audit of original transcript passages, not semantic verification.

No model calls; preserve any source sentence not represented by a citation
or a safely accounted exact repeat. Never infer meaning from source IDs alone.
"""
from .minutes_evidence import (_SENTENCE_BREAK,_AMOUNT,_AGREEMENT,_UNCERTAIN,
    _PROPOSAL,_NOTICE,_RESERVED_SCHEDULE,_ANNOUNCED_START,_PENDING,
    _DISAGREEMENT,_IMPLEMENTATION,_COMMITMENT,_DEADLINE_QUALIFIERS,_PERSONAL_TENTATIVE)

def audit_source_passages(blocks,items,themes,editorial_gaps=()):
    refs={}
    def add(ref,kind):
        refs.setdefault(ref['source_id'],[]).append((ref['quote'],kind))
    for item in items:
        # The renderer shows original quotes for these records. Ordinary
        # topics have no guaranteed original quotation in the report.
        if item['category']!='topic' or any(_AMOUNT.search(r['quote']) for r in item['sources']):
            for ref in item['sources']:
                add(ref,'structured_or_review')
    for theme in themes:
        for ref in theme['sources']:
            add(ref,'editorial_citation')
    for ref in editorial_gaps:
        add(ref,'existing_gap')
    # Callers pass the original pre-compaction themes; their separate
    # presentation diagnostics retain exact repetitions and structured moves.
    # A cited source is not proof all of its meaning was retained.
    guards=(_AMOUNT,_AGREEMENT,_UNCERTAIN,_PROPOSAL,_NOTICE,_RESERVED_SCHEDULE,
            _ANNOUNCED_START,_PENDING,_DISAGREEMENT,_IMPLEMENTATION,_COMMITMENT,
            _PERSONAL_TENTATIVE,*_DEADLINE_QUALIFIERS)
    prior={};entries=[];gaps=[]
    for block in blocks:
        for row in block:
            for part in _SENTENCE_BREAK.split(row['text']):
                quote=part.strip()
                if not quote:continue
                ref={'source_id':row['id'],'timestamp':row['timestamp'],'quote':quote}
                # Search complete sentences of each citation, not substrings
                # that could represent a shorter sentence inside a clause.
                matches=[kind for cited,kind in refs.get(row['id'],())
                         if quote in [s.strip() for s in _SENTENCE_BREAK.split(cited)]]
                eligible=not any(p.search(quote) for p in guards)
                if matches:
                    kind=next(k for k in ('structured_or_review','editorial_citation','existing_gap') if k in matches)
                    entry={**ref,'status':kind}
                    if eligible and kind!='existing_gap':
                        prior.setdefault(quote,row['id'])
                elif eligible and quote in prior:
                    entry={**ref,'status':'exact_repeat','earlier_source_id':prior[quote]}
                else:
                    entry={**ref,'status':'uncited_passage'}
                    gaps.append(ref)
                entries.append(entry)
    return {'verification':'structural_citation_only_not_semantic',
            'entries':entries,'uncited_passages':gaps}
