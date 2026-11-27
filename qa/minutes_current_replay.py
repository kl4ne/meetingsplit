"""Offline replay of exact archived model responses against current source.

Never call Ollama. Strict replay stops on a missing request; separate
stage revalidation uses original request/source identity and explicitly
reports differences. Neither is fresh inference or semantic acceptance.
"""
import argparse
import collections
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import summarize,ollama
from engine.minutes_evidence import (source_blocks,validate_items,explicit_source_items,
    reconcile_source_items,find_coverage_gaps,repeated_topic_coverage,render_minutes)
from engine.minutes_brief import editorial_input,validate_editorial,omitted_editorial_sources
from engine.minutes_localization import prepare_presentation,apply_translations,translation_request
from engine.minutes_theme_presentation import compact_repeated_theme_sources,separate_structured_themes
from engine.minutes_overview import build_overview
from engine.minutes_source_accounting import audit_source_passages
from qa.minutes_varied_long import fixture,score
from qa.minutes_editorial_ab import TRANSCRIPT,RUBRIC

def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def events(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]

def pairs(events):
    pending={}
    result=[]
    for e in events:
        if e.get('arm') not in (None,'pipeline') or 'stage' not in e:
            continue
        key=(e['stage'],json.dumps(e.get('scope'),sort_keys=True))
        if e['event']=='request':
            pending[key]=e
        elif e['event']=='response':
            req=pending.pop(key)
            result.append((req,e))
        elif e['event'] in ('request_error','error'):
            pending.pop(key,None)
    return result

class MissingArchivedRequest(AssertionError):
    pass

def strict(transcript,archived,output):
    output.mkdir()
    outcomes={}
    for mode in ('both','summary','minutes'):
        calls=[];trace=[];evidence={}
        # Each mode has its own replay pool. Never substitute a similar prompt.
        remaining=list(archived)
        def reply(messages,model,**kw):
            req=trace[-1]
            assert req['event']=='request' and req['model']==model==ollama.MODEL
            assert messages==req['messages'] and kw['json_output']==req['schema']
            candidates=[(i,p) for i,p in enumerate(remaining)
                if p[0]['stage']==req['stage'] and p[0]['scope']==req['scope']
                and p[0]['messages']==messages and p[0]['schema']==kw['json_output']
                and p[0].get('cpu_only',False)==kw.get('cpu_only',False)]
            if len(candidates)!=1:
                calls.append({'stage':req['stage'],'scope':req['scope'],'matched':False})
                raise MissingArchivedRequest('No unique exact archived request')
            i,(_,response)=candidates[0]
            remaining.pop(i)
            calls.append({'stage':req['stage'],'scope':req['scope'],'matched':True})
            return response['raw']
        try:
            with patch.object(summarize,'ollama_chat',reply),patch.object(ollama,'chat',side_effect=AssertionError('Network prohibited')):
                report=summarize.summarize_local(transcript,mode,'es',ollama.MODEL,
                    narrative_strategy='localized_editorial',qa_trace=trace.append,evidence_sink=evidence.update)
            (output/(mode+'.md')).write_text(report,encoding='utf-8')
            dump(output/(mode+'-evidence.json'),evidence)
            outcomes[mode]={'completed':True,'uncited':len(evidence['source_accounting']['uncited_passages']),
                'editorial_gaps':len(evidence['editorial_gaps']),
                'review_records':sum(i['category']=='review' for i in evidence['items']),
                'localization_rejected':sum(len(x['rejected']) for x in evidence['localization'])}
        except MissingArchivedRequest:
            outcomes[mode]={'completed':False,'reason':'current request differs from archive; no substitution'}
        outcomes[mode]['calls']=calls
        dump(output/(mode+'-requests.json'),calls)
    return outcomes

def refkey(ref):
    return ref['source_id'],ref['quote']

def varied_revalidate(transcript,original,targeted,output):
    """Stage revalidation, not exact execution of the current orchestrator."""
    output.mkdir()
    expected,checks,topics=fixture()
    assert transcript==expected
    blocks=list(source_blocks(transcript));rows=[r for b in blocks for r in b];byid={r['id']:r for r in rows}
    extracted=[];seen=set();empty=[]
    for n,block in enumerate(blocks,1):
        req,res=[p for p in original if p[0]['stage']=='extraction' and p[0]['scope']['block']==n][-1]
        assert json.loads(req['messages'][1]['content'])['source_rows']==block
        result=validate_items(res['raw'],block,'es',source_only_on_mismatch=req['scope']['attempt']>1)
        if not result:empty.append(n)
        for item in result:
            key=json.dumps(item,sort_keys=True,ensure_ascii=False)
            if key not in seen:seen.add(key);extracted.append(item)
    explicit=explicit_source_items(rows,'es');items=reconcile_source_items(extracted,explicit)
    sections=list(editorial_input(blocks,items,explicit_items=explicit))
    allowed={refkey(r) for section in sections for r in section}
    themes=[];rejected=[];skipped=[];accepted_keys=set()
    for req,res in original+targeted:
        if req['stage'] not in ('editorial','editorial_retry','editorial_omission_retry'):continue
        sources=[{'source_id':r['id'],'timestamp':byid[r['id']]['timestamp'],'quote':r['quote']}
                 for r in json.loads(req['messages'][1]['content'])['sources']]
        assert all(r['quote'] in byid[r['source_id']]['text'] or all(
            part in byid[r['source_id']]['text'] for part in r['quote'].splitlines()) for r in sources)
        bad=[];reasons=[]
        if json.loads(res['raw'])=={'themes':[]}:continue
        good=validate_editorial(res['raw'],sources,'es',rejected=bad,
            on_rejection=lambda theme,exc:reasons.append({'theme':theme,'reason':str(exc)}))
        rejected.extend(reasons)
        for t in good:
            if any(refkey(r) not in allowed for r in t['sources']):
                skipped.append(t);continue
            key=json.dumps(t,sort_keys=True,ensure_ascii=False)
            if key not in accepted_keys:accepted_keys.add(key);themes.append(t)
    themes.sort(key=lambda t:t['sources'][0]['source_id'])
    gaps=omitted_editorial_sources([r for section in sections for r in section],themes)
    # Reuse individual translation text only for matching complete structured identity.
    # A different batch/index is NOT an exact request replay; revalidate it explicitly.
    def identity(record):
        return tuple(record[k] for k in ('category','source','owner','due'))
    recorded=collections.defaultdict(list)
    for req,res in original+targeted:
        if req['stage']!='localization':continue
        recs={r['id']:r for r in json.loads(req['messages'][1]['content'])['records']}
        for r in json.loads(res['raw'])['translations']:
            recorded[identity(recs[r['id']])].append(r['text'])
    presented,todo=prepare_presentation(items,'es')
    good=[];bad=[];corrections=[]
    for i in todo:
        _,schema=translation_request(presented,[i],'es')
        messages,_=translation_request(presented,[i],'es')
        record=json.loads(messages[1]['content'])['records'][0]
        candidates=list(dict.fromkeys(recorded.get(identity(record),[])))
        problems=[]
        for value in reversed(candidates):
            a,b=apply_translations(json.dumps({'translations':[{'id':i,'text':value}]}),
                presented,[i],'es',protected_weekdays=True,corrections=corrections)
            if a:good.extend(a);break
            problems.extend(b)
        else:bad.append({'id':i,'reason':'No accepted archived translation','attempts':problems})
    localization=[{'language':'es','candidate_ids':todo,'accepted':good,'rejected':bad,
                   'protected_weekdays':corrections}]
    repetition=repeated_topic_coverage(blocks,items,themes,empty)
    display,compacted=compact_repeated_theme_sources(blocks,themes)
    display,moved=separate_structured_themes(blocks,display,presented,('es',),localization)
    structural=find_coverage_gaps(rows,items)
    audit=audit_source_passages(blocks,items,themes,gaps)
    evidence={'items':items,'presentation':presented,'editorial_themes':themes,
              'editorial_gaps':gaps,'rejected_archived_themes':rejected,
              'skipped_changed_sources':skipped,'localization':localization,
              'source_accounting':audit,'repetition_coverage':repetition,
              'structured_moves':moved,'coverage_gaps':structural}
    dump(output/'evidence.json',evidence)
    for mode in ('both','summary','minutes'):
        report=render_minutes(presented,mode,'es',repetition['unresolved_empty_block_ids'],structural,
            editorial=display,editorial_gaps=gaps,executive_overview={'es':build_overview(
                presented,display,'es',detail_included=mode!='summary')},
            show_timestamps=False,repetition_coverage=repetition,localization=localization,
            repeated_themes=compacted,respect_mode=True,uncited_passages=audit['uncited_passages'])
        (output/(mode+'.md')).write_text(report,encoding='utf-8')
    return {'facts':score(transcript,checks,items),'themes':len(themes),'archived_theme_rejections':len(rejected),
            'changed_source_themes_skipped':len(skipped),'editorial_gap_ids':[r['source_id'] for r in gaps],
            'uncited_ids':[r['source_id'] for r in audit['uncited_passages']],
            'localization_rejected':bad,'source_statuses':dict(collections.Counter(
                e['status'] for e in audit['entries']))}

def main(short,varied,targeted,output):
    output.mkdir(parents=True,exist_ok=False)
    st=(short/'transcript.txt').read_text(encoding='utf-8')
    vt=(varied/'transcript.txt').read_text(encoding='utf-8')
    assert st==TRANSCRIPT
    s=pairs(events(short/'trace.jsonl'));v=pairs(events(varied/'trace.jsonl'))
    t=pairs(events(targeted/'varied-targeted'/'targeted-trace.jsonl'))
    (output/'short-reference.md').write_text((short/'reference.md').read_text(encoding='utf-8'),encoding='utf-8')
    dump(output/'short-rubric.json',RUBRIC)
    result={'scope':'offline strict replay or stage revalidation only; no semantic acceptance',
            'short_strict':strict(st,s,output/'short'),
            'varied_strict':strict(vt,v+t,output/'varied-strict'),
            'varied_stage_revalidation':varied_revalidate(vt,v,t,output/'varied-revalidated')}
    dump(output/'result.json',result)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('short','varied','targeted','output'):p.add_argument(name,type=Path)
    a=p.parse_args();main(a.short,a.varied,a.targeted,a.output)
