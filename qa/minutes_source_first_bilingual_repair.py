"""Replay completed bilingual evidence; repair only unresolved structured translation.

The original raw source-first grouping is reused by exact unit identity.
A group whose membership changes receives a neutral QA fallback title; it
is explicitly flagged for editorial review, not certified as a valid plan.
"""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_source_first import source_units,compose_groups
from engine.minutes_localization import apply_translations,translation_request
from engine.minutes_evidence import source_blocks,render_minutes,find_coverage_gaps
from engine.minutes_overview import build_overview
from qa.minutes_source_first_integrated import fixture,VERSION,DIGEST,score
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main(source,output,live):
    output.mkdir(parents=True,exist_ok=False)
    e=json.loads((source/'evidence.json').read_text(encoding='utf-8'))
    events=[json.loads(l) for l in (source/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    transcript,checks,stamps=fixture();assert (source/'transcript.txt').read_text(encoding='utf-8')==transcript
    blocks=list(source_blocks(transcript));rows=[r for b in blocks for r in b]
    items=e['items'];presentation=[dict(i) for i in e['presentation']]
    assert score(transcript,checks,items)['passed']
    pending=[];localization=[]
    for d in e['localization']:
        lang=d['language'];diag=dict(d,accepted=list(d['accepted']),rejected=[])
        for failure in d['rejected']:
            i=failure['id']
            original=next(r for ev in events if ev['stage']=='localization' and ev['event']=='response' and ev['scope']['language']==lang
                         for r in json.loads(ev['raw'])['translations'] if r['id']==i)
            good,bad=apply_translations(json.dumps({'translations':[original]}),presentation,[i],lang)
            diag['accepted'].extend(good);diag['rejected'].extend(bad)
            if bad:pending.append((lang,i))
        localization.append(diag)
    assert pending==[('en',3)],pending
    # Do not lose any descriptive source when eliminating the duplicate
    # structured proposal. Map through exact source identity, not position.
    narratives={};overview={};changes=[];new_units={}
    for old in e['source_first']:
        lang=old['language']
        fresh=source_units(blocks,items,presentation,lang,localization)
        def key(u):return (u['source']['source_id'],u['source']['quote'])
        prior={key(u):u for u in old['units']}
        assert all(key(u) in prior for u in fresh)
        translated=[dict(prior[key(u)],id=u['id']) for u in fresh]
        assert stamps<={u['source']['timestamp'] for u in translated}
        mapping={prior[key(u)]['id']:u['id'] for u in fresh}
        removed=[u for u in old['units'] if u['id'] not in mapping]
        assert all(u['source']['source_id']==15 for u in removed)
        new_units[lang]=translated
        groups=[]
        for w in old['windows']:
            for g in w['groups']:
                ids=[mapping[i] for i in g['unit_ids'] if i in mapping]
                if not ids:continue
                changed=len(ids)!=len(g['unit_ids'])
                title=('Otros temas tratados' if lang=='es' else 'Other topics discussed') if changed else g['title']
                if changed:changes.append({'language':lang,'old_title':g['title'],'new_title':title,'reason':'QA neutral fallback after removal of duplicated structured event'})
                groups.append({'title':title,'unit_ids':ids,'overview_id':mapping.get(g['overview_id'],ids[0])})
        assert sorted(i for g in groups for i in g['unit_ids'])==[u['id'] for u in translated]
        themes,reps=compose_groups(groups,translated,lang)
        narratives[lang]=[{'title':t['title_'+lang],'text':t['summary_'+lang],'sources':t['sources']} for t in themes]
        overview[lang]=[{'summary_'+lang:r} for r in reps]
    save(output/'plan.json',{'pending':pending,'localization':localization,'grouping_changes':changes,'units':{l:len(u) for l,u in new_units.items()}})
    print(json.dumps({'pending':pending,'units':{l:len(u) for l,u in new_units.items()},'grouping_changes':changes},ensure_ascii=False),flush=True)
    if not live:return 0
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    lang,i=pending[0]
    messages,schema=translation_request(presentation,[i],lang)
    messages[0]['content']+=' A source statement specifying a task on a weekday must use "on" that weekday, not "by" or "before". Keep the explicit commitment.'
    started=time.monotonic()
    raw=ollama.chat(messages,think=False,json_output=schema)
    save(output/'trace.json',{'messages':messages,'schema':schema,'raw':raw})
    good,bad=apply_translations(raw,presentation,[i],lang)
    diag=next(d for d in localization if d['language']==lang);diag['accepted'].extend(good);diag['rejected']=bad
    report=render_minutes(presentation,'both','both',[],find_coverage_gaps(rows,items),
        narratives=narratives,narrative_fallbacks=[{'language':c['language'],'theme_ids':[]} for c in changes],
        executive_overview={l:build_overview(presentation,t,l) for l,t in overview.items()},
        show_timestamps=False,repetition_coverage=e['repetition_coverage'],localization=localization)
    (output/'minutes.md').write_text(report,encoding='utf-8')
    save(output/'presentation.json',presentation)
    result={'passed':not bad,'all_structured_facts':True,'all_descriptive_rows':True,
      'localization':localization,'grouping_changes':changes,'seconds':round(time.monotonic()-started,3),
      'requests':1,'scope':'hybrid exact replay + one translation, grouping fallback remains explicit; not full production acceptance'}
    save(output/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main(*(Path(x) for x in sys.argv[1:3]),live='--live' in sys.argv[3:]))
