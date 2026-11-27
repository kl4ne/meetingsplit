"""Translate only missing presentation records from the exact synthetic long run."""
import json
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import render_minutes,repeated_topic_coverage,source_blocks
from engine.minutes_overview import build_overview
from engine.minutes_localization import prepare_presentation,translation_request,apply_translations,local_day
from qa.minutes_long_acceptance import fixture,score
from qa.minutes_editorial_ab import VERSION,DIGEST

def main(source,output):
    transcript,checks=fixture()
    assert (source/'transcript.txt').read_text(encoding='utf-8')==transcript
    evidence=json.loads((source/'evidence.json').read_text(encoding='utf-8'))
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    output.mkdir(parents=True,exist_ok=False)
    original=evidence['items']
    translated,todo=prepare_presentation(original,'es')
    started=time.monotonic()
    accepted=[];rejected=[];traces=[]
    for start in range(0,len(todo),5):
        ids=todo[start:start+5]
        messages,schema=translation_request(translated,ids,'es')
        trace={'ids':ids,'messages':messages,'schema':schema}
        try:
            raw=ollama.chat(messages,think=False,json_output=schema)
            trace['raw']=raw
            good,bad=apply_translations(raw,translated,ids,'es')
            accepted.extend(good);rejected.extend(bad)
        except Exception as exc:
            rejected.extend({'id':i,'reason':str(exc)} for i in ids)
        traces.append(trace)
        (output/'translation-trace.json').write_text(json.dumps(traces,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all({k:v for k,v in a.items() if k!='text_es'}=={k:v for k,v in b.items() if k!='text_es'} for a,b in zip(original,translated))
    # Display-only localized days; score original immutable records.
    displayed=[dict(i,due=local_day(i['due'],'es')) for i in translated]
    blocks=list(source_blocks(transcript));themes=evidence['editorial_themes']
    coverage=repeated_topic_coverage(blocks,original,themes,evidence['empty_block_ids'])
    # The historical report has few outcomes; keep all of them in the brief
    # rather than sampling just two, by using the improved overview helper.
    report=render_minutes(displayed,'both','es',coverage['unresolved_empty_block_ids'],evidence['coverage_gaps'],
        editorial=themes,editorial_gaps=evidence['editorial_gaps'],show_timestamps=False,
        executive_overview={'es':build_overview(displayed,themes,'es')},repetition_coverage=coverage)
    (output/'minutes.md').write_text(report,encoding='utf-8')
    (output/'presentation.json').write_text(json.dumps(translated,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'candidate_ids':todo,'accepted':accepted,'rejected':rejected,'seconds':round(time.monotonic()-started,3),
            'calls':len(traces),'facts_unchanged':score(transcript,checks,original)['passed'],
            'quality':'requires manual semantic review; translation changes presentation only'}
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if not rejected and len(accepted)==len(todo) else 2

if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
