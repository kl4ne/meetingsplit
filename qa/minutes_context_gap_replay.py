"""Strict archived complete pipeline replay; no model calls."""
import json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import summarize
from qa.minutes_context_adapter_preflight import TRANSCRIPT

def main(archive,out):
    out.mkdir(parents=True,exist_ok=False)
    assert (archive/'transcript.txt').read_text(encoding='utf-8')==TRANSCRIPT
    old=json.loads((archive/'evidence.json').read_text(encoding='utf-8'))
    trace=[json.loads(l) for l in (archive/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[(e,n) for e,n in zip(trace,trace[1:]) if e['event']=='request' and n['event']=='response']
    assert len(responses)==5
    pos=0;last={};evidence={}
    def event(e):
        if e['event']=='request':last.update(e)
    def saved(messages,model,*,json_output,**kwargs):
        nonlocal pos
        req,reply=responses[pos];pos+=1
        assert model==req['model'] and messages==req['messages'] and json_output==req['schema']
        assert last['stage']==req['stage'] and last['scope']==req['scope']
        assert last['cpu_only']==req['cpu_only']
        return reply['raw']
    with patch.object(summarize,'ollama_chat',saved):
        report=summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',
            narrative_strategy='contextual_qa',qa_trace=event,evidence_sink=evidence.update)
    assert pos==5
    compaction=evidence['context_diagnostics'].pop('gap_presentation_compaction')
    assert evidence==old
    evidence['context_diagnostics']['gap_presentation_compaction']=compaction
    assert [r['source']['source_id'] for r in compaction]==[12,13]
    assert [r['source_id'] for r in evidence['editorial_gaps']]==[12,13,14]
    assert report.count('Someone mentioned an unclear measurement')==1
    assert 'and the recording stopped in the middle of' in report
    assert 'a más tardar el viernes' in report
    before=(archive/'minutes.md').read_text(encoding='utf-8')
    result={'scope':'strict five-response replay, presentation only, no semantic acceptance',
        'replayed_responses':pos,'model_requests':0,'original_evidence_unchanged':True,
        'compacted_source_ids':[r['source']['source_id'] for r in compaction],
        'original_gap_ids':[r['source_id'] for r in evidence['editorial_gaps']],
        'before_words':len(before.split()),'after_words':len(report.split())}
    (out/'minutes.md').write_text(report,encoding='utf-8')
    (out/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
