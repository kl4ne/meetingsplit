"""Compare already-paid outputs using a conservative literal-anchor audit."""
import collections
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_bounded_synthesis import atoms,audit_themes,windows,byte_size
from engine.minutes_evidence import source_blocks

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def analyze(sources,items,themes):
    units,account=atoms(sources,items)
    audit=audit_themes(units,themes,'es')
    batches=list(windows(units))
    return {'source_units':len(units),'structured':sum(a['status']=='structured' for a in account),
        'statuses':dict(collections.Counter(a['status'] for a in audit)),
        'windows':len(batches),'oversize':sum(large for _,large in batches),
        'maximum_normal_input_bytes':max((byte_size(b) for b,large in batches if not large),default=0),
        'proposed_synthesis_calls_upper_bound':2*sum(not large for _,large in batches),
        'audit':audit}

def main(varied,dense,replay,out):
    plan=load(varied/'varied-targeted/plan.json')
    ve=load(varied/'varied-targeted/evidence.json')
    vsrc=[r for s in plan['sections'] for r in s['section']]
    v=analyze(vsrc,ve['items'],ve['editorial_themes'])
    de=load(dense/'evidence.json')
    original=(dense/'transcript.txt').read_text(encoding='utf-8')
    dsrc=[{'source_id':r['id'],'timestamp':r['timestamp'],'quote':r['text']}
          for b in source_blocks(original) for r in b]
    d=analyze(dsrc,load(replay/'items.json'),de['source_first'][0]['themes'])
    # Independently known partial omission in varied source 2, despite a cited ID.
    assert any(a['unit']['source']['source_id']==2 and a['status']=='anchor_gap'
               and 'accesibilidad' in a['missing'] for a in v['audit'])
    assert all(sum(x['statuses'].values())==x['source_units'] for x in (v,d))
    out.mkdir(parents=True,exist_ok=True)
    result={'scope':'offline lexical triage; not semantic acceptance or new inference',
            'varied_scope':'previously supplied editorial excerpts, not full transcript',
            'dense_scope':'full original source with corrected metadata; prior rendered themes',
            'varied':v,'dense':d}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:{a:b for a,b in x.items() if a!='audit'} for k,x in
                      [('varied',v),('dense',d)]},ensure_ascii=False),flush=True)

if __name__=='__main__':
    main(*map(Path,sys.argv[1:]))
