"""Revalidate actual varied targeted themes; no model call or evidence rewrite."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_brief import validate_editorial,editorial_modality_error
def main(source,output):
    evidence=json.loads((source/'varied-targeted'/'evidence.json').read_text(encoding='utf-8'))
    themes=evidence['editorial_themes']
    bad=[];good=[]
    for index,t in enumerate(themes):
        refs=t['sources']
        raw=json.dumps({'themes':[{'source_ids':[r['source_id'] for r in refs],
                'title_es':t['title_es'],'summary_es':t['summary_es']}]},ensure_ascii=False)
        rejected=[];reasons=[]
        kept=validate_editorial(raw,refs,'es',rejected=rejected,
                   on_rejection=lambda _theme,exc:reasons.append(str(exc)))
        if kept:
            assert kept==[t]
            good.extend(kept)
        else:
            bad.append({'index':index,'sources':refs,'theme':t,'reasons':reasons})
    assert len(themes)==39
    assert {r['source_id'] for t in bad for r in t['sources']}=={33,63}
    assert len(bad)==2 and len(good)==37
    output.mkdir(parents=True,exist_ok=False)
    result={'raw_themes':len(themes),'accepted_unchanged':len(good),'rejected':bad,
            'note':'Only modality regression verified; source-ID coverage does not certify within-source details.'}
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    main(*(Path(x) for x in sys.argv[1:]))
