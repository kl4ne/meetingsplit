"""Offline consolidation experiment using the exact synthetic A/B artifact.

No inference, downloads of models or real meeting inputs. This is a QA-only
comparison, not a change to production rendering or a semantic acceptance.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import render_minutes, _presentation_text, _markdown, _LOCALES
from engine.minutes_narrative import narrative_sections, validate_narrative, recover_narrative
from qa.minutes_editorial_ab import TRANSCRIPT, RUBRIC, REFERENCE

def overview(items, themes, lang, *, max_topics=6, max_per_category=2):
    """A bounded index of accepted themes plus actual outcome descriptions.

    This deliberately does not generate new factual claims, rank importance,
    or imply that a proposal was approved. All detail remains below.
    """
    loc=_LOCALES[lang]
    labels={
        'es':{'lead':'La reunión abordó','more':'entre otros temas',
              'details':'El detalle se desarrolla en las secciones siguientes.',
              'decision':'Acuerdos registrados','action':'Tareas registradas',
              'notice':'Avisos','pending':'Pendientes','proposal':'Propuestas'},
        'en':{'lead':'The meeting covered','more':'among other topics',
              'details':'Details appear in the sections below.',
              'decision':'Recorded decisions','action':'Recorded tasks',
              'notice':'Announcements','pending':'Pending items','proposal':'Proposals'},
    }[lang]
    titles=list(dict.fromkeys(t['title_'+lang].rstrip('.').strip() for t in themes))
    paragraphs=[]
    if titles:
        selected=titles if len(titles)<=max_topics else titles[:max_topics-1]+titles[-1:]
        intro=labels['lead']+': '+ '; '.join(_markdown(t) for t in selected)
        if len(selected)<len(titles):
            intro+='; '+labels['more']
        paragraphs.append(intro+'.')
    for category in ('decision','action','notice','pending','proposal'):
        records=[i for i in items if i['category']==category]
        if not records:
            continue
        values=[]
        for item in records:
            text=_presentation_text(item,lang)
            if text==loc['source_only'] or text.startswith(('Propuesta sin aprobación confirmada; consulta','Proposal without confirmed approval; see')):
                continue
            value=text.rstrip('.')
            if category=='action':
                suffix=[]
                if item['owner'] and item['owner'].casefold() not in value.casefold():
                    suffix.append(item['owner'])
                if item['due'] and item['due'].casefold() not in value.casefold():
                    suffix.append(item['due'])
                if suffix:
                    value+=' ('+', '.join(suffix)+')'
            if value not in values:
                values.append(value)
        if values:
            selected=values[:max_per_category]
            line='**'+labels[category]+':** '+ '; '.join(_markdown(v) for v in selected)+'.'
            if len(selected)<len(values) or len(values)<len(records):
                line+=' '+labels['details']
        else:
            line='**'+labels[category]+':** '+labels['details']
        paragraphs.append(line)
    return '\n\n'.join(paragraphs)

def render_variant(evidence, *, narratives=None, fallbacks=()):
    return render_minutes(evidence['items'],'both','es',evidence['empty_block_ids'],
                          evidence['coverage_gaps'],editorial=evidence['editorial_themes'],
                          editorial_gaps=evidence['editorial_gaps'],narratives=narratives,
                          narrative_fallbacks=fallbacks,show_timestamps=False)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args()
    if (args.input/'transcript.txt').read_text(encoding='utf-8')!=TRANSCRIPT:
        raise ValueError('Only the exact built-in synthetic short fixture is permitted')
    args.output.mkdir(parents=True,exist_ok=False)
    evidence=json.loads((args.input/'pipeline-evidence.json').read_text(encoding='utf-8'))
    trace=[json.loads(line) for line in (args.input/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    accepted=[e for e in trace if e.get('stage')=='editorial' and e.get('event')=='accepted']
    if [t for e in accepted for t in e['themes']]!=evidence['editorial_themes']:
        raise ValueError('Recorded themes do not match sidecar')
    sections=list(narrative_sections(evidence['editorial_themes'],'es'))
    paragraphs=[];fallbacks=[];results=[]
    for section in sections:
        scope={'language':'es','theme_ids':list(section)}
        events=[e for e in trace if e.get('scope')==scope and e.get('stage') in ('draft','review')]
        requests=[e for e in events if e.get('event')=='request']
        expected={f'E{k}':record for k,(_,record) in section.items()}
        if not requests or any(json.loads(e['messages'][1]['content'])!=expected for e in requests):
            raise ValueError('Replay request does not match exact section')
        replies={e['stage']:e['raw'] for e in events if e.get('event')=='response'}
        try:
            values=validate_narrative(replies.get('review',''),section,'es')
            selection={'review':list(section),'draft':[],'themes':[]}
            reason=None
        except ValueError as exc:
            values,selection=recover_narrative(section,'es',draft=replies.get('draft'),revised=replies.get('review'))
            fallbacks.append(scope);reason=str(exc)
        paragraphs.extend(values)
        results.append({'scope':scope,'selection':selection,'reason':reason})
    baseline=(args.input/'pipeline.md').read_text(encoding='utf-8')
    recovered=render_variant(evidence,narratives={'es':paragraphs},fallbacks=fallbacks)
    # Keep historical warning in this offline alternative; cannot retroactively
    # declare a model run complete by suppressing its failed narrative stage.
    editorial=render_variant(evidence,fallbacks=evidence['narrative_fallbacks'])
    heading='## Resumen ejecutivo\n\n'
    if heading not in editorial:
        raise ValueError('Expected existing summary heading')
    brief=overview(evidence['items'],evidence['editorial_themes'],'es')
    consolidated=editorial.replace(heading,heading+brief+'\n\n## Temas tratados\n\n',1)
    for name,doc in [('historical',baseline),('recovered',recovered),('editorial_only',editorial),
                     ('consolidated',consolidated),('reference',REFERENCE)]:
        (args.output/(name+'.md')).write_text(doc,encoding='utf-8')
    report={'scope':'offline exact synthetic artifact 15179585459; no inference',
            'narrative_replay':results,'original_seconds':819.771,'original_requests':5,
            'quality':'manual review required; no real-model improvement or time saving certified',
            'rubric':RUBRIC}
    (args.output/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
