"""Bounded executive overview from validated text without new inference.

The detailed thematic record and evidence remain authoritative. This is a
deterministic extractive brief, not proof of semantic fidelity or ranking.
"""
from .minutes_evidence import _presentation_text, _LOCALES, _AMOUNT

def _sample(values, maximum):
    if len(values)<=maximum:
        return values
    if maximum==1:
        return values[:1]
    return [values[round(i*(len(values)-1)/(maximum-1))] for i in range(maximum)]

def build_overview(items, themes, lang):
    loc=_LOCALES[lang]
    labels={
        'es':{'more':'Los demás temas se desarrollan a continuación.',
              'detail':'Consulta el detalle en la sección correspondiente.',
              'decision':'Acuerdos registrados','action':'Tareas registradas',
              'notice':'Avisos','pending':'Pendientes','proposal':'Propuestas',
              'topic':'Información financiera'},
        'en':{'more':'The remaining topics are detailed below.',
              'detail':'See the corresponding section for details.',
              'decision':'Recorded decisions','action':'Recorded tasks',
              'notice':'Announcements','pending':'Pending items','proposal':'Proposals',
              'topic':'Financial information'},
    }[lang]
    paragraphs=[]
    values=list(dict.fromkeys(t['summary_'+lang].strip() for t in themes))
    chosen=_sample(values,6)
    while len(' '.join(chosen))>1400 and len(chosen)>1:
        chosen=_sample(values,len(chosen)-1)
    if chosen:
        lead=' '.join(v if v.endswith(('.', '!', '?')) else v+'.' for v in chosen)
        if len(chosen)<len(values):
            lead+=' '+labels['more']
        paragraphs.append(lead)
    for category in ('decision','action','notice','pending','proposal','topic'):
        records=sorted((i for i in items if i['category']==category and
                 (category!='topic' or any(_AMOUNT.search(r['quote']) for r in i['sources']))),
                 key=lambda i:min(r['source_id'] for r in i['sources']))
        if not records:
            continue
        descriptions=[]
        for item in records:
            value=_presentation_text(item,lang).strip()
            if value==loc['source_only'] or 'consulta la cita original' in value or 'see the source quotation' in value:
                continue
            if category=='action':
                fields=[]
                if item.get('owner') and item['owner'].casefold() not in value.casefold():
                    fields.append(loc['owner']+': '+item['owner'])
                from .minutes_localization import local_day
                due=local_day(item.get('due'),lang)
                if due and due.casefold() not in value.casefold():
                    fields.append(loc['due']+': '+due)
                if fields:
                    value=value.rstrip('.')+' ('+'; '.join(fields)+')'
            if value not in descriptions:
                descriptions.append(value)
        # Preserve all outcomes of a short list. Bound longer lists and sample
        # chronologically; the full detailed record is always retained.
        chosen=_sample(descriptions,5)
        while len(' '.join(chosen))>1100 and len(chosen)>1:
            chosen=_sample(descriptions,len(chosen)-1)
        if chosen:
            text=labels[category]+': '+ ' '.join(v if v.endswith(('.', '!', '?')) else v+'.' for v in chosen)
            if len(chosen)<len(records):
                text+=' '+labels['detail']
        else:
            text=labels[category]+': '+labels['detail']
        paragraphs.append(text)
    return paragraphs


def build_source_first_overview(items,composed,lang,mode):
    """Bounded, extractive and explicit: no further model rewrite.

    Mention each group heading when space permits; include representative
    source statements and verified outcomes. In summary mode the renderer
    retains the full structured sections, so do not repeat their text here.
    """
    titles=list(dict.fromkeys(t['title_'+lang].strip() for t in composed['themes']))
    representatives=list(dict.fromkeys(x.strip() for x in composed['representatives']))
    paragraphs=[]
    chosen=[]
    for title in titles:
        if len('; '.join(chosen+[title]))>850:
            break
        chosen.append(title)
    if chosen:
        intro=('Temas principales: ' if lang=='es' else 'Main subjects: ')+'; '.join(chosen)+'.'
        if len(chosen)<len(titles):
            intro+=(' Otros temas constan en las evidencias.' if lang=='es' else ' Further topics are recorded in the evidence.')
        paragraphs.append(intro)
    selected=_sample(representatives,4)
    while len(' '.join(selected))>1000 and len(selected)>1:
        selected=_sample(selected,len(selected)-1)
    if selected:
        paragraphs.append(' '.join(v if v.endswith(('.', '!', '?')) else v+'.' for v in selected))
    if mode=='both':
        paragraphs.extend(build_overview(items,[],lang))
    return paragraphs
