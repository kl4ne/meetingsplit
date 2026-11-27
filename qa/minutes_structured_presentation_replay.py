"""Offline display comparison with exact integrated short artifact."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,render_minutes
from engine.minutes_overview import build_overview
from engine.minutes_theme_presentation import separate_structured_themes
from qa.minutes_editorial_ab import TRANSCRIPT
def main(original,output):
    assert (original/'transcript.txt').read_text(encoding='utf-8')==TRANSCRIPT
    e=json.loads((original/'pipeline-evidence.json').read_text(encoding='utf-8'))
    themes=e['editorial_themes'];items=e['presentation']
    blocks=list(source_blocks(TRANSCRIPT))
    kept,moved=separate_structured_themes(blocks,themes,items,('es',),e['localization'])
    report=render_minutes(items,'both','es',e['repetition_coverage']['unresolved_empty_block_ids'],
        e['coverage_gaps'],editorial=kept,editorial_gaps=e['editorial_gaps'],
        executive_overview={'es':build_overview(items,kept,'es')},repetition_coverage=e['repetition_coverage'],
        show_timestamps=False,localization=e['localization'])
    output.mkdir(parents=True,exist_ok=False)
    before=(original/'pipeline.md').read_text(encoding='utf-8')
    (output/'before.md').write_text(before,encoding='utf-8')
    (output/'minutes.md').write_text(report,encoding='utf-8')
    result={'moved':moved,'original_themes':len(themes),'displayed_topics':len(kept),
            'before_characters':len(before),'after_characters':len(report),
            'review_notice_preserved':'Clasificación pendiente de revisión' in report,
            'quality':'manual comparison required; original source and theme data unchanged'}
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if len(moved)==2 and result['review_notice_preserved'] else 2
if __name__=='__main__':
    raise SystemExit(main(*(Path(a) for a in sys.argv[1:])))
