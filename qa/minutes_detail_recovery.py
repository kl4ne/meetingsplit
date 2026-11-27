"""Targeted manual-reference experiment on the exact saved varied report.

Three Spanish source rows are used literally; one English-containing theme
needs new inference. All remaining themes and structured records are immutable.
Not a generic automatic semantic repair or a fresh pipeline benchmark.
"""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama
from engine.minutes_brief import validate_editorial,editorial_request
from engine.minutes_evidence import source_blocks,render_minutes,find_coverage_gaps
from engine.minutes_theme_presentation import compact_repeated_theme_sources,separate_structured_themes
from engine.minutes_overview import build_overview
from qa.minutes_varied_long import fixture,VERSION,DIGEST

def save(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def main(source,output):
    output.mkdir(parents=True,exist_ok=False)
    old=json.loads((source/'varied-targeted'/'evidence.json').read_text(encoding='utf-8'))
    themes=old['editorial_themes']; items=old['items']; display=old['presentation']
    transcript,_,_=fixture()
    blocks=list(source_blocks(transcript))
    assert len(themes)==39
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    corrected=list(themes);audit=[]
    # Manual reference intervention in QA only, not a production rule.
    for idx,title in [(1,'Accesibilidad, bienvenida y registro'),(17,'Preparación de ejemplos para voluntarios'),(34,'Claridad de las observaciones')]:
        t=themes[idx];assert len(t['sources'])==1
        assert t['sources'][0]['source_id']=={1:2,17:33,34:63}[idx]
        raw={'themes':[{'source_ids':[t['sources'][0]['source_id']], 'title_es':title,
                         'summary_es':t['sources'][0]['quote']}]}
        corrected[idx]=validate_editorial(json.dumps(raw,ensure_ascii=False),t['sources'],'es')[0]
        audit.append({'index':idx,'method':'manual literal Spanish reference','before':t,'after':corrected[idx]})
    idx=2;t=themes[idx]
    assert [r['source_id'] for r in t['sources']]==[4,18]
    messages,schema=editorial_request(t['sources'],'es')
    schema['properties']['themes']['minItems']=1
    schema['properties']['themes']['maxItems']=1
    messages[0]['content']+=(
        ' Return exactly one theme with both source IDs. Preserve every substantive statement, '
        'including the first sentence of each excerpt and specific physical accessibility details. '
        'Do not replace a concrete facility with a generic statement. Distinguish public and confidential information. '
        'Use idiomatic Spanish and no added obligations or proposals.')
    started=time.monotonic()
    raw=ollama.chat(messages,json_output=schema)
    save(output/'detail-trace.json',{'messages':messages,'schema':schema,'raw':raw,'seconds':time.monotonic()-started})
    got=validate_editorial(raw,t['sources'],'es')
    assert len(got)==1 and got[0]['sources']==t['sources']
    corrected[idx]=got[0]
    audit.append({'index':idx,'method':'one targeted translation/synthesis request','before':t,'after':got[0]})
    checks={
      'only_four_themes_changed':all(a==b for i,(a,b) in enumerate(zip(themes,corrected)) if i not in (1,2,17,34)),
      'same_sources':all(a['sources']==b['sources'] for a,b in zip(themes,corrected)),
      'reception_counter_accessibility':all(w in corrected[1]['summary_es'].casefold() for w in ('accesibilidad','mostrador')),
      'entrance_ramp':all(w in corrected[2]['summary_es'].casefold() for w in ('rampa','entrada')),
      'confidentiality_retained':any(w in corrected[2]['summary_es'].casefold() for w in ('privad','confidencial')),
      'discussion_not_proposal':all(corrected[i]['summary_es']==themes[i]['sources'][0]['quote'] for i in (17,34)),
    }
    shown,compacted=compact_repeated_theme_sources(blocks,corrected)
    shown,moved=separate_structured_themes(blocks,shown,display,('es',),old['localization'])
    gaps=find_coverage_gaps([r for b in blocks for r in b],items)
    report=render_minutes(display,'both','es',old['repetition_coverage']['unresolved_empty_block_ids'],gaps,
        editorial=shown,editorial_gaps=old['editorial_gaps'],executive_overview={'es':build_overview(display,shown,'es')},
        show_timestamps=False,repetition_coverage=old['repetition_coverage'],localization=old['localization'],repeated_themes=compacted)
    (output/'minutes.md').write_text(report,encoding='utf-8')
    save(output/'evidence.json',{**old,'editorial_themes':corrected,'manual_reference_changes':audit})
    result={'checks':checks,'passed':all(checks.values()),'calls':1,'seconds':round(time.monotonic()-started,3),
       'scope':'QA-only manual reference intervention plus one model request; not automatic production acceptance',
       'remaining':'grouping, global executive overview, generalized within-source semantic coverage'}
    save(output/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
