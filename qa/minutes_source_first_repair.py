"""Repair only seven conflicting/missing group assignments from exact QA artifacts."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import source_blocks,render_minutes,find_coverage_gaps
from engine.minutes_overview import build_overview
from qa.minutes_varied_long import fixture,VERSION,DIGEST
from qa.minutes_source_first import (source_units,plan_grouping_repair,grouping_repair_request,
    apply_grouping_repair,compose_groups)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main(original,saved,output,live):
    output.mkdir(parents=True,exist_ok=False)
    e=json.loads((original/'varied-targeted'/'evidence.json').read_text(encoding='utf-8'))
    transcript,expected,topics=fixture();blocks=list(source_blocks(transcript))
    units=json.loads((saved/'source-units.json').read_text(encoding='utf-8'))
    assert source_units(blocks,e['items'],e['presentation'],'es',e['localization'])==units
    translated=json.loads((saved/'translated-units.json').read_text(encoding='utf-8'))
    assert len(units)==len(translated)==55
    assert all(a['source']==b['source'] and a['id']==b['id'] for a,b in zip(units,translated))
    assert not json.loads((saved/'translation-diagnostics.json').read_text(encoding='utf-8'))
    events=[json.loads(l) for l in (saved/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    replies=[r for r in events if r['stage']=='grouping' and r['event']=='response'];assert len(replies)==1
    plan=plan_grouping_repair(replies[0]['raw'],translated,'es')
    assert plan['duplicates']==[6,8,31,38,39] and plan['missing']==[7,18]
    save(output/'plan.json',plan)
    print(json.dumps({'reused_units':len(translated),'fixed_assignments':48,'disputed':plan['disputed'],'duplicates':plan['duplicates'],'missing':plan['missing']}),flush=True)
    if not live:return 0
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    messages,schema=grouping_repair_request(plan,translated,'es')
    started=time.monotonic()
    raw=ollama.chat(messages,think=False,json_output=schema)
    save(output/'trace.json',{'messages':messages,'schema':schema,'raw':raw,'seconds':time.monotonic()-started})
    groups=apply_grouping_repair(raw,plan,translated,'es')
    themes,reps=compose_groups(groups,translated,'es')
    overview=[' '.join(reps[i:i+3]) for i in range(0,len(reps),3)]
    overview.extend(build_overview(e['presentation'],[],'es'))
    gaps=find_coverage_gaps([r for b in blocks for r in b],e['items'])
    report=render_minutes(e['presentation'],'both','es',e['repetition_coverage']['unresolved_empty_block_ids'],gaps,
        editorial=themes,editorial_gaps=e['editorial_gaps'],executive_overview={'es':overview},
        show_timestamps=False,repetition_coverage=e['repetition_coverage'],localization=e['localization'])
    (output/'minutes.md').write_text(report,encoding='utf-8')
    save(output/'groups.json',groups)
    save(output/'translated-units.json',translated)
    save(output/'evidence.json',{**e,'source_first_themes':themes,'source_first_group_plan':groups})
    checks={'all_units_once':sorted(i for g in groups for i in g['unit_ids'])==list(range(1,56)),
            'fixed_membership_preserved':all(any(g['title']==f['title'] and set(f['unit_ids'])<=set(g['unit_ids']) for g in groups) for f in plan['fixed']),
            'all_source_texts_present':all(u['text'] in ' '.join(t['summary_es'] for t in themes) for u in translated)}
    result={'checks':checks,'passed':all(checks.values()),'groups':len(groups),'units':55,'reused_translations':26,
            'requests':1,'seconds':round(time.monotonic()-started,3),
            'scope':'QA grouping-only repair, no retranslation or extraction; semantic grouping/overview still needs review'}
    save(output/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':
    raise SystemExit(main(*(Path(x) for x in sys.argv[1:4]),live='--live' in sys.argv[4:]))
