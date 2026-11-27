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

# This is a deliberately limited review cue, not a semantic validator.
# Only inspect explicitly delimited multiple clauses in already cited passages.
# Inflection, synonyms and translation can prevent literal matches.
import re
import unicodedata
from .minutes_localization import _language

_COMPOUND_BREAK=re.compile(r'(?<=[.!?])\s+|\n+|;\s*')
_FUNCTION_WORDS=set(('el la los las de del y para por con se una un que en es son al '
    'le les lo su sus como a o e sobre the an of and for with was were that to in on '
    'their is are be this these those it its how from as at by can may will').split())

def _content_tokens(text):
    folded=''.join(c for c in unicodedata.normalize('NFKD',text.casefold())
                   if not unicodedata.combining(c))
    return set(re.findall(r'\b[^\W\d_]+\b',folded))-_FUNCTION_WORDS

def _clauses(text):
    return [s.strip() for s in _COMPOUND_BREAK.split(text) if s.strip()]

def audit_compound_citations(themes,items,language,*,already_visible=()):
    """Flag compound citations whose distinct clauses lack literal support.

    Cross-language clauses cannot be checked by same-language word overlap.
    Keep original quotations for review; never invalidate a theme or claim
    semantic omission based on this heuristic. No extra model requests.
    """
    langs=('es','en') if language=='both' else (language,)
    visible={}
    def add(ref):
        visible.setdefault(ref['source_id'],set()).update(_clauses(ref['quote']))
    for ref in already_visible:add(ref)
    for item in items:
        if item['category']!='topic' or any(_AMOUNT.search(r['quote']) for r in item['sources']):
            for ref in item['sources']:add(ref)
    grouped={}
    for theme in themes:
        for ref in theme['sources']:
            key=(ref['source_id'],ref['timestamp'],ref['quote'])
            entry=grouped.setdefault(key,{'source':ref,'themes':[]})
            entry['themes'].append(theme)
    result={}
    for lang in langs:
        findings=[]
        for entry in grouped.values():
            ref=entry['source'];clauses=_clauses(ref['quote'])
            if len(clauses)<2:continue
            summaries=[t['summary_'+lang] for t in entry['themes']]
            tokens=[_content_tokens(s) for s in summaries]
            problems=[]
            for clause in clauses:
                if clause in visible.get(ref['source_id'],set()):continue
                words=_content_tokens(clause)
                if any(clause.casefold() in s.casefold() for s in summaries):continue
                if _language(clause,'en' if lang=='es' else 'es') and not _language(clause,lang):
                    problems.append({'clause':clause,'reason':'cross_language_unverified'})
                elif _language(clause,lang) and len(words)>=4:
                    best=max(len(words&t)/len(words) for t in tokens)
                    if best<0.4:
                        problems.append({'clause':clause,'reason':'low_literal_overlap',
                                         'overlap':round(best,3)})
            if problems:
                findings.append({'source':ref,'clauses':problems})
        result[lang]=findings
    return result

