"""Compare prose alone, using already-paid translations and fixed source groups."""
import argparse
import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_prelocalized_prose import prepare,compose

VERSION='0.40.18'
DIGEST='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90'
# Exact IDs from the earlier source_first bilingual run, not inferred grouping.
GROUPS={'g1':[1,2,7,8],'g2':[4,5]}
CHECKLIST={
    'g1':['families visiting the community center for the first time',
        'entrance instructions distinguish ramp from stairs','location of accessible restrooms',
        'discussion of examples of respectful service for people unfamiliar with available services',
        'translated sign differs from an individual conversation with a visitor'],
    'g2':['public building map versus individual private data',
        'volunteer handbook refers a question to reception without disclosing private contact details']}
def load_groups(evidence):
    src=json.loads(evidence.read_text(encoding='utf-8'))['source_first']
    result={}
    for lang in ('es','en'):
        saved=next(r for r in src if r['language']==lang)
        result[lang]=[]
        for gid,ids in GROUPS.items():
            units=[]
            for sid in ids:
                found=[u for u in saved['units'] if u['source']['source_id']==sid]
                assert len(found)==1
                units.append(found[0])
            result[lang].append({'id':gid,'units':units})
        prepare(result[lang],lang)
    for a,b in zip(result['es'],result['en']):
        assert [u['source'] for u in a['units']]==[u['source'] for u in b['units']]
    return result
def main(evidence,output,preflight):
    groups=load_groups(evidence)
    if preflight:
        print('Verified six exact source units and saved localizations in each language.',flush=True);return 0
    from engine import ollama
    output.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    save('expected.json',{'groups':groups,'independent_checklist':CHECKLIST})
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    trace=[];results={};start=time.monotonic()
    for lang in ('es','en'):
        def request(messages,schema):
            t=time.monotonic()
            entry={'language':lang,'messages':messages,'schema':schema};trace.append(entry)
            try:
                entry['raw']=ollama.chat(messages,model=ollama.MODEL,json_output=schema,
                    think=False,cpu_only=True,timeout=240)
                return entry['raw']
            except Exception as exc:
                entry['error']=str(exc);raise
            finally:
                entry['seconds']=round(time.monotonic()-t,3);save('trace.json',trace)
        results[lang]=compose(groups[lang],lang,request)
        save('evidence.json',results)
        lines=[]
        for group in results[lang]['groups']:
            lines+=['## '+group['id'],'','BASELINE: '+group['baseline'],'',
                'CANDIDATE: '+(group['candidate'] or '[fallback]'),'']
        (output/(lang+'.md')).write_text('\n'.join(lines),encoding='utf-8')
    checks={'at_most_two_requests':len(trace)==2,'all_groups_have_candidates':all(
        g['candidate'] for r in results.values() for g in r['groups'])}
    r={'checks':checks,'passed':all(checks.values()),'requests':len(trace),
        'seconds':round(time.monotonic()-start,3),'scope':'fixed groups, prior translations; lexical gates only; editorial acceptance requires independent review'}
    save('result.json',r);print(json.dumps(r),flush=True)
    return 0 if r['passed'] else 2
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--preflight',action='store_true');a=p.parse_args()
    raise SystemExit(main(a.evidence,a.output,a.preflight))
