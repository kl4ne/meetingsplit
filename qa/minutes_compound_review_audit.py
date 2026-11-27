"""Measure the integrated compound-review cue on archived synthetic outputs.

No inference. Re-render the Spanish short and varied records with exactly
the current presentation and review functions. Dense source-first output
is only a contrasting diagnostic, not the current production strategy.
"""
import argparse
import collections
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.minutes_evidence import source_blocks,render_minutes
from engine.minutes_source_accounting import audit_source_passages,audit_compound_citations
from engine.minutes_theme_presentation import compact_repeated_theme_sources,separate_structured_themes
from engine.minutes_overview import build_overview
from qa.minutes_editorial_ab import TRANSCRIPT
from qa.minutes_varied_long import fixture

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def analyze(label,transcript,evidence,out,*,render=True):
    blocks=list(source_blocks(transcript))
    items=evidence['items']
    themes=evidence['editorial_themes']
    presented=evidence.get('presentation') or items
    gaps=evidence.get('editorial_gaps',[])
    display,compacted=compact_repeated_theme_sources(blocks,themes)
    display,moved=separate_structured_themes(blocks,display,presented,('es',),evidence.get('localization',[]))
    accounting=audit_source_passages(blocks,items,themes,gaps)
    findings=audit_compound_citations(display,items,'es',
        already_visible=[*gaps,*accounting['uncited_passages']])
    refs=[f['source'] for f in findings['es']]
    result={'case':label,'scope':'saved outputs, no model calls',
        'rows':sum(map(len,blocks)),'themes_displayed':len(display),
        'flagged_source_ids':[r['source_id'] for r in refs],
        'flagged_quotes':len(refs),'flagged_quote_words':sum(len(r['quote'].split()) for r in refs),
        'clause_reasons':dict(collections.Counter(c['reason'] for f in findings['es'] for c in f['clauses'])),
        'existing_gap_ids':[r['source_id'] for r in gaps],
        'uncited_ids':[r['source_id'] for r in accounting['uncited_passages']],
        'findings':findings}
    if render:
        repetition=evidence.get('repetition_coverage')
        for mode in ('summary','minutes','both'):
            kwargs={'editorial':display,'editorial_gaps':gaps,
                'executive_overview':{'es':build_overview(presented,display,'es',detail_included=mode!='summary')},
                'show_timestamps':False,'repetition_coverage':repetition,
                'localization':evidence.get('localization',[]),'repeated_themes':compacted,
                'respect_mode':True,'uncited_passages':accounting['uncited_passages']}
            args=(presented,mode,'es',(repetition or {}).get('unresolved_empty_block_ids',[]),
                  evidence.get('coverage_gaps',[]))
            before=render_minutes(*args,**kwargs)
            after=render_minutes(*args,**kwargs,compound_review=findings)
            (out/(label+'-'+mode+'.md')).write_text(after,encoding='utf-8')
            result.setdefault('render_delta',{})[mode]={'before_words':len(before.split()),
                'after_words':len(after.split()),'additional_words':len(after.split())-len(before.split())}
    return result

def main(short,varied,dense,reclassified,out):
    out.mkdir(parents=True,exist_ok=False)
    v=load(varied/'varied-revalidated/evidence.json')
    s=load(short/'evidence.json')
    d=load(dense/'evidence.json')
    transcript,_,_=fixture()
    cases=[analyze('short',TRANSCRIPT,s,out),analyze('varied',transcript,v,out),
           analyze('dense-old-source-first',(dense/'transcript.txt').read_text(encoding='utf-8'),d,out,render=False)]
    # Corrected dense metadata has no newly translated or rendered prose.
    # Keep it separate and use original themes only for the audit.
    d2={**d,'items':load(reclassified/'items.json'),'presentation':load(reclassified/'items.json'),'localization':[]}
    cases.append(analyze('dense-corrected-metadata-old-themes',(dense/'transcript.txt').read_text(encoding='utf-8'),d2,out,render=False))
    report={'verification':'heuristic review cue, not semantic acceptance',
        'requests':0,'cases':cases,
        'known_compound_omissions_flagged':{str(i):i in cases[1]['flagged_source_ids'] for i in (2,4)}}
    save(out/'result.json',report)
    print(json.dumps({**report,'cases':[{k:v for k,v in c.items() if k!='findings'} for c in cases]},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('short','varied','dense','reclassified','out'):p.add_argument(k,type=Path)
    a=p.parse_args();main(a.short,a.varied,a.dense,a.reclassified,a.out)
