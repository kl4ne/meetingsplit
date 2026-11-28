"""Counterfactual deterministic failure-path replay; no model calls.

Archive contains real extraction and rejected translation, not completed claim responses.
Restored exact punctuation changes context planning and localization input; deliberately
simulate the two timeouts instead of claiming identical transport replay.
"""
import json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import summarize
from qa.minutes_claim_full_preflight import TRANSCRIPT,RUBRIC
def main(archive,out):
    out.mkdir(parents=True,exist_ok=False)
    assert TRANSCRIPT==(archive/'transcript.txt').read_text(encoding='utf-8')
    assert RUBRIC==json.loads((archive/'rubric.json').read_text(encoding='utf-8'))
    old=json.loads((archive/'evidence.json').read_text(encoding='utf-8'))
    trace=[json.loads(l) for l in (archive/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    pairs=[(a,b) for a,b in zip(trace,trace[1:]) if a['event']=='request' and b['event'] in ('response','request_error')]
    assert [a['stage'] for a,b in pairs]==['extraction','contextual_claim_editorial','contextual_claim_editorial','localization']
    assert all(b['error_type']=='TimeoutError' for a,b in pairs[1:3])
    stages=[];e={};events=[]
    def answer(messages,model,*,json_output,**kwargs):
        stage=events[-1]['stage'];stages.append(stage)
        if stage=='extraction':
            req,res=pairs[0]
            assert messages==req['messages'] and json_output==req['schema']
            return res['raw']
        if stage=='contextual_claim_editorial':
            raise TimeoutError('Ollama operation exceeded its time limit')
        if stage=='localization':
            req,res=pairs[-1]
            assert json_output==req['schema'] and messages[0]==req['messages'][0]
            prior=json.loads(req['messages'][1]['content']);current=json.loads(messages[1]['content'])
            assert len(prior['records'])==len(current['records'])==1
            prior['records'][0]['source']+='.'
            assert prior==current
            return res['raw']
        raise AssertionError(stage)
    with patch.object(summarize,'ollama_chat',answer):
        report=summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',narrative_strategy='contextual_claim_qa',
            evidence_sink=e.update,qa_trace=events.append)
    assert stages==['extraction','contextual_claim_editorial','contextual_claim_editorial','localization'] or stages==['extraction','contextual_claim_editorial','localization']
    assert not e['editorial_themes']
    assert e['context_diagnostics']['structured_source_ids']==[17,18,19,22]
    assert [d['source_id'] for d in e['context_diagnostics']['structured_period_repairs']]==[18,19]
    assert {i for w in e['context_diagnostics']['windows'] for i in w['interruption_review_ids']}=={12,13}
    assert [r['source_id'] for r in e['editorial_gaps']]==[i for i in range(1,23) if i not in (17,18,19,22)]
    assert all(r['quote'] in report for r in e['editorial_gaps'])
    assert report.count('## Resumen ejecutivo')==1 and 'No se completó la síntesis temática.' in report
    assert 'a más tardar el jueves' in report
    assert not e['localization'][0]['rejected'] and e['localization'][0]['protected_weekdays']==[6]
    assert [i['category'] for i in e['items']]==[i['category'] for i in old['items']]
    assert e['review_required']
    (out/'minutes.md').write_text(report,encoding='utf-8')
    (out/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'scope':'archived extraction/translation with simulated timeouts on changed context plan; no model inference',
        'model_requests':0,'simulated_timeouts':stages.count('contextual_claim_editorial'),
        'structured_ids':e['context_diagnostics']['structured_source_ids'],'gap_ids':[r['source_id'] for r in e['editorial_gaps']],
        'interrupted_ids':[12,13],'deadline_protected':True,'single_summary_heading':True,'themes':0,
        'semantic_acceptance':False}
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
if __name__=='__main__':main(*map(Path,sys.argv[1:]))
