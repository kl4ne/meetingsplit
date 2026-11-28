"""Limited real A/B of editorial context transport, not a complete pipeline."""
import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_brief import editorial_input,editorial_request,validate_editorial,omitted_editorial_sources
from engine.minutes_context_windows import plan_context,compose_context
from engine.minutes_source_accounting import audit_source_passages
from qa.minutes_context_windows_preflight import TRANSCRIPT,RUBRIC

VERSION='0.40.18'
DIGEST='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90'
def main(output):
    output.mkdir(parents=True,exist_ok=False)
    blocks=list(source_blocks(TRANSCRIPT));rows=[r for b in blocks for r in b]
    expected={26:'notice',27:'decision',28:'action',36:'notice'}
    explicit=explicit_source_items(rows,'es')
    structured=[item for item in explicit if all(expected.get(r['source_id'])==item['category'] for r in item['sources'])]
    assert {r['source_id']:i['category'] for i in structured for r in i['sources']}==expected
    old=list(editorial_input(blocks,structured,explicit_items=structured))
    plan=plan_context(blocks,structured)
    assert len(old)==1 and len(plan['windows'])==2
    assert len(plan['structured_sources'])==4 and not plan['overbudget_sources']
    assert len(rows)==36
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    trace=[];results={}
    def save(name,value):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    save('rubric.json',RUBRIC);save('plan.json',plan);save('structured.json',structured)
    (output/'transcript.txt').write_text(TRANSCRIPT,encoding='utf-8')
    def request(arm,messages,schema):
        if len(trace)>=3:raise AssertionError('Exceeded three-call experiment budget')
        e={'arm':arm,'messages':messages,'schema':schema};trace.append(e)
        start=time.monotonic()
        try:
            e['raw']=ollama.chat(messages,model=ollama.MODEL,json_output=schema,think=False,
                                 cpu_only=True,timeout=240)
            return e['raw']
        except Exception as exc:
            e['error']=str(exc);raise
        finally:
            e['seconds']=round(time.monotonic()-start,3);save('trace.json',trace)
    guide=(ROOT/'docs/Guia_Owll_y_Minutas_para_Ollama.md').read_text(encoding='utf-8')
    themes=[];gaps=[];rejections=[]
    start=time.monotonic()
    for section in old:
        messages,schema=editorial_request(section,'es')
        messages=[dict(messages[0],content=messages[0]['content']+
            '\n\nGuía editorial. Mantén el esquema JSON solicitado; aplica la guía a las descripciones.\n'+
            guide+'\n\nPara esta etapa, sigue el encargo y el esquema específicos del comienzo.'),*messages[1:]]
        rejected=[]
        try:
            accepted=validate_editorial(request('baseline',messages,schema),section,'es',
                rejected=rejected,on_rejection=lambda t,exc:rejections.append({'theme':t,'reason':str(exc)}))
            themes.extend(accepted);gaps.extend(rejected)
            gaps.extend(omitted_editorial_sources(section,accepted,rejected))
        except (OSError,RuntimeError,ValueError) as exc:
            gaps.extend(section);rejections.append({'reason':str(exc)})
    results['baseline']={'themes':themes,'gaps':gaps,'rejections':rejections,
                         'seconds':round(time.monotonic()-start,3)}
    start=time.monotonic()
    results['context']=compose_context(plan,'es',lambda m,s:request('context',m,s))
    results['context']['seconds']=round(time.monotonic()-start,3)
    metrics={}
    for arm,data in results.items():
        accounting=audit_source_passages(blocks,structured,data['themes'],data['gaps'])
        data['accounting']=accounting
        save(arm+'-evidence.json',data)
        lines=['# Thematic comparison — '+arm,'']
        for t in data['themes']:
            lines.extend(['**'+t['title_es']+'.** '+t['summary_es'],''])
        lines+=['## Original source passages requiring review','']
        for r in data['gaps']:
            lines.append('- '+str(r['source_id'])+': '+r['quote'])
        (output/(arm+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
        metrics[arm]={'requests':sum(e['arm']==arm for e in trace),
            'request_seconds':round(sum(e['seconds'] for e in trace if e['arm']==arm),3),
            'wall_seconds':data['seconds'],'themes':len(data['themes']),
            'theme_words':sum(len((t['title_es']+' '+t['summary_es']).split()) for t in data['themes']),
            'gaps':len(data['gaps']),'gap_ids':sorted({r['source_id'] for r in data['gaps']}),
            'uncited_ids':[r['source_id'] for r in accounting['uncited_passages']],
            'rejections':len(data['rejections'])}
    report={'scope':'three real CPU editorial calls; four shared literal structured records; no extraction or retry; not end-to-end',
            'metrics':metrics,'request_budget_ok':len(trace)==3,
            'semantic_acceptance':'manual review required; group ID coverage not clause coverage'}
    save('result.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
    return 0 if len(trace)==3 else 2
if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1])))
