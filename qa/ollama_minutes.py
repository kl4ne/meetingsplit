"""Explicit synthetic EN/ES generation QA; never reads or uploads meeting recordings."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.ollama import LocalService,MODEL
from engine.summarize import summarize_local

root=Path(sys.argv[1]).resolve()
transcript='[00:00:01] Ana will send the draft on Friday.\n[00:00:06] Luis agreed to review it on Monday.'
results=[]
languages=sys.argv[2:] or ('en','es')
if any(language not in ('en','es') for language in languages): raise ValueError('Use en and/or es')
with LocalService(root) as service:
    service.ensure_model()
    for language in languages:
        start=time.monotonic()
        report=summarize_local(transcript,'minutes',language,MODEL,endpoint=service.endpoint)
        (root/f'qa-minutes-{language}.md').write_text(report,encoding='utf-8')
        row={'language':language,'seconds':round(time.monotonic()-start,2),'characters':len(report),
             'required_names':all(name in report for name in ('Ana','Luis')),
             'complete_markdown':report.startswith('#'),'review_required':True}
        print(json.dumps(row),flush=True);results.append(row)
(root/'minutes-en-es.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
