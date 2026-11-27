"""Exact-response reconstruction of the varied synthetic case; targeted repair only.

Not an end-to-end fresh inference. Revalidate recorded successful extraction
responses, preserve valid themes, and call the same model only for omitted
excerpts or localization still unresolved. Never reads real meetings.
"""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import (source_blocks,validate_items,explicit_source_items,
    reconcile_source_items,find_coverage_gaps,repeated_topic_coverage,render_minutes)
from engine.minutes_brief import (editorial_input,validate_editorial,omitted_editorial_sources,
    repair_editorial_omissions)
from engine.minutes_localization import (prepare_presentation,apply_translations,translation_request)
from engine.minutes_theme_presentation import compact_repeated_theme_sources,separate_structured_themes
from engine.minutes_overview import build_overview
from qa.minutes_varied_long import fixture,score,SECTIONS,VERSION,DIGEST

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def main(original,output,live):
    output.mkdir(parents=True,exist_ok=False)
    transcript,checks,topics=fixture()
    assert (original/'transcript.txt').read_text(encoding='utf-8')==transcript
    old=json.loads((original/'evidence.json').read_text(encoding='utf-8'))
    events=[json.loads(l) for l in (original/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    blocks=list(source_blocks(transcript));rows=[r for b in blocks for r in b]
    extracted=[];seen=set();empty=[]
    # The original run completed extraction after its normal retry policy.
    # Reuse only each block's final successful raw reply and validate it again.
    for n,block in enumerate(blocks,1):
        replies=[e for e in events if e['stage']=='extraction' and e['event']=='response' and e['scope']['block']==n]
        assert replies
        reply=replies[-1]
        req=next(e for e in events if e['stage']=='extraction' and e['event']=='request' and e['scope']==reply['scope'])
        assert json.loads(req['messages'][1]['content'])['source_rows']==block
        items=validate_items(reply['raw'],block,'es',source_only_on_mismatch=reply['scope']['attempt']>1)
        if not items:empty.append(n)
        for item in items:
            key=(item['category'],tuple((r['source_id'],r['quote']) for r in item['sources']),
                 item['owner'],item['due'],item.get('text_es'),item.get('text_en'))
            if key not in seen:
                seen.add(key);extracted.append(item)
    explicit=explicit_source_items(rows,'es')
    items=reconcile_source_items(extracted,explicit)
    facts=score(transcript,checks,items)
    def ids(item):return {r['source_id'] for r in item['sources']}
    checks_pre={'all_expected_facts':facts['passed'],
                'no_false_pending_example':not any(i['category']=='pending' and 67 in ids(i) for i in items),
                'no_false_teaching_proposal':not any(i['category']=='proposal' and 36 in ids(i) for i in items),
                'no_unresolved_review':not any(i['category']=='review' for i in items)}
    save(output/'extraction-replay.json',{'checks':checks_pre,'facts':facts,'items':items})
    # Revalidate raw editorial replies against their original exact input,
    # then retain only themes whose entire references still belong to the
    # newly computed input section. No cross-section reassignment.
    replies=[e for e in events if e['stage']=='editorial' and e['event']=='response']
    sections=list(editorial_input(blocks,items,explicit_items=explicit))
    assert len(sections)==len(replies)
    row_by_id={r['id']:r for r in rows}
    def key(r):return r['source_id'],r['quote']
    plans=[]
    for section,reply in zip(sections,replies):
        req=next(e for e in events if e['stage']=='editorial' and e['event']=='request' and e['scope']==reply['scope'])
        orig=[{'source_id':r['id'],'timestamp':row_by_id[r['id']]['timestamp'],'quote':r['quote']}
              for r in json.loads(req['messages'][1]['content'])['sources']]
        rejected=[]
        accepted=validate_editorial(reply['raw'],orig,'es',rejected=rejected)
        assert not rejected
        allowed={key(r) for r in section}
        kept=[t for t in accepted if all(key(r) in allowed for r in t['sources'])]
        omitted=omitted_editorial_sources(section,kept)
        plans.append({'section':section,'kept':kept,'omitted':omitted})
    # Reuse recorded translations by exact source, category, owner and due,
    # not by mutable item index. Previously rejected responses must pass
    # the new validator before reuse; do not silently accept a change.
    def identity(i):
        return (i['category'],i['owner'],i['due'],tuple((r['source_id'],r['quote']) for r in i['sources']))
    recorded={}
    for e in events:
        if e['stage']=='localization' and e['event']=='response':
            for r in json.loads(e['raw'])['translations']:
                recorded[identity(old['items'][r['id']])]=r['text']
    presented,todo=prepare_presentation(items,'es')
    accepted=[];pending=[];corrections=[]
    for i in todo:
        raw=recorded.get(identity(items[i]))
        if raw is not None:
            good,bad=apply_translations(json.dumps({'translations':[{'id':i,'text':raw}]}),presented,[i],'es',
                                         protected_weekdays=True,corrections=corrections)
            accepted.extend(good)
            if good:continue
        pending.append(i)
    save(output/'plan.json',{'checks':checks_pre,'sections':plans,'reused_localization':accepted,
                             'pending_localization':pending,'pending_sources':[items[i]['sources'] for i in pending],
                             'mode':'exact-response replay; no fresh inference yet'})
    print(json.dumps({'checks':checks_pre,'omitted_ids':[[r['source_id'] for r in p['omitted']] for p in plans],
                      'reused_localization':accepted,'pending_localization':pending},ensure_ascii=False),flush=True)
    if not all(checks_pre.values()):return 2
    if not live:return 0
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    guide=(ROOT/'docs'/'Guia_Owll_y_Minutas_para_Ollama.md').read_text(encoding='utf-8')
    calls=[];started=time.monotonic()
    def trace(stage,event,scope,**details):
        with (output/'targeted-trace.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'stage':stage,'event':event,'scope':scope,**details},ensure_ascii=False)+'\n')
    def request(messages,schema,*,stage,scope):
        if stage=='editorial_omission_retry':
            messages=[dict(messages[0],content=messages[0]['content']+
                       '\n\nGuía editorial. Mantén el esquema JSON solicitado; aplica la guía a las descripciones.\n'+
                       guide+'\n\nPara esta etapa, sigue el encargo y el esquema específicos del comienzo.'),*messages[1:]]
        calls.append(stage);trace(stage,'request',scope,messages=messages,schema=schema)
        start=time.monotonic()
        try:
            raw=ollama.chat(messages,json_output=schema)
            trace(stage,'response',scope,raw=raw,seconds=time.monotonic()-start)
            return raw
        except Exception as exc:
            trace(stage,'error',scope,reason=str(exc),error_type=type(exc).__name__)
            raise
    themes=[];gaps=[]
    for plan in plans:
        kept,unresolved,_=repair_editorial_omissions(plan['section'],plan['kept'],[],'es',request,trace=trace)
        themes.extend(kept);gaps.extend(unresolved)
    rejected=[]
    for start in range(0,len(pending),5):
        batch=pending[start:start+5];messages,schema=translation_request(presented,batch,'es')
        try:
            raw=request(messages,schema,stage='localization',scope={'language':'es','item_indices':batch})
            good,bad=apply_translations(raw,presented,batch,'es',protected_weekdays=True,corrections=corrections)
            accepted.extend(good);rejected.extend(bad)
        except (OSError,RuntimeError,ValueError) as exc:
            rejected.extend({'id':i,'reason':str(exc)} for i in batch)
    localization=[{'language':'es','candidate_ids':todo,'accepted':accepted,'rejected':rejected,'protected_weekdays':corrections}]
    assert all({k:v for k,v in a.items() if k!='text_es'}=={k:v for k,v in b.items() if k!='text_es'} for a,b in zip(items,presented))
    repeated=repeated_topic_coverage(blocks,items,themes,empty)
    display,compacted=compact_repeated_theme_sources(blocks,themes)
    display,moved=separate_structured_themes(blocks,display,presented,('es',),localization)
    structural=find_coverage_gaps(rows,items)
    report=render_minutes(presented,'both','es',repeated['unresolved_empty_block_ids'],structural,
         editorial=display,editorial_gaps=gaps,executive_overview={'es':build_overview(presented,display,'es')},
         show_timestamps=False,repetition_coverage=repeated,localization=localization,repeated_themes=compacted)
    cited={r['timestamp'] for t in themes for r in t['sources']}
    section_results=[{'section':s['name'],'cited_rows':sum(t['stamp'] in cited for t in topics if t['section']==s['name']),
                      'total_rows':len(s['lines'])} for s in SECTIONS]
    criteria={**checks_pre,'all_nine_sections':all(s['cited_rows']>0 for s in section_results),
              'no_detected_structural_gaps':not structural,'no_uncited_editorial_excerpts':not gaps,
              'no_failed_localization':not rejected}
    (output/'minutes.md').write_text(report,encoding='utf-8')
    save(output/'evidence.json',{'items':items,'presentation':presented,'editorial_themes':themes,'editorial_gaps':gaps,
                                'localization':localization,'repetition_coverage':repeated,'structured_moves':moved})
    result={'scope':'revalidated recorded extraction and synthesis plus targeted real inference; not a fresh full pipeline',
            'checks':criteria,'sections':section_results,'facts':facts,'requests':calls,
            'seconds':round(time.monotonic()-started,3),'passed':all(criteria.values()),'quality':'manual semantic review required'}
    save(output/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='facts'},ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('original',type=Path);p.add_argument('output',type=Path);p.add_argument('--live',action='store_true')
    a=p.parse_args();raise SystemExit(main(a.original,a.output,a.live))
