"""One executive lead request; reuse exact repaired groups and 55 units."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import source_blocks,render_minutes,find_coverage_gaps
from engine.minutes_overview import build_overview
from qa.minutes_varied_long import fixture,VERSION,DIGEST
from qa.minutes_source_first import validate_grouping,compose_groups
from qa.minutes_source_first_executive import executive_input,executive_request,validate_executive

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main(saved,output):
    output.mkdir(parents=True,exist_ok=False)
    source=saved/'group-repair'
    e=json.loads((source/'evidence.json').read_text(encoding='utf-8'))
    units=json.loads((source/'translated-units.json').read_text(encoding='utf-8'))
    groups=json.loads((source/'groups.json').read_text(encoding='utf-8'))
    assert len(units)==55 and len(groups)==9
    assert validate_grouping(json.dumps({'groups':groups}),units,'es')==groups
    themes,reps=compose_groups(groups,units,'es')
    assert themes==e['source_first_themes']
    transcript,_,_=fixture();rows=[r for b in source_blocks(transcript) for r in b]
    records=executive_input(groups,units)
    messages,schema=executive_request(records,'es')
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    started=time.monotonic()
    raw=ollama.chat(messages,think=False,json_output=schema)
    seconds=round(time.monotonic()-started,3)
    save(output/'trace.json',{'messages':messages,'schema':schema,'raw':raw,'seconds':seconds})
    try:
        lead=validate_executive(raw,records,'es')
    except ValueError as exc:
        result={'passed':False,'reason':str(exc),'requests':1,'seconds':seconds,
            'scope':'QA only, preserve prior report; no fallback presented as success'}
        save(output/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
        return 2
    overview=lead+build_overview(e['presentation'],[],'es')
    report=render_minutes(e['presentation'],'both','es',e['repetition_coverage']['unresolved_empty_block_ids'],
        find_coverage_gaps(rows,e['items']),editorial=themes,editorial_gaps=e['editorial_gaps'],
        executive_overview={'es':overview},show_timestamps=False,repetition_coverage=e['repetition_coverage'],
        localization=e['localization'])
    before=(source/'minutes.md').read_text(encoding='utf-8')
    detail='## Temas tratados'
    assert before.split(detail,1)[1]==report.split(detail,1)[1], 'Detailed minutes changed'
    (output/'minutes.md').write_text(report,encoding='utf-8')
    (output/'before.md').write_text(before,encoding='utf-8')
    result={'passed':True,'requests':1,'seconds':seconds,'lead_words':len(' '.join(lead).split()),
        'groups':len(groups),'units':len(units),'detail_unchanged':True,'lead':lead,
        'scope':'QA-only descriptive lead synthesis, structured outcomes and all detail unchanged',
        'quality':'manual semantic comparison required'}
    save(output/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
