"""Re-render exact synthetic long evidence with verified translated presentation."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,render_minutes,repeated_topic_coverage
from engine.minutes_overview import build_overview
from engine.minutes_theme_presentation import compact_repeated_theme_sources
from qa.minutes_long_acceptance import fixture,score

def main(original,localized,output):
    transcript,checks=fixture()
    assert (original/'transcript.txt').read_text(encoding='utf-8')==transcript
    evidence=json.loads((original/'evidence.json').read_text(encoding='utf-8'))
    items=evidence['items'];themes=evidence['editorial_themes']
    presentation=json.loads((localized/'presentation.json').read_text(encoding='utf-8'))
    assert all({k:v for k,v in a.items() if k!='text_es'}=={k:v for k,v in b.items() if k!='text_es'} for a,b in zip(items,presentation))
    blocks=list(source_blocks(transcript))
    kept,omitted=compact_repeated_theme_sources(blocks,themes)
    repetition=repeated_topic_coverage(blocks,items,themes,evidence['empty_block_ids'])
    report=render_minutes(presentation,'both','es',repetition['unresolved_empty_block_ids'],evidence['coverage_gaps'],
        editorial=kept,editorial_gaps=evidence['editorial_gaps'],executive_overview={'es':build_overview(presentation,kept,'es')},
        repetition_coverage=repetition,show_timestamps=False,localization=[{'language':'es','rejected':[]}],repeated_themes=omitted)
    output.mkdir(parents=True,exist_ok=False)
    (output/'minutes.md').write_text(report,encoding='utf-8')
    result={'scope':'offline exact artifact; no inference','original_theme_count':len(themes),'displayed_theme_count':len(kept),
            'omitted':omitted,'facts_unchanged':score(transcript,checks,items)['passed'],
            'unique_fragment_retained':any(t['title_es']=='Continuidad de la discusión' for t in kept),
            'quality':'manual editorial review remains required'}
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if len(omitted)==2 and result['facts_unchanged'] and result['unique_fragment_retained'] else 2
if __name__=='__main__':
    raise SystemExit(main(*(Path(a) for a in sys.argv[1:])))
