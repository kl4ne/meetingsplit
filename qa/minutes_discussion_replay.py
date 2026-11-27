"""Replay exact integrated short extraction with the discussion-only guard."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,validate_items,reconcile_source_items,explicit_source_items,find_coverage_gaps
from qa.minutes_editorial_ab import TRANSCRIPT
def main(original,output):
    assert (original/'transcript.txt').read_text(encoding='utf-8')==TRANSCRIPT
    evidence=json.loads((original/'pipeline-evidence.json').read_text(encoding='utf-8'))
    rows=[r for b in source_blocks(TRANSCRIPT) for r in b]
    events=[json.loads(line) for line in (original/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    extracted=[e for e in events if e.get('stage')=='extraction' and e.get('event')=='response']
    assert len(extracted)==1 and extracted[0]['scope']['source_ids']==[r['id'] for r in rows]
    result=reconcile_source_items(validate_items(extracted[0]['raw'],rows,'es'),explicit_source_items(rows,'es'))
    old=evidence['items']
    assert len(old)==len(result)
    changes=[{'index':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(old,result)) if a!=b]
    assert len(changes)==1
    change=changes[0]
    assert change['before']['category']=='review' and change['after']['category']=='topic'
    assert change['before']['sources']==change['after']['sources']
    assert change['after']['sources'][0]['source_id']==12
    assert change['before']['owner']==change['after']['owner'] is None
    assert change['before']['due']==change['after']['due'] is None
    assert not find_coverage_gaps(rows,result)
    output.mkdir(parents=True,exist_ok=False)
    (output/'result.json').write_text(json.dumps({'changed':changes,'no_other_changes':True,
        'coverage_gaps':[],'quality':'lexical classification only; not semantic certification'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Only source 12 recovered as descriptive topic; all other evidence records unchanged.')
if __name__=='__main__':
    main(*(Path(a) for a in sys.argv[1:]))
