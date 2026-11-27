"""Replay exact recorded translation responses; no model call or source rewrite."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import render_minutes,repeated_topic_coverage,source_blocks
from engine.minutes_overview import build_overview
from engine.minutes_localization import (prepare_presentation,apply_translations,local_day,
                                           restore_protected_weekday)
from qa.minutes_long_acceptance import fixture,score

def main(source,prior,retry,output):
    transcript,checks=fixture()
    assert (source/'transcript.txt').read_text(encoding='utf-8')==transcript
    evidence=json.loads((source/'evidence.json').read_text(encoding='utf-8'))
    original=evidence['items']
    translated,todo=prepare_presentation(original,'es')
    accepted=[];corrections=[];rejected=[]
    for folder in (prior,retry):
        results=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        traces=json.loads((folder/'translation-trace.json').read_text(encoding='utf-8'))
        for batch in traces:
            for rec in json.loads(batch['raw'])['translations']:
                i=rec['id']
                if i not in todo or i in accepted:
                    continue
                if i in results['accepted']:
                    good,bad=apply_translations(json.dumps({'translations':[rec]}),translated,[i],'es')
                    accepted.extend(good)
                elif folder==retry:
                    corrected=restore_protected_weekday(rec['text'],original[i],'es')
                    if corrected is not None:
                        good,bad=apply_translations(json.dumps({'translations':[{'id':i,'text':corrected}]}),
                                                   translated,[i],'es')
                        if good:
                            accepted.extend(good)
                            corrections.append({'id':i,'recorded':rec['text'],'corrected':corrected,
                                               'source':original[i]['sources']})
    rejected=[i for i in todo if i not in accepted]
    immutable=all({k:v for k,v in a.items() if k!='text_es'}=={k:v for k,v in b.items() if k!='text_es'} for a,b in zip(original,translated))
    assert immutable
    displayed=[dict(i,due=local_day(i['due'],'es')) for i in translated]
    themes=evidence['editorial_themes'];blocks=list(source_blocks(transcript))
    coverage=repeated_topic_coverage(blocks,original,themes,evidence['empty_block_ids'])
    report=render_minutes(displayed,'both','es',coverage['unresolved_empty_block_ids'],evidence['coverage_gaps'],
        editorial=themes,editorial_gaps=evidence['editorial_gaps'],show_timestamps=False,
        executive_overview={'es':build_overview(displayed,themes,'es')},repetition_coverage=coverage)
    output.mkdir(parents=True,exist_ok=False)
    (output/'minutes.md').write_text(report,encoding='utf-8')
    (output/'presentation.json').write_text(json.dumps(translated,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'scope':'offline replay of exact recorded responses; no inference','candidate_ids':todo,
            'accepted':accepted,'unresolved':rejected,'protected_weekday_corrections':corrections,
            'facts_unchanged':score(transcript,checks,original)['passed'],
            'source_records_unchanged':immutable,'quality':'manual semantic review required'}
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='protected_weekday_corrections'},ensure_ascii=False))
    return 0 if not rejected and result['facts_unchanged'] and immutable else 2

if __name__=='__main__':
    raise SystemExit(main(*(Path(arg) for arg in sys.argv[1:])))
