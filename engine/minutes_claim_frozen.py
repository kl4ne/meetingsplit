"""QA-only reuse of a previously reconciled extraction ledger.

Literal validation is not semantic certification. Do not reinterpret or add
outcomes, hide old extraction warnings, or send these records to a model as
instructions. This opt-in avoids repeating extraction for a controlled test.
"""
from copy import deepcopy
from .minutes_evidence import _CATEGORIES,_field,_literal

def frozen_extraction(evidence,blocks,language):
    if not isinstance(evidence,dict) or evidence.get('narrative_strategy')!='localized_editorial':
        raise ValueError('Expected original reconciled 0.8.19 evidence')
    items=evidence.get('items');empty=evidence.get('empty_block_ids')
    if (not isinstance(items,list) or len(items)>50000 or not isinstance(empty,list)
        or any(type(i) is not int or not 1<=i<=len(blocks) for i in empty)
        or len(set(empty))!=len(empty) or evidence.get('source_blocks')!=len(blocks)
        or evidence.get('empty_blocks')!=len(empty)):
        raise ValueError('Invalid frozen extraction metadata')
    rows={r['id']:r for b in blocks for r in b}
    fields={'text_'+l for l in (('es','en') if language=='both' else (language,))}
    for item in items:
        if not isinstance(item,dict) or set(item)!=fields|{'category','sources','owner','due'} or item['category'] not in _CATEGORIES:
            raise ValueError('Invalid frozen extraction item')
        refs=item['sources']
        if not isinstance(refs,list) or not 1<=len(refs)<=5000:
            raise ValueError('Invalid frozen source list')
        for ref in refs:
            if not isinstance(ref,dict) or set(ref)!={'source_id','timestamp','quote'} or type(ref['source_id']) is not int:
                raise ValueError('Invalid frozen source reference')
            row=rows.get(ref['source_id']);quote=_field(ref['quote'],1800)
            if not row or row['timestamp']!=ref['timestamp'] or quote not in row['text']:
                raise ValueError('Frozen reference differs from original')
        for field in fields:_field(item[field],2400)
        quotes=[r['quote'] for r in refs]
        for field in ('owner','due'):
            if item[field] is not None and _literal(item[field],quotes)!=item[field]:
                raise ValueError('Invalid frozen outcome metadata')
    return deepcopy(items),list(empty)
