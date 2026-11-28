"""Archived real synthetic claim response through new full report path.
Extraction is explicitly mocked empty; existing deterministic notice retained.
Not a complete archived pipeline or new model run.
"""
import json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import summarize
from qa.minutes_context_claims_preflight import TRANSCRIPT,RUBRIC

def main(archive,prior,out):
    out.mkdir(parents=True,exist_ok=False)
    def load(p):return json.loads(p.read_text(encoding='utf-8'))
    assert TRANSCRIPT==(archive/'transcript.txt').read_text(encoding='utf-8')
    assert RUBRIC==load(archive/'rubric.json')
    req=load(archive/'claim_candidate-request.json')
    raw=(archive/'claim_candidate-raw.json').read_text(encoding='utf-8')
    old=load(prior/'validated.json')
    calls=[];e={}
    def answer(messages,*args,json_output,**kw):
        if 'items' in json_output['properties']:
            calls.append('mock_extraction');return '{"items":[]}'
        assert {'messages':messages,'schema':json_output}==req
        calls.append('archived_claim_response');return raw
    with patch.object(summarize,'ollama_chat',answer):
        report=summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',
            narrative_strategy='contextual_claim_qa',evidence_sink=e.update)
    assert calls==['mock_extraction','archived_claim_response']
    assert e['editorial_gaps']==old['gaps']
    assert [t['claims'] for t in e['editorial_themes']]==[t['claims'] for t in old['themes']]
    assert e['context_diagnostics']['windows'][0]['quote_repairs']==old['quote_repairs']
    assert e['context_diagnostics']['windows'][0]['neutralized_titles']
    assert e['context_diagnostics']['windows'][0]['review_ids']==[8,9]
    assert len(e['editorial_themes'])==3 and sum(len(t['claims']) for t in e['editorial_themes'])==6
    assert e['review_required'] and e['source_accounting']['uncited_passages']==[]
    assert [(i['category'],[r['source_id'] for r in i['sources']]) for i in e['items']]==[('notice',[11])]
    assert all(report.count(t['summary_es'])==1 for t in e['editorial_themes'])
    assert all(r['quote'] in report for r in e['editorial_gaps'])
    (out/'minutes.md').write_text(report,encoding='utf-8')
    (out/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'scope':'archived claim response with mocked extraction, integrated report; not semantic acceptance',
        'model_requests':0,'mock_extraction_responses':1,'archived_claim_responses':1,'claims':6,'themes':3,
        'gap_ids':[8,9],'review_ids':[8,9],'notice_count':1,'words':len(report.split()),
        'original_claims_unchanged':True,'semantic_acceptance':False}
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
if __name__=='__main__':main(*map(Path,sys.argv[1:]))
