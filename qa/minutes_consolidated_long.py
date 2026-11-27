"""Long synthetic source acceptance; no real recordings or personal data."""
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import ollama,summarize
from engine.minutes_evidence import source_blocks
from qa.minutes_long_acceptance import fixture,score
from qa.minutes_editorial_ab import VERSION,DIGEST

def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main(output):
    output.mkdir(parents=True,exist_ok=False)
    state=ollama.existing_status()
    if state['version']!=VERSION or not state['model'] or state['model'].get('digest')!=DIGEST or not ollama.reusable_existing():
        raise RuntimeError('Pinned local model/server unavailable')
    transcript,checks=fixture()
    blocks=list(source_blocks(transcript))
    (output/'transcript.txt').write_text(transcript,encoding='utf-8')
    save(output/'expected.json',checks)
    save(output/'environment.json',{'model':ollama.MODEL,'digest':DIGEST,'version':VERSION,
        'language':'es','input':'historical synthetic bilingual fixture, distinct from unavailable 29-block run',
        'rows':len(transcript.splitlines()),'blocks':len(blocks),'characters':len(transcript)})
    trace=output/'trace.jsonl'
    def emit(event):
        with trace.open('a',encoding='utf-8') as f:
            f.write(json.dumps(event,ensure_ascii=False)+'\n')
    original=ollama.stream_json
    calls=0
    def stream(endpoint,route,payload,cancel,progress,deadline_seconds=900):
        nonlocal calls
        calls+=1
        number=calls
        start=time.monotonic()
        emit({'event':'transport_request','call':number,'payload':payload})
        try:
            for row in original(endpoint,route,payload,cancel,progress,deadline_seconds):
                if row.get('done'):
                    emit({'event':'transport_done','call':number,'seconds':time.monotonic()-start,
                        'metrics':{key:row.get(key) for key in ('done_reason','prompt_eval_count','eval_count','total_duration','load_duration')}})
                yield row
        except Exception as exc:
            emit({'event':'transport_error','call':number,'reason':str(exc),'type':type(exc).__name__})
            raise
    cache=output/'extraction-cache';cache.mkdir()
    def read_block(key):
        file=cache/(key+'.json')
        return file.read_text(encoding='utf-8') if file.is_file() else None
    def write_block(key,raw):
        (cache/(key+'.json')).write_text(raw,encoding='utf-8')
    evidence={}
    start=time.monotonic()
    result={'scope':'Linux CPU source QA, not frozen Windows EXE or ASUS GPU','passed':False}
    try:
        with patch.object(ollama,'stream_json',stream):
            report=summarize.summarize_local(transcript,'both','es',ollama.MODEL,
                evidence_sink=evidence.update,qa_trace=emit,read_block=read_block,write_block=write_block,
                narrative_strategy='validated_editorial',progress=lambda msg:print(msg,flush=True))
        (output/'minutes.md').write_text(report,encoding='utf-8')
        save(output/'evidence.json',evidence)
        facts=score(transcript,checks,evidence['items'])
        criteria={'historical_11_fact_rubric':facts['passed'],
            'no_structural_gaps':not evidence['coverage_gaps'],
            'no_editorial_gaps':not evidence['editorial_gaps'],
            'no_empty_blocks':not evidence['empty_block_ids'],
            'no_unclassified_items':not any(i['category']=='review' for i in evidence['items']),
            'overview_and_details':'## Resumen ejecutivo' in report and '## Temas tratados' in report,
            'no_rewrite_calls':not any(e.get('stage') in ('draft','review') and e.get('event')=='request'
                                     for e in map(json.loads,trace.read_text(encoding='utf-8').splitlines()))}
        result.update(criteria=criteria,facts=facts,theme_count=len(evidence['editorial_themes']),
                      editorial_gaps=evidence['editorial_gaps'],passed=all(criteria.values()),
                      editorial_quality='manual review of entire document remains required')
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(seconds=round(time.monotonic()-start,3),requests=calls)
        save(output/'result.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('facts','editorial_gaps')},ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2

if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1])))
