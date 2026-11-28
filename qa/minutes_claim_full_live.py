"""One independent end-to-end synthetic run, with a hard transport budget.

The contextual path is explicitly selected. No desktop default changes.
Checks are structural, not a replacement for reading the independent rubric.
"""
import json,re,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama,summarize
from engine.minutes_evidence import source_blocks
from qa.minutes_claim_full_preflight import TRANSCRIPT,EXPECTED,RUBRIC

CALL_CAP=6
WALL_CAP=900
PER_CALL=300
class BudgetExceeded(AssertionError):pass

def main(preflight,out):
    out.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    assert TRANSCRIPT==(preflight/'transcript.txt').read_text(encoding='utf-8')
    assert RUBRIC==json.loads((preflight/'rubric.json').read_text(encoding='utf-8'))
    assert {str(k):v for k,v in EXPECTED.items()}==json.loads((preflight/'expected.json').read_text(encoding='utf-8'))
    prior=json.loads((preflight/'result.json').read_text(encoding='utf-8'))
    assert prior['model_requests']==0 and prior['future_real_call_cap']==CALL_CAP
    state=ollama.existing_status()
    assert state['version']=='0.40.18' and state['model']['digest']=='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90' and ollama.reusable_existing()
    save('rubric.json',RUBRIC);save('expected.json',EXPECTED)
    (out/'transcript.txt').write_text(TRANSCRIPT,encoding='utf-8')
    calls=[];events=[];evidence={};started=time.monotonic()
    original=summarize.ollama_chat
    def emit(event):
        events.append(event)
        with (out/'trace.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(event,ensure_ascii=False)+'\n')
    def bounded(messages,model,**kwargs):
        remaining=WALL_CAP-(time.monotonic()-started)
        if len(calls)>=CALL_CAP or remaining<1:raise BudgetExceeded('QA transport budget exhausted')
        kwargs.update(cpu_only=True,timeout=min(PER_CALL,remaining))
        current={'stage':events[-1]['stage'],'scope':events[-1]['scope']}
        calls.append(current);t=time.monotonic()
        try:return original(messages,model,**kwargs)
        except Exception as exc:
            current['error']=type(exc).__name__+': '+str(exc);raise
        finally:
            current['seconds']=round(time.monotonic()-t,3)
            save('calls.json',calls)
    result={'scope':'fresh independent synthetic full minutes pipeline, CPU, Spanish both mode; no audio or hardware validation',
            'completed':False,'checks':{},'semantic_acceptance':'manual review required'}
    try:
        with patch.object(summarize,'ollama_chat',bounded):
            report=summarize.summarize_local(TRANSCRIPT,'both','es',ollama.MODEL,
                narrative_strategy='contextual_claim_qa',qa_trace=emit,evidence_sink=evidence.update,
                progress=lambda msg:print(msg,flush=True))
        (out/'minutes.md').write_text(report,encoding='utf-8')
        save('evidence.json',evidence)
        rows={r['id']:r for b in source_blocks(TRANSCRIPT) for r in b}
        operations={'decision','action','notice','proposal','pending','disagreement'}
        items=evidence['items']
        actual={(r['source_id'],i['category']) for i in items if i['category'] in operations for r in i['sources']}
        refs=[r for i in items for r in i['sources']]+[r for t in evidence['editorial_themes'] for r in t['sources']]+evidence['editorial_gaps']
        claim_refs=[r for t in evidence['editorial_themes'] for c in t['claims'] for r in c['sources']]
        refs+=claim_refs
        gaps={r['source_id'] for r in evidence['editorial_gaps']}
        diag=evidence['context_diagnostics']
        interrupted={i for w in diag['windows'] for i in w['interruption_review_ids']}
        action=[i for i in items if i['category']=='action' and any(r['source_id']==19 for r in i['sources'])]
        checks={
            'all_four_actual_outcomes':set(EXPECTED.items())<=actual,
            'no_unexpected_operations':actual<=set(EXPECTED.items()),
            'named_thursday_commitment':any(i['owner']=='Elena Ruiz' and i['due'] in ('Thursday','by Thursday') for i in action),
            'inclusive_deadline_visible':'a más tardar el jueves' in report,
            'all_citations_literal':all(r['source_id'] in rows and r['timestamp']==rows[r['source_id']]['timestamp'] and r['quote'] in rows[r['source_id']]['text'] for r in refs),
            'no_unaccounted_passages':not evidence['source_accounting']['uncited_passages'],
            'interrupted_source_retained':{12,13}<=gaps and {12,13}<=interrupted,
            'no_confirmed_theme_using_interrupted_source':all(not ({12,13}&{r['source_id'] for r in t['sources']}) for t in evidence['editorial_themes']),
            'has_thematic_prose':bool(evidence['editorial_themes']),
            'claim_evidence_retained':all(t.get('claims') and {(r['source_id'],r['timestamp'],r['quote']) for r in t['sources']}=={(r['source_id'],r['timestamp'],r['quote']) for c in t['claims'] for r in c['sources']} for t in evidence['editorial_themes']),
            'claim_strategy_only':evidence['narrative_strategy']=='contextual_claim_qa',
            'all_gaps_visible':all(r['quote'] in report for r in evidence['editorial_gaps']),
            'no_full_theme_in_overview':all(t['summary_es'] not in report.split('## Temas tratados')[0] for t in evidence['editorial_themes']),
            'overview_and_detail':'## Resumen ejecutivo' in report and '## Temas tratados' in report,
            'no_timecodes_tables':not re.search(r'\[\d{2}:\d{2}:\d{2}\]',report) and not any(l.startswith('|') for l in report.splitlines()),
            'no_localization_rejections':all(not d['rejected'] for d in evidence['localization']),
            'manual_review_retained':evidence['review_required'] is True,
            'budget':len(calls)<=CALL_CAP}
        result.update(completed=True,checks=checks,structured_outcomes=sorted([list(x) for x in actual]),
            themes=len(evidence['editorial_themes']),claims=sum(len(t['claims']) for t in evidence['editorial_themes']),gap_ids=sorted(gaps),
            review_records=sum(i['category']=='review' for i in items),
            word_count=len(report.split()),context_windows=diag['window_count'],
            context_rejections=sum(len(w['rejections']) for w in diag['windows']),
            quarantined_themes=sum(len(w['quarantined_themes']) for w in diag['windows']))
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(requests=len(calls),seconds=round(time.monotonic()-started,3),
            call_cap=CALL_CAP,wall_cap=WALL_CAP,per_call_cap=PER_CALL)
        result['passed']=result['completed'] and all(result['checks'].values())
        save('result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
