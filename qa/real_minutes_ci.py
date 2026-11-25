"""Actual optional Ollama runtime and Qwen on disposable CI, source-level QA."""
import json,os,sys,time
from pathlib import Path
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='kl4ne/meetingsplit':
    raise SystemExit('CI only')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import ollama,summarize
from desktop import components
from engine.control import Cancellation
from qa.minutes_acceptance import TRANSCRIPT,evaluate
root=Path(sys.argv[1]).resolve(strict=True)
out=root/'minutes-report.json'
def confined(path):
    p=Path(path).resolve(strict=True)
    if not p.is_dir() or not p.is_relative_to(root):raise ValueError('Outside QA root')
    return p
ollama.validate_local_folder=components.validate_local_folder=confined
result={'candidate_source':'5152b851490988dd3d63d3a0fe377867d985a860','scope':'source-level real Ollama and Qwen; synthetic only; not frozen GUI or ASUS acceptance','ok':False,'languages':[]}
def save():out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
save()
task=Cancellation()
try:
    components.install_package(components.OLLAMA_PACKAGE,root,lambda x:print(x,flush=True),task)
    with ollama.LocalService(root,task,lambda x:print(x,flush=True),reuse=False) as service:
        model=service.ensure_model(allow_download=True)
        result['model_digest']=model.get('digest')
        result['runtime_version']=ollama.existing_status(service.endpoint)['version'];save()
        for lang in ('both','es','en'):
            started=time.monotonic();evidence={}
            try:
                report=summarize.summarize_local(TRANSCRIPT,'both',lang,ollama.MODEL,endpoint=service.endpoint,cancel=task,progress=lambda x:print(x,flush=True),evidence_sink=evidence.update)
                (root/(lang+'-minutes.md')).write_text(report,encoding='utf-8')
                (root/(lang+'-evidence.json')).write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
                checks=evaluate(evidence)
                result['languages'].append({'language':lang,'checks':checks,'passed':all(checks.values()),'seconds':round(time.monotonic()-started,2)})
            except Exception as exc:
                result['languages'].append({'language':lang,'passed':False,'error':str(exc)[:700]})
            save()
        result['ok']=all(x['passed'] for x in result['languages']) and len(result['languages'])==3
except Exception as exc:
    result['error']=str(exc)[:1000];raise
finally:save()
if not result['ok']:raise SystemExit(2)
