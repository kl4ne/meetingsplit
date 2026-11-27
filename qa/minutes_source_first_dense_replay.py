"""Revalidate exact saved metadata after descriptive sentence classification repair.

No Ollama. Reuse the original final batch responses, not cached final categories.
Account for original source sentences and report which new detail units would
require translation/grouping. Do not claim a fresh successful dense run.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,explicit_source_items,reconcile_source_items,find_coverage_gaps
from engine.minutes_source_first import validate_source_first_extraction,source_units_with_accounting
from qa.minutes_source_first_dense import fixture,score

def main(source,output):
    output.mkdir(parents=True,exist_ok=False)
    transcript,checks,topics=fixture()
    assert (source/'transcript.txt').read_text(encoding='utf-8')==transcript
    old=json.loads((source/'evidence.json').read_text(encoding='utf-8'))
    events=[json.loads(l) for l in (source/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    blocks=list(source_blocks(transcript));rows=[r for b in blocks for r in b];by_id={r['id']:r for r in rows}
    responses=[e for e in events if e['stage']=='source_first_extraction' and e['event']=='response']
    # Ignore unsuccessful parent batches which were replaced by child requests.
    scopes=[set(e['scope']['source_ids']) for e in responses]
    leaves=[e for n,e in enumerate(responses) if not any(s<scopes[n] for s in scopes[n+1:])]
    seen_rows=[];extracted=[]
    for e in leaves:
        ids=e['scope']['source_ids'];batch=[by_id[i] for i in ids]
        req=next(r for r in events if r['stage']=='source_first_extraction' and r['event']=='request' and r['scope']==e['scope'])
        assert json.loads(req['messages'][1]['content'])['source_rows']==batch
        seen_rows.extend(ids)
        extracted.extend(validate_source_first_extraction(e['raw'],batch,'es'))
    assert sorted(seen_rows)==list(by_id)
    unique={}
    for i in extracted:
        key=(i['category'],tuple((r['source_id'],r['quote']) for r in i['sources']),i['owner'],i['due'],i['text_es'],i.get('text_en'))
        unique.setdefault(key,i)
    items=reconcile_source_items(list(unique.values()),explicit_source_items(rows,'es'))
    facts=score(transcript,checks,items)
    def operation(i):
        return i['category'] in ('decision','action','notice','proposal','pending','disagreement') or (i['category']=='topic' and any('USD 3,650' in r['quote'] for r in i['sources']))
    old_expected=[i for i in old['items'] if operation(i) and not (i['category']=='proposal' and any(r['source_id'] in (26,39) for r in i['sources']))]
    new_expected=[i for i in items if operation(i)]
    assert sorted(map(lambda i:json.dumps(i,sort_keys=True,ensure_ascii=False),old_expected))==sorted(map(lambda i:json.dumps(i,sort_keys=True,ensure_ascii=False),new_expected))
    units,account=source_units_with_accounting(blocks,items,items,'es')
    old_keys={(u['source']['source_id'],u['source']['quote']) for u in old['source_first'][0]['units']}
    new_keys={(u['source']['source_id'],u['source']['quote']) for u in units}
    assert old_keys<=new_keys
    added=[u for u in units if (u['source']['source_id'],u['source']['quote']) not in old_keys]
    checks={'all_ten_facts':facts['passed'],'no_unexpected_operations':not facts['unexpected'],
            'no_unresolved_review':not any(i['category']=='review' for i in items),
            'no_structural_gaps':not find_coverage_gaps(rows,items),
            'all_prior_detail_units_preserved':old_keys<=new_keys,
            'sentence_accounting_preserved':len(account)==len(old['source_first'][0]['source_accounting'])}
    result={'checks':checks,'passed':all(checks.values()),'facts':facts,
            'old_detail_units':len(old_keys),'new_detail_units':len(new_keys),'added_units':added,
            'scope':'offline metadata replay only; no fresh translation or grouping, editorial quality not certified'}
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'items.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='facts'},ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
