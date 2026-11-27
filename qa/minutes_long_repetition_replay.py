"""Replay only the exact historical synthetic fixture, with no model calls."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,repeated_topic_coverage,render_minutes
from engine.minutes_overview import build_overview
from qa.minutes_long_acceptance import fixture,score

def main(source,output):
    transcript,checks=fixture()
    assert (source/'transcript.txt').read_text(encoding='utf-8')==transcript
    evidence=json.loads((source/'evidence.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=False)
    blocks=list(source_blocks(transcript))
    items=evidence['items'];themes=evidence['editorial_themes']
    coverage=repeated_topic_coverage(blocks,items,themes,evidence['empty_block_ids'])
    report=render_minutes(items,'both','es',coverage['unresolved_empty_block_ids'],
        evidence['coverage_gaps'],editorial=themes,editorial_gaps=evidence['editorial_gaps'],
        show_timestamps=False,executive_overview={'es':build_overview(items,themes,'es')},
        repetition_coverage=coverage)
    results={'facts_still_correct':score(transcript,checks,items)['passed'],
             'all_four_blocks_accounted':len(coverage['covered_empty_blocks'])==4 and not coverage['unresolved_empty_block_ids'],
             'all_15_reviews_accounted':len(coverage['repeated_review_items'])==15 and not coverage['unresolved_review_indices'],
             'original_diagnostics_preserved':len(evidence['empty_block_ids'])==4 and sum(i['category']=='review' for i in items)==15,
             'visible_review_notice':'advertencias de extracción' in report}
    (output/'minutes.md').write_text(report,encoding='utf-8')
    (output/'result.json').write_text(json.dumps({'checks':results,'repetition_coverage':coverage,
        'raw_empty_ids':evidence['empty_block_ids'],'raw_review_count':15,'quality':'not approved; semantic review still required'},
        ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results),flush=True)
    return 0 if all(results.values()) else 2

if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
