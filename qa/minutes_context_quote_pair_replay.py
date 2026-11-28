"""Exact archived A/B candidate replay; zero inference; fictional material only."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import plan_context
from engine.minutes_context_claims import claim_request,validate_claims,recovery_targets
from qa.minutes_context_claims_preflight import TRANSCRIPT,RUBRIC

def main(archive,out):
    out.mkdir(parents=True,exist_ok=False)
    def load(n):return json.loads((archive/n).read_text(encoding='utf-8'))
    def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    assert TRANSCRIPT==(archive/'transcript.txt').read_text(encoding='utf-8')
    assert RUBRIC==load('rubric.json')
    blocks=list(source_blocks(TRANSCRIPT));rows=[r for b in blocks for r in b]
    items=explicit_source_items(rows,'es');plan=plan_context(blocks,items)
    assert items==load('items.json') and plan==load('plan.json')
    units=plan['windows'][0]
    messages,schema=claim_request(units,'es')
    assert {'messages':messages,'schema':schema}==load('claim_candidate-request.json')
    raw=(archive/'claim_candidate-raw.json').read_text(encoding='utf-8')
    old=validate_claims(raw,units,'es',blocks=blocks)
    assert old==load('claim_candidate-validated.json')
    new=validate_claims(raw,units,'es',blocks=blocks,repair_quote_pairs=True)
    assert len(old['themes'])==len(new['themes'])==3
    assert [r['source_id'] for r in old['gaps']]==[3,4,8,9]
    assert [r['source_id'] for r in new['gaps']]==[8,9]
    assert old['review_ids']==new['review_ids']==[8,9]
    assert new['rejections']==old['rejections'][1:]
    assert new['quote_repairs']==[{'code':'restored_original_double_quote_pair','source_id':4,
                                  'theme_index':0,'claim_index':1,'ref_index':1}]
    assert new['themes'][1:]==old['themes'][1:]
    a,b=old['themes'][0],new['themes'][0]
    assert a['claims']==[b['claims'][0],b['claims'][2]]
    assert b['claims'][1]['sources'][1]['quote']==rows[3]['text']
    assert new['review_required'] and recovery_targets(units,new)==[]
    byid={r['id']:r for r in rows}
    refs=[r for t in new['themes'] for c in t['claims'] for r in c['sources']]
    assert all(r['timestamp']==byid[r['source_id']]['timestamp'] and r['quote'] in byid[r['source_id']]['text'] for r in refs)
    result={'scope':'frozen fictional candidate quote-pair repair replay; not semantic acceptance',
        'model_requests':0,'old_claims':sum(len(t['claims']) for t in old['themes']),
        'new_claims':sum(len(t['claims']) for t in new['themes']),
        'old_gap_ids':[3,4,8,9],'new_gap_ids':[8,9],'review_ids':[8,9],
        'restored_source_ids':[4],'other_claims_unchanged':True,'notice_unchanged':True,
        'semantic_acceptance':False}
    save('validated.json',new);save('result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main(*map(Path,sys.argv[1:]))
