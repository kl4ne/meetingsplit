"""Controlled Spanish single-window A/B on the frozen fictitious exhibit.
Two calls maximum, no retries, no owner transcript, no full minutes acceptance.
Raw output is synthetic only. Judge both outputs manually using the frozen rubric.
"""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import plan_context
from engine.minutes_context_row_citations import row_request,validate_rows
from engine.minutes_context_interruptions import quarantine_interrupted
from engine.minutes_context_claims import claim_request,validate_claims,recovery_targets
from qa.minutes_context_claims_preflight import TRANSCRIPT,RUBRIC

CALL_CAP=2
PER_CALL=300
WALL_CAP=610
DIGEST='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90'

def main(preflight,out):
    out.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    def load(name):
        return json.loads((preflight/name).read_text(encoding='utf-8'))
    assert TRANSCRIPT==(preflight/'transcript.txt').read_text(encoding='utf-8')
    assert RUBRIC==load('rubric.json')
    assert load('result.json')=={'rows':11,'windows':1,'model_requests':0,
        'scope':'offline mock structural preflight','recovery_target_ids':[7]}
    blocks=list(source_blocks(TRANSCRIPT));rows=[r for b in blocks for r in b]
    items=explicit_source_items(rows,'es');plan=plan_context(blocks,items)
    assert plan==load('plan.json')
    units=plan['windows'][0];messages,schema=claim_request(units,'es')
    assert {'messages':messages,'schema':schema}==load('request.json')
    state=ollama.existing_status()
    assert state['version']=='0.40.18' and state['model']['digest']==DIGEST and ollama.reusable_existing()
    save('rubric.json',RUBRIC);save('items.json',items);save('plan.json',plan)
    (out/'transcript.txt').write_text(TRANSCRIPT,encoding='utf-8')
    byid={r['id']:r for r in rows}
    ids={r['source_id'] for u in units for r in u['sources']}
    calls=[];results={};start=time.monotonic()
    for name in ('row_baseline','claim_candidate'):
        entry={'completed':False,'checks':{}}
        results[name]=entry
        try:
            m,s=(row_request if name=='row_baseline' else claim_request)(units,'es')
            save(name+'-request.json',{'messages':m,'schema':s})
            remaining=WALL_CAP-(time.monotonic()-start)
            assert len(calls)<CALL_CAP and remaining>1
            call={'arm':name,'cpu_only':True};calls.append(call);t=time.monotonic()
            try:
                raw=ollama.chat(m,model=ollama.MODEL,json_output=s,cpu_only=True,
                                timeout=min(PER_CALL,remaining))
                (out/(name+'-raw.json')).write_text(raw,encoding='utf-8')
            finally:
                call['seconds']=round(time.monotonic()-t,3);save('calls.json',calls)
            if name=='row_baseline':
                result=quarantine_interrupted(validate_rows(raw,units,'es'),units,blocks)
            else:
                result=validate_claims(raw,units,'es',blocks=blocks)
            save(name+'-validated.json',result)
            refs=[r for theme in result['themes'] for r in theme['sources']]
            gapids={r['source_id'] for r in result['gaps']}
            covered={r['source_id'] for r in refs}
            allrefs=refs+result['gaps']+[r for item in items for r in item['sources']]
            claimrefs=[r for theme in result['themes'] for claim in theme.get('claims',[]) for r in claim['sources']]
            checks={
                'all_literal':all(r['source_id'] in byid and r['timestamp']==byid[r['source_id']]['timestamp']
                    and r['quote'] in byid[r['source_id']]['text'] for r in allrefs+claimrefs),
                'all_rows_accounted':covered|gapids==ids,
                'interrupted_rows_preserved':{8,9}<=gapids,
                'no_interrupted_rows_in_accepted_themes':not ({8,9}&covered),
                'notice_unchanged':[(i['category'],[r['source_id'] for r in i['sources']]) for i in items]==[('notice',[11])],
                'notice_not_in_themes':11 not in covered,
                'review_required':result['review_required'] is True,
                'has_narrative':bool(result['themes'])
            }
            if name=='claim_candidate':
                checks['each_claim_has_own_refs']=all(t.get('claims') and all(c['sources'] for c in t['claims']) for t in result['themes'])
                entry['recovery_target_ids']=recovery_targets(units,result)
            entry.update(completed=True,checks=checks,themes=len(result['themes']),
                accepted_claims=sum(len(t.get('claims',[])) for t in result['themes']),
                gap_ids=sorted(gapids),rejections=result['rejections'])
        except Exception as exc:
            entry.update(error_type=type(exc).__name__,error=str(exc))
        print(name,json.dumps(entry,ensure_ascii=False),flush=True)
    result={'scope':'frozen fictional single-window Spanish A/B; not end-to-end report',
        'model':ollama.MODEL,'runtime':state['version'],'digest':DIGEST,'requests':len(calls),
        'seconds':round(time.monotonic()-start,3),'call_cap':CALL_CAP,'per_call_cap':PER_CALL,
        'wall_cap':WALL_CAP,'recovery_calls':0,'arms':results,'semantic_acceptance':False,
        'manual_rubric_required':True}
    result['structural_pass']=len(calls)==2 and all(e['completed'] and all(e['checks'].values()) for e in results.values())
    save('result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['structural_pass'] else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
