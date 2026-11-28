"""Replay the exact archived contextual first window with interruption review."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import plan_context
from engine.minutes_context_row_citations import row_request,validate_rows
from engine.minutes_context_interruptions import quarantine_interrupted
from qa.minutes_context_windows_preflight import TRANSCRIPT

def main(archive,out):
    out.mkdir(parents=True,exist_ok=False)
    trace=json.loads((archive/'trace.json').read_text(encoding='utf-8'))
    original=json.loads((archive/'evidence.json').read_text(encoding='utf-8'))
    blocks=list(source_blocks(TRANSCRIPT))
    expected={26:'notice',27:'decision',28:'action',36:'notice'}
    items=[i for i in explicit_source_items([r for b in blocks for r in b],'es')
        if all(expected.get(r['source_id'])==i['category'] for r in i['sources'])]
    units=plan_context(blocks,items)['windows'][0]
    messages,schema=row_request(units,'es')
    assert messages==trace['messages'] and schema==trace['schema']
    before=validate_rows(trace['raw'],units,'es')
    assert before==original
    after=quarantine_interrupted(before,units,blocks)
    assert after['interruption_review_ids']==[19,20]
    assert [r['source_id'] for r in after['gaps']]==[10,11,12,19,20,25]
    assert len(after['themes'])==3 and len(after['quarantined_themes'])==1
    assert after['rejections']==before['rejections']
    for name,value in [('before.json',before),('after.json',after)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# First window — conservative review replay','']
    for theme in after['themes']:
        lines+=['**'+theme['title_es']+'.** '+theme['summary_es'],'']
    lines+=['## Original passages for review','']+['- '+str(r['source_id'])+': '+r['quote'] for r in after['gaps']]
    (out/'first-window.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result={'scope':'exact archived response, no inference, not semantic acceptance',
        'model_requests':0,'before_themes':len(before['themes']),'after_themes':len(after['themes']),
        'before_gap_ids':[r['source_id'] for r in before['gaps']],
        'after_gap_ids':[r['source_id'] for r in after['gaps']],
        'interruption_review_ids':after['interruption_review_ids'],
        'quarantined_themes':len(after['quarantined_themes']),
        'original_rejections_preserved':True}
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
if __name__=='__main__':
    main(Path(sys.argv[1]),Path(sys.argv[2]))
