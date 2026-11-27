"""Independent experimental report using saved structured evidence, not a new extraction."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_evidence import source_blocks,render_minutes,find_coverage_gaps
from engine.minutes_overview import build_overview
from qa.minutes_varied_long import fixture,VERSION,DIGEST
from qa.minutes_source_first import source_units,translate_units,grouping_request,validate_grouping,compose_groups

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main(original,output):
    output.mkdir(parents=True,exist_ok=False)
    source=original/'varied-targeted'/'evidence.json'
    e=json.loads(source.read_text(encoding='utf-8'))
    transcript,expected,topics=fixture();blocks=list(source_blocks(transcript))
    units=source_units(blocks,e['items'],e['presentation'],'es',e['localization'])
    save(output/'source-units.json',units)
    # Expected data are used only to evaluate, never to choose input or prompt.
    expected_stamps={x['stamp'] for x in topics}
    actual_stamps={u['source']['timestamp'] for u in units}
    assert expected_stamps==actual_stamps,(sorted(expected_stamps-actual_stamps),sorted(actual_stamps-expected_stamps))
    assert len(units)==55
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    started=time.monotonic();calls=[]
    def request(messages,schema,*,stage,scope):
        calls.append(stage)
        p=output/'trace.jsonl'
        def emit(event,**kw):
            with p.open('a',encoding='utf-8') as f:f.write(json.dumps({'stage':stage,'scope':scope,'event':event,**kw},ensure_ascii=False)+'\n')
        emit('request',messages=messages,schema=schema)
        raw=ollama.chat(messages,think=False,json_output=schema)
        emit('response',raw=raw)
        return raw
    translated,bad,_=translate_units(units,'es',request)
    save(output/'translated-units.json',translated);save(output/'translation-diagnostics.json',bad)
    messages,schema=grouping_request(translated,'es')
    try:
        raw=request(messages,schema,stage='grouping',scope={'language':'es'})
        groups=validate_grouping(raw,translated,'es')
    except (OSError,RuntimeError,ValueError) as exc:
        save(output/'result.json',{'passed':False,'grouping_error':str(exc),'translations_rejected':bad,'requests':calls,'seconds':time.monotonic()-started})
        return 2
    save(output/'groups.json',groups)
    themes,representatives=compose_groups(groups,translated,'es')
    # One representative sentence per group, with exact structured outcomes
    # from the existing overview. This is explicitly extractive, not a new
    # model-written executive narrative.
    overview=[' '.join(representatives[i:i+3]) for i in range(0,len(representatives),3)]
    overview.extend(build_overview(e['presentation'],[],'es'))
    gaps=find_coverage_gaps([r for b in blocks for r in b],e['items'])
    report=render_minutes(e['presentation'],'both','es',e['repetition_coverage']['unresolved_empty_block_ids'],gaps,
        editorial=themes,editorial_gaps=e['editorial_gaps'],executive_overview={'es':overview},
        show_timestamps=False,repetition_coverage=e['repetition_coverage'],localization=e['localization'])
    (output/'minutes.md').write_text(report,encoding='utf-8')
    # Explicitly check known defects; manual comparison across all units still required.
    texts={i:' '.join(u['text'] for u in translated if u['source']['source_id']==i).casefold() for i in (2,4,18,33,63)}
    checks={'every_descriptive_row':actual_stamps==expected_stamps,
        'all_units_retained':sum(len(g['unit_ids']) for g in groups)==len(units),
        'original_sources_unchanged':all(a['source']==b['source'] for a,b in zip(units,translated)),
        'no_failed_translation':not bad,
        'counter_and_accessibility':all(x in texts[2] for x in ('mostrador','accesibilidad','registro')),
        'ramp_and_private_contacts':all(x in texts[4] for x in ('rampa','entrada','contact')),
        'privacy_guide_retained':all(x in texts[18] for x in ('contact','públic')),
        'discussion_literal':all('se habló de' in texts[i] and 'se propuso' not in texts[i] for i in (33,63))}
    result={'checks':checks,'passed':all(checks.values()),'groups':len(groups),'units':len(units),
        'requests':calls,'seconds':round(time.monotonic()-started,3),
        'scope':'QA source-first architecture, saved structured records; not production or fresh pipeline',
        'quality':'manual comparison required; exact unit coverage is not semantic translation proof'}
    save(output/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
