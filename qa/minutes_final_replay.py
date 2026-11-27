"""Exact full-pipeline replay of the integrated synthetic short fixture.

Every model request must match the saved request exactly. No new inference,
no network, no change to the original artifact.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import summarize,ollama
from qa.minutes_editorial_ab import TRANSCRIPT,REFERENCE,RUBRIC

def main(source,output):
    assert (source/'transcript.txt').read_text(encoding='utf-8')==TRANSCRIPT
    old=json.loads((source/'pipeline-evidence.json').read_text(encoding='utf-8'))
    events=[json.loads(line) for line in (source/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    requests=[e for e in events if e.get('event')=='request']
    responses=[e for e in events if e.get('event')=='response' and e.get('stage')]
    assert len(requests)==len(responses)==4
    for req,resp in zip(requests,responses):
        assert req['stage']==resp['stage'] and req['scope']==resp['scope']
    calls=[];traces=[];evidence={}
    def reply(messages,model,*args,json_output,**kwargs):
        i=len(calls)
        if i>=len(requests):
            raise AssertionError('Unexpected additional model request')
        req=requests[i]
        assert messages==req['messages'], f'Request {i} input changed'
        assert json_output==req['schema'], f'Request {i} schema changed'
        assert model==req['model']
        calls.append(req['stage'])
        return responses[i]['raw']
    with patch.object(summarize,'ollama_chat',reply):
        report=summarize.summarize_local(TRANSCRIPT,'both','es',ollama.MODEL,
                   narrative_strategy='localized_editorial',evidence_sink=evidence.update,qa_trace=traces.append)
    changes=[(a,b) for a,b in zip(old['items'],evidence['items']) if a!=b]
    checks={
        'all_recorded_requests_match':len(calls)==4,
        'one_classification_change_only':len(old['items'])==len(evidence['items']) and len(changes)==1 and
            changes[0][0]['category']=='review' and changes[0][1]['category']=='topic' and
            changes[0][0]['sources']==changes[0][1]['sources'] and changes[0][1]['sources'][0]['source_id']==12,
        'all_editorial_themes_unchanged':old['editorial_themes']==evidence['editorial_themes'],
        'proposal_and_pending_separated':len(evidence['structured_theme_presentation'])==2,
        'no_unresolved_classification':not any(i['category']=='review' for i in evidence['items']),
        'no_detected_gaps':not evidence['coverage_gaps'] and not evidence['editorial_gaps'],
        'no_translation_failures':all(not x['rejected'] for x in evidence['localization']),
        'no_hidden_warning':evidence['review_required'] and 'Borrador para revisión' in report,
        'expected_sections':all(h in report for h in ('## Resumen ejecutivo','## Temas tratados','## Avisos','## Propuestas','## Pendientes')),
    }
    output.mkdir(parents=True,exist_ok=False)
    (output/'minutes.md').write_text(report,encoding='utf-8')
    (output/'reference.md').write_text(REFERENCE,encoding='utf-8')
    (output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'result.json').write_text(json.dumps({'checks':checks,'calls':calls,'passed':all(checks.values()),
        'quality':'manual review required; no new inference','rubric':RUBRIC},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False))
    return 0 if all(checks.values()) else 2
if __name__=='__main__':
    raise SystemExit(main(*(Path(a) for a in sys.argv[1:])))
