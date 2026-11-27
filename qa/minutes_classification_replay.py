"""Offline replay of synthetic artifact 15180493657; no new model calls."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa.minutes_editorial_ab import TRANSCRIPT
from engine.minutes_evidence import (source_blocks, plan_quote_retry, validate_items,
    unresolved_retry_items, explicit_source_items, reconcile_source_items, find_coverage_gaps,
    render_minutes)
from engine.minutes_overview import build_overview

def main(source, output):
    if (source/'transcript.txt').read_text(encoding='utf-8')!=TRANSCRIPT:
        raise ValueError('Exact synthetic fixture required')
    output.mkdir(parents=True,exist_ok=False)
    evidence=json.loads((source/'pipeline-evidence.json').read_text(encoding='utf-8'))
    events=[json.loads(l) for l in (source/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    extraction=[e for e in events if e.get('stage')=='extraction' and e.get('event')=='response']
    rows=[row for block in source_blocks(TRANSCRIPT) for row in block]
    assert len(extraction)==2
    assert extraction[0]['scope']['source_ids']==[r['id'] for r in rows]
    kept,subset=plan_quote_retry(extraction[0]['raw'],rows,'es')
    assert [r['id'] for r in subset]==extraction[1]['scope']['source_ids']
    retry=validate_items(extraction[1]['raw'],subset,'es')
    items=reconcile_source_items(kept+retry+unresolved_retry_items(subset,retry,'es'),explicit_source_items(rows,'es'))
    gaps=find_coverage_gaps(rows,items)
    themes=evidence['editorial_themes']
    overview=build_overview(items,themes,'es')
    report=render_minutes(items,'both','es',evidence['empty_block_ids'],gaps,editorial=themes,
                          editorial_gaps=evidence['editorial_gaps'],show_timestamps=False,
                          executive_overview={'es':overview})
    indexed={i['sources'][0]['source_id']:i for i in items}
    checks={
        'guidance_is_topic':indexed[3]['category']=='topic',
        'notices_verbatim':all(indexed[i]['text_es']==rows[i-1]['text'] for i in (4,5)),
        'unassigned_pending':indexed[11]['category']=='pending' and indexed[11]['owner'] is None and indexed[11]['due'] is None,
        'commitment_preserved':indexed[10]['text_es']==rows[9]['text'],
        'proposal_not_approved':indexed[8]['category']=='proposal',
        'budget_preserved':indexed[6]['category']=='topic' and 'USD 2,400' in report,
        'no_structural_gaps':not gaps,
        'all_six_themes_retained':len(themes)==6 and all(t['title_es'] in report for t in themes),
    }
    (output/'minutes.md').write_text(report,encoding='utf-8')
    (output/'replay.json').write_text(json.dumps({'scope':'offline only','checks':checks,
        'items':items,'coverage_gaps':gaps,'remaining_review_count':sum(i['category']=='review' for i in items),
        'quality':'manual review required'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False))
    return 0 if all(checks.values()) else 2

if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
