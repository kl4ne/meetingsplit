"""Explicit local Ollama evaluation; synthetic transcripts only, no auto-downloads.

Pass means this narrow synthetic rubric passed, not that all AI claims are true.
Run on the intended Windows hardware with the optional model already installed.
"""
from pathlib import Path
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.ollama import LocalService, MODEL
from engine.summarize import summarize_local

TRANSCRIPT=(
    '[00:00:01] Ana will send the signed draft on Friday.\n'
    '[00:00:06] Luis confirmó que revisará el presupuesto el lunes.\n'
    '[00:00:12] Proposal only: move the next meeting to Saturday. Not approved.\n'
    '[00:00:18] Se aprobó por unanimidad conservar el horario actual.\n'
    '[00:00:23] Who will order supplies? No responsible person or deadline was assigned.\n'
)

def evaluate(evidence):
    items=evidence.get('items',[])
    def has(category,stamp,owner=None,due=None):
        return any(i['category']==category and any(s['timestamp']==stamp for s in i['sources'])
                   and (owner is None or i['owner']==owner)
                   and (due is None or i['due']==due) for i in items)
    return {
        'ana_friday_action':has('action','00:00:01','Ana','Friday'),
        'luis_lunes_action':has('action','00:00:06','Luis','lunes') or has('action','00:00:06','Luis','el lunes'),
        'proposal_not_decision':has('proposal','00:00:12') and not has('decision','00:00:12'),
        'actual_decision':has('decision','00:00:18'),
        'unassigned_not_invented':not any(i['category']=='action' and any(s['timestamp']=='00:00:23' for s in i['sources'])
                                         and (i['owner'] is not None or i['due'] is not None) for i in items),
        'manual_review_required':evidence.get('review_required') is True,
    }

def main():
    if len(sys.argv)!=2:
        raise SystemExit('Usage: python qa/minutes_acceptance.py <configured data root>')
    from desktop.storage import validate_local_folder
    root=validate_local_folder(Path(sys.argv[1]))
    import tempfile
    output=Path(tempfile.mkdtemp(prefix='MeetingSplit-minutes-QA-',dir=root))
    results=[]
    with LocalService(root) as service:
        service.ensure_model()
        for language in ('es','en','both'):
            started=time.monotonic()
            evidence={}
            report=summarize_local(TRANSCRIPT,'both',language,MODEL,
                endpoint=service.endpoint,evidence_sink=evidence.update)
            (output/f'{language}-minutes.md').write_text(report,encoding='utf-8')
            (output/f'{language}-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
            checks=evaluate(evidence)
            results.append({'language':language,'seconds':round(time.monotonic()-started,2),
                            'checks':checks,'passed':all(checks.values())})
    (output/'acceptance.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(output),'results':results},ensure_ascii=False,indent=2))
    return 0 if all(r['passed'] for r in results) else 2

if __name__=='__main__':
    raise SystemExit(main())
