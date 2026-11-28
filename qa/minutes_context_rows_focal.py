"""One real request on the affected window only; keep previous successful window as archived evidence."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import plan_context
from engine.minutes_context_row_citations import row_request,validate_rows
from qa.minutes_context_windows_preflight import TRANSCRIPT,RUBRIC

def main(archive,output):
    output.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    blocks=list(source_blocks(TRANSCRIPT))
    expected={26:'notice',27:'decision',28:'action',36:'notice'}
    items=[i for i in explicit_source_items([r for b in blocks for r in b],'es')
        if all(expected.get(r['source_id'])==i['category'] for r in i['sources'])]
    plan=plan_context(blocks,items)
    assert plan==json.loads((archive/'plan.json').read_text(encoding='utf-8'))
    assert TRANSCRIPT==(archive/'transcript.txt').read_text(encoding='utf-8')
    trace=json.loads((archive/'trace.json').read_text(encoding='utf-8'))
    assert len(trace)==3 and trace[1]['arm']=='context' and trace[2]['arm']=='context'
    prior=json.loads((archive/'context-evidence.json').read_text(encoding='utf-8'))
    units=plan['windows'][0]
    assert [r['source_id'] for u in units for r in u['sources']]==list(range(1,26))
    messages,schema=row_request(units,'es')
    save('rubric.json',RUBRIC)
    save('comparison-scope.json',{'affected_ids':list(range(1,26)),
      'prior_accepted_themes':[t for t in prior['themes'] if t['sources'][0]['source_id']<=25],
      'unchanged_archived_themes':[t for t in prior['themes'] if t['sources'][0]['source_id']>25],
      'prior_rejections':prior['rejections'],'prior_gaps':prior['gaps']})
    state=ollama.existing_status()
    assert state['version']=='0.40.18' and state['model']['digest']=='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90' and ollama.reusable_existing()
    record={'messages':messages,'schema':schema,'requests':1};start=time.monotonic()
    try:
        record['raw']=ollama.chat(messages,model=ollama.MODEL,json_output=schema,think=False,cpu_only=True,timeout=240)
        out=validate_rows(record['raw'],units,'es')
    except (OSError,RuntimeError,ValueError) as exc:
        record['error']=str(exc)
        out={'themes':[],'gaps':[r for u in units for r in u['sources']],
             'review_ids':[],'rejections':[{'reason':str(exc)}],'review_required':True}
    finally:
        record['seconds']=round(time.monotonic()-start,3);save('trace.json',record)
    save('evidence.json',out)
    lines=['# New first window only','']
    for t in out['themes']:
        lines+=['**'+t['title_es']+'.** '+t['summary_es'],'']
    lines+=['## Original review passages','']+['- '+str(r['source_id'])+': '+r['quote'] for r in out['gaps']]
    (output/'first-window.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    metrics={'requests':1,'seconds':record['seconds'],'themes':len(out['themes']),
      'gap_ids':[r['source_id'] for r in out['gaps']], 'review_ids':out['review_ids'],
      'rejections':len(out['rejections']),
      'scope':'one affected window, not complete report; manual semantic review required'}
    save('result.json',metrics);print(json.dumps(metrics,ensure_ascii=False),flush=True)
    return 0 if 'error' not in record else 2

if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
