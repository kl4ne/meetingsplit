"""Context transport with explicit original-row citation and review accounting.

QA-only. Context units support reading, never automatically certify all rows.
Do not weaken the operational-decision guard or infer speaker identity.
"""
import json
from .minutes_context_windows import request_spec as context_request
from .minutes_evidence import (_NUMBER,_amount_keys,_field,_unique_keys,
    editorial_decision_error,changes_operational_meaning)
from .minutes_brief import (_language_matches,_PROPOSAL_ASSERTION,_EXPLICIT_PROPOSAL_SOURCE)

def row_request(units,language):
    messages,schema=context_request(units,language)
    refs=[r for u in units for r in u['sources']]
    ids=[r['source_id'] for r in refs]
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate raw source ID in window')
    theme=schema['properties']['themes']['items']
    fields=theme['properties']
    del fields['unit_ids']
    fields['source_ids']={'type':'array','items':{'type':'integer','enum':ids},
        'minItems':1,'maxItems':len(ids),'uniqueItems':True}
    theme['required']=list(fields)
    schema['properties']['review_ids']={'type':'array','items':{'type':'integer','enum':ids},
        'maxItems':len(ids),'uniqueItems':True}
    schema['required']=['themes','review_ids']
    prompt=messages[0]['content'].replace(
        'Cite the supporting context unit IDs; one unit can support more than one distinct theme.',
        'Cite original fragment IDs (source_ids), not context unit IDs. Cite only fragments whose content the theme actually represents. A theme may cite many fragments, and different themes may cite the same fragment. ')
    prompt+=(' Return review_ids for unclear, incomplete, or uncertain original fragments; do not guess their meaning. '
        'A review ID can also be cited if only part of that fragment is understood. '
        'Do not include entire units merely because a neighboring sentence was summarized. '
        'For a clearly fictional example of approval, describe the example as hypothetical in indirect speech, '
        'rather than copying an affirmative approval statement into the thematic prose. '
        'The original quotations remain in the evidence record. Do not present the example as an actual approval. '
        'Do not claim an action or agreement just because a speaker quoted one.')
    messages[0]['content']=prompt
    return messages,schema

def validate_rows(raw,units,language):
    _,schema=row_request(units,language)
    doc=json.loads(raw,object_pairs_hook=_unique_keys)
    byid={r['source_id']:r for u in units for r in u['sources']}
    def valid_ids(ids,allow_empty=False):
        return (isinstance(ids,list) and (allow_empty or bool(ids))
                and all(type(i) is int and i in byid for i in ids)
                and len(ids)==len(set(ids)))
    if (not isinstance(doc,dict) or set(doc)!={'themes','review_ids'}
        or not isinstance(doc['themes'],list)
        or len(doc['themes'])>schema['properties']['themes']['maxItems']
        or not valid_ids(doc['review_ids'],True)):
        raise ValueError('Invalid row-accounted response')
    langs=('es','en') if language=='both' else (language,)
    fields={f'{field}_{lang}' for lang in langs for field in ('title','summary')}
    themes=[];covered=set();failed=set();seen=set();rejections=[]
    review=set(doc['review_ids'])
    for t in doc['themes']:
        ids=t.get('source_ids') if isinstance(t,dict) else None
        try:
            if not valid_ids(ids) or set(t)!=fields|{'source_ids'}:
                raise ValueError('Invalid original source IDs or fields')
            refs=[byid[i] for i in sorted(ids)]
            quotes=' '.join(r['quote'] for r in refs)
            texts={k:_field(t[k],100 if k.startswith('title_') else 700) for k in fields}
            for lang in langs:
                if not _language_matches(texts['summary_'+lang],lang):
                    raise ValueError('Wrong synthesis language')
            for value in texts.values():
                reason=editorial_decision_error(value,quotes)
                if reason:raise ValueError(reason)
                if changes_operational_meaning(value,quotes):
                    raise ValueError('Unsupported operational assertion')
                if _PROPOSAL_ASSERTION.search(value) and not _EXPLICIT_PROPOSAL_SOURCE.search(quotes):
                    raise ValueError('Unsupported proposal')
                if set(_NUMBER.findall(value))-set(_NUMBER.findall(quotes)) or _amount_keys(value)-_amount_keys(quotes):
                    raise ValueError('Unsupported quantity')
            key=tuple(texts['title_'+lang].casefold() for lang in langs)
            if key in seen:raise ValueError('Duplicate theme title')
            seen.add(key);covered.update(ids)
            themes.append({'sources':refs,**texts})
        except ValueError as exc:
            affected=ids if valid_ids(ids) else list(byid)
            failed.update(affected)
            rejections.append({'source_ids':list(affected),'reason':str(exc)})
    missing=(set(byid)-covered)|failed|review
    return {'themes':sorted(themes,key=lambda t:t['sources'][0]['source_id']),
        'gaps':[byid[i] for i in sorted(missing)],'review_ids':sorted(review),
        'rejections':rejections,'review_required':True,
        'verification':'original_row_citation_not_semantic'}
