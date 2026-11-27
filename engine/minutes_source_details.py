"""Bounded source-backed detail for explicitly selected review passages.

No grouping, paraphrase or extraction. Same-language sentences remain
literal; translation candidates retain their exact original references.
This is not a semantic verifier or a default desktop strategy.
"""
import re
from .control import JobCancelled
from .minutes_evidence import _SENTENCE_BREAK
from .minutes_localization import _language,translation_request,apply_translations
from .minutes_brief import _PROPOSAL_ASSERTION,_EXPLICIT_PROPOSAL_SOURCE
import json

MAX_SENTENCES=5
MAX_BYTES=4500
_NEGATIVE=re.compile(r'\b(?:not|never|without|no|nunca|sin|ningún|ninguna|ninguno)\b',re.I)

def prepare_details(refs,lang):
    if lang not in ('es','en'):
        raise ValueError('One target language required')
    records=[];seen=set()
    for ref in refs:
        for part in _SENTENCE_BREAK.split(ref['quote']):
            quote=part.strip()
            if not quote:continue
            key=(ref['source_id'],ref['timestamp'],quote)
            if key in seen:continue
            seen.add(key)
            src={**ref,'quote':quote}
            records.append({'category':'topic','owner':None,'due':None,
                'sources':[src],'text_'+lang:quote,
                'status':'literal_source' if _language(quote,lang) else 'source_only'})
    return records

def compose_details(refs,lang,request,*,cancel=None):
    records=prepare_details(refs,lang)
    pending=[i for i,r in enumerate(records) if r['status']=='source_only']
    calls=0;rejected=[]
    if pending:
        msgs,schema=translation_request(records,pending,lang)
        if len(pending)>MAX_SENTENCES or len(msgs[1]['content'].encode('utf-8'))>MAX_BYTES:
            rejected=[{'id':i,'reason':'translation budget exceeded'} for i in pending]
        else:
            if cancel:cancel.check()
            calls+=1
            try:
                raw=request(msgs,schema)
                translated=[dict(r) for r in records]
                accepted,bad=apply_translations(raw,translated,pending,lang)
                rejected.extend(bad)
                for i in accepted:
                    original=records[i]['sources'][0]['quote']
                    candidate=translated[i]['text_'+lang]
                    if (bool(_NEGATIVE.search(original))!=bool(_NEGATIVE.search(candidate))
                        or (_PROPOSAL_ASSERTION.search(candidate)
                            and not _EXPLICIT_PROPOSAL_SOURCE.search(original))):
                        rejected.append({'id':i,'reason':'translation changed negation or proposal modality'})
                        continue
                    records[i]['text_'+lang]=candidate
                    records[i]['status']='translation_candidate_review_required'
            except JobCancelled:raise
            except (ValueError,RuntimeError,OSError) as exc:
                rejected.extend({'id':i,'reason':str(exc)} for i in pending)
    if cancel:cancel.check()
    return {'language':lang,'records':records,'requests':calls,'rejected':rejected,
            'review_required':True,'verification':'literal_source_or_translation_candidate_not_semantic'}

def detail_markdown(result):
    """Review-only output: keep originals attributable; no fabricated headings."""
    lang=result['language'];es=lang=='es'
    lines=['## Detalles de fuente para revisión' if es else '## Source details for review','']
    for r in result['records']:
        original=r['sources'][0]['quote']
        candidate=r['text_'+lang]
        from .minutes_evidence import _markdown
        if r['status']=='literal_source':
            lines.append('- '+_markdown(original))
        elif r['status']=='translation_candidate_review_required':
            lines.append('- '+_markdown(candidate))
            lines.append('  - '+('Cita original: ' if es else 'Original quotation: ')+_markdown(original))
        else:
            lines.append('- '+('Sin traducción validada: ' if es else 'No validated translation: ')+_markdown(original))
    return '\n'.join(lines)+'\n'
