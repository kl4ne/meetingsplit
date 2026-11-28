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

def _other_topic_titles(themes, chosen, lang):
    """Bound the inventory of unsampled titles; never claim it is a synthesis."""
    titles=[];seen=set()
    for theme in themes:
        if theme['summary_'+lang].strip() in chosen:
            continue
        title=theme['title_'+lang].strip()
        key=title.casefold()
        if title and key not in seen:
            seen.add(key);titles.append(title)
    selected=_sample(titles,12)
    while len('; '.join(selected))>900 and len(selected)>1:
        selected=_sample(titles,len(selected)-1)
    if selected and len('; '.join(selected))>900:
        selected=[]
    return selected,len(titles)


def build_compact_combined_overview(items,themes,lang):
    """Navigation digest for combined reports, not an independent synthesis.

    No new factual prose, no duplicate paragraphs or outcome quotations.
    The caller must retain the complete detail and outcome/review sections.
    Counts describe records, not unique real-world events or completeness.
    """
    labels={
        'es':('Panorama de los temas tratados (selección de títulos, no una síntesis independiente)',
              'Se muestran {shown} de {total} títulos distintos; el detalle conserva todos los temas presentados.',
              'Registros por categoría','Consulta las secciones correspondientes para su contenido y citas.',
              ('acuerdos','tareas','avisos','pendientes','propuestas','desacuerdos','información financiera')),
        'en':('Overview of topics discussed (selected titles, not an independent synthesis)',
              'Showing {shown} of {total} distinct titles; the detail retains all presented topics.',
              'Records by category','See the corresponding sections for their content and quotations.',
              ('decisions','tasks','announcements','pending items','proposals','disagreements','financial information'))
    }[lang]
    intro,count_label,category_label,detail_label,category_names=labels
    titles=[];seen=set()
    for t in themes:
        value=t['title_'+lang].strip()
        key=value.casefold().rstrip('.!?')
        if key and key not in seen:
            seen.add(key);titles.append(value.rstrip('.'))
    selected=_sample(titles,5)
    while selected and len('; '.join(selected))>360:
        if len(selected)==1:
            selected=[];break
        selected=_sample(titles,len(selected)-1)
    paragraphs=[]
    if titles:
        if selected:paragraphs.append(intro+': '+'; '.join(selected)+'.')
        paragraphs.append(count_label.format(shown=len(selected),total=len(titles)))
    counts=[]
    for category,label in zip(('decision','action','notice','pending','proposal','disagreement','topic'),category_names):
        n=sum(i['category']==category and (category!='topic' or any(_AMOUNT.search(r['quote']) for r in i['sources'])) for i in items)
        if n:counts.append(f'{label}: {n}')
    if counts:paragraphs.append(category_label+': '+'; '.join(counts)+'. '+detail_label)
    return paragraphs

def build_overview(items, themes, lang, *, detail_included=True, compact_combined=False):
    if compact_combined and detail_included:
        return build_compact_combined_overview(items,themes,lang)
    loc=_LOCALES[lang]
    labels={
        'es':{'more':'Los demás temas se desarrollan a continuación.',
              'detail':'Consulta el detalle en la sección correspondiente.',
              'other':'Otros temas identificados (títulos)',
              'other_count':'Se muestran {shown} de {total} títulos adicionales.',
              'source_detail':'El registro de evidencias conserva las síntesis y citas; esta lista no es una síntesis completa.',
              'decision':'Acuerdos registrados','action':'Tareas registradas',
              'notice':'Avisos','pending':'Pendientes','proposal':'Propuestas','disagreement':'Desacuerdos',
              'topic':'Información financiera'},
        'en':{'more':'The remaining topics are detailed below.',
              'detail':'See the corresponding section for details.',
              'other':'Other identified topics (titles)',
              'other_count':'Showing {shown} of {total} additional titles.',
              'source_detail':'The evidence record retains the summaries and quotations; this list is not a complete synthesis.',
              'decision':'Recorded decisions','action':'Recorded tasks',
              'notice':'Announcements','pending':'Pending items','proposal':'Proposals','disagreement':'Disagreements',
              'topic':'Financial information'},
    }[lang]
    paragraphs=[]
    values=list(dict.fromkeys(t['summary_'+lang].strip() for t in themes))
    chosen=_sample(values,6)
    while len(' '.join(chosen))>1400 and len(chosen)>1:
        chosen=_sample(values,len(chosen)-1)
    if chosen:
        lead=' '.join(v if v.endswith(('.', '!', '?')) else v+'.' for v in chosen)
        if len(chosen)<len(values) and detail_included:
            lead+=' '+labels['more']
        paragraphs.append(lead)
        if len(chosen)<len(values) and not detail_included:
            titles,total=_other_topic_titles(themes,chosen,lang)
            inventory=[]
            if titles:
                inventory.append(labels['other']+': '+'; '.join(titles)+'.')
            if len(titles)<total:
                inventory.append(labels['other_count'].format(shown=len(titles),total=total))
            inventory.append(labels['source_detail'])
            paragraphs.append(' '.join(inventory))
    for category in ('decision','action','notice','pending','proposal','disagreement','topic'):
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
                from .minutes_localization import presentation_due
                due=presentation_due(item,lang)
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
