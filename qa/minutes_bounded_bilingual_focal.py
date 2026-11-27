"""One new mixed-language window from existing synthetic evidence. No full rerun."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_bounded_synthesis import atoms
from engine.minutes_bounded_bilingual import compose_bilingual,render_candidate,bounded_windows

VERSION='0.40.18'
DIGEST='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90'
SOURCES=[
    'The entrance instructions distinguish the ramp from the stairs and describe where the accessible restrooms are located.',
    'Se explicó el uso de etiquetas para distinguir los materiales prestados de los materiales disponibles.',
    'The volunteer handbook explains how to refer a question to reception without disclosing private contact details.',
    'Se habló de revisar la claridad de las instrucciones dirigidas a personas que leen en otro idioma.',
]
# Independent review checklist fixed before inference; not automated entailment.
EXPECTED=[
    ['entrance instructions','ramp vs stairs','location of accessible restrooms'],
    ['use of labels','borrowed vs available materials'],
    ['volunteer handbook','refer a question to reception','no disclosure of private contact details'],
    ['discussion (not proposal/decision)','clarity of instructions','people reading another language'],
]
def main(output):
    output.mkdir(parents=True,exist_ok=False)
    def save(name,x):(output/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
    refs=[{'source_id':i,'timestamp':'00:00:00','quote':s} for i,s in enumerate(SOURCES,1)]
    units,_=atoms(refs)
    assert len(list(bounded_windows(units,('es','en'))))==1
    save('expected.json',{'sources':refs,'clauses':EXPECTED})
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    trace=[];start=time.monotonic()
    def request(messages,schema,**kw):
        t=time.monotonic();entry={**kw,'messages':messages,'schema':schema};trace.append(entry)
        try:
            entry['raw']=ollama.chat(messages,model=ollama.MODEL,json_output=schema,think=False,
                cpu_only=True,timeout=240)
            return entry['raw']
        except Exception as exc:
            entry['error']=str(exc);raise
        finally:
            entry['seconds']=round(time.monotonic()-t,3);save('trace.json',trace)
    result=compose_bilingual(units,'both',request)
    save('evidence.json',result)
    for mode in ('summary','minutes','both'):
        for lang,doc in render_candidate(result,mode).items():
            (output/(mode+'-'+lang+'.md')).write_text(doc,encoding='utf-8')
    checks={'bounded_requests':len(trace)<=2,'both_languages':set(result['reports'])=={'es','en'},
            'all_pairs_rendered':all(not r['source_only'] for r in result['reports'].values()),
            'requires_semantic_review':result['review_required']}
    report={'checks':checks,'passed':all(checks.values()),'seconds':round(time.monotonic()-start,3),
        'requests':len(trace),'scope':'one synthetic mixed window, lexical gates only; independent manual review required',
        'fallbacks':{l:len(r['source_only']) for l,r in result['reports'].items()}}
    save('result.json',report);print(json.dumps(report),flush=True)
    return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1])))
