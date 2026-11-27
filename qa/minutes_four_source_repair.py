"""Four demonstrated defects: literal ES detail plus one bounded EN->ES translation.

The selection and rubric are fixed by manual comparison of existing evidence;
not an automatic semantic detector. Do not modify existing archived themes.
"""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks
from engine.minutes_source_details import compose_details,detail_markdown,prepare_details
from qa.minutes_varied_long import fixture,score

VERSION='0.40.18'
DIGEST='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90'
TARGETS=(2,4,33,63)
CHECKLIST={
    '2':['accessibility information must be available at the counter','distinguish welcome from administrative registration'],
    '4':['visitors needing assistance can use the entrance ramp','discussion of accessible routes','without disclosing private contact information'],
    '33':['discussion, not proposal/decision','examples helping volunteers distinguish frequent questions from exceptional requests'],
    '63':['discussion, not proposal/decision','review clarity of observations received during activities'],
}

def inputs(evidence_path):
    evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
    transcript,checks,_=fixture()
    rows={r['id']:r for b in source_blocks(transcript) for r in b}
    refs=[{'source_id':i,'timestamp':rows[i]['timestamp'],'quote':rows[i]['text']} for i in TARGETS]
    assert {r['source_id'] for r in evidence['editorial_gaps']}=={33,63}
    assert all(any(r in t['sources'] for t in evidence['editorial_themes']) for r in refs[:2])
    assert all(r in evidence['editorial_gaps'] for r in refs[2:])
    facts=score(transcript,checks,evidence['items'])
    assert facts['passed']
    records=prepare_details(refs,'es')
    assert len(records)==5 and sum(r['status']=='source_only' for r in records)==2
    return refs,evidence,facts

def main(evidence_path,output,preflight=False):
    refs,evidence,facts=inputs(evidence_path)
    if preflight:
        print('Exact source and previous gaps checked; 17 structured facts; 3 literal + 2 translation sentences.',flush=True)
        return 0
    from engine import ollama
    output.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    save('expected.json',{'refs':refs,'checklist':CHECKLIST,'facts':facts})
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    trace=[];started=time.monotonic()
    def request(messages,schema):
        e={'messages':messages,'schema':schema};trace.append(e);t=time.monotonic()
        try:
            e['raw']=ollama.chat(messages,model=ollama.MODEL,json_output=schema,think=False,
                cpu_only=True,timeout=240)
            return e['raw']
        except Exception as exc:
            e['error']=str(exc);raise
        finally:
            e['seconds']=round(time.monotonic()-t,3);save('trace.json',trace)
    result=compose_details(refs,'es',request)
    save('details.json',result)
    old=[t for t in evidence['editorial_themes'] if any(r['source_id'] in TARGETS for r in t['sources'])]
    save('prior-affected-themes.json',old)
    lines=['# Focal comparison — not a replacement minute','',
           'The existing accepted themes and original gaps remain unchanged.','']
    for t in old:lines.extend([t['title_es']+': '+t['summary_es'],''])
    lines.append(detail_markdown(result))
    (output/'comparison.md').write_text('\n'.join(lines),encoding='utf-8')
    checks={'one_request':len(trace)==1,'three_literal':sum(r['status']=='literal_source' for r in result['records'])==3,
            'two_translation_candidates':sum(r['status']=='translation_candidate_review_required' for r in result['records'])==2,
            'no_rejected_translation':not result['rejected'],'review_required':result['review_required'],
            'all_seventeen_structured_facts':facts['passed']}
    r={'checks':checks,'passed':all(checks.values()),'requests':len(trace),
       'seconds':round(time.monotonic()-started,3),
       'scope':'manually selected source detail only; not automatic omission detection, professional synthesis or final pipeline acceptance'}
    save('result.json',r);print(json.dumps(r),flush=True)
    return 0 if r['passed'] else 2

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('evidence',type=Path);p.add_argument('output',type=Path);p.add_argument('--preflight',action='store_true')
    a=p.parse_args();raise SystemExit(main(a.evidence,a.output,a.preflight))
