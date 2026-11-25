"""Isolated Qwen3 non-thinking structured-output feasibility. Synthetic data only."""
import os,sys,json,time,re
from pathlib import Path
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='kl4ne/meetingsplit':
    raise SystemExit('CI only')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import ollama,summarize
from engine.control import Cancellation
from engine.minutes_evidence import source_blocks,validate_items,render_minutes,extraction_prompt
from desktop import components
from qa.minutes_acceptance import TRANSCRIPT,evaluate
root=Path(sys.argv[1]).resolve(strict=True)
def confined(p):
    p=Path(p).resolve(strict=True)
    if not p.is_dir() or not p.is_relative_to(root):raise ValueError('Outside QA root')
    return p
ollama.validate_local_folder=components.validate_local_folder=confined
result={'scope':'real model, source-level feasibility; synthetic only','ok':False,'attempts':[]}
def save(): (root/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
save()
task=Cancellation()
def schema(lang):
    properties={'category':{'type':'string','enum':['topic','decision','action','proposal','disagreement','pending']},
                'sources':{'type':'array','minItems':1,'maxItems':3,'items':{'type':'object','properties':{'id':{'type':'integer'},'quote':{'type':'string'}},'required':['id','quote'],'additionalProperties':False}},
                'owner':{'type':['string','null']},'due':{'type':['string','null']}}
    for l in ('es','en') if lang=='both' else (lang,):
        properties['text_'+l]={'type':'string'}
    return {'type':'object','properties':{'items':{'type':'array','items':{'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}}},'required':['items'],'additionalProperties':False}
def safe(s):
    return s.replace('<|','\\u003c|').replace('|>','|\\u003e').replace('<think>','\\u003cthink\\u003e').replace('</think>','\\u003c/think\\u003e')
def raw_extract(endpoint,rows,lang):
    messages=extraction_prompt(rows,lang)
    system=messages[0]['content']+' Return concise literal evidence and short descriptions. Do not explain.'
    prompt='<|im_start|>system\n'+safe(system)+'<|im_end|>\n<|im_start|>user\n'+safe(messages[1]['content'])+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
    payload={'model':ollama.MODEL,'prompt':prompt,'raw':True,'stream':True,'format':schema(lang),'keep_alive':'2m','options':{'temperature':0.3,'num_ctx':8192,'num_predict':2048,'top_p':0.8,'top_k':20}}
    chunks=[];count=0;done=False
    for record in ollama.stream_json(endpoint,'/api/generate',payload,task,lambda _:None,360):
        if record.get('thinking'):raise RuntimeError('Unexpected thinking output')
        text=record.get('response','');chunks.append(text);count+=len(text)
        if count>65536:raise RuntimeError('Output limit')
        if record.get('done'):
            if record.get('done_reason')=='length':raise RuntimeError('Generation token limit')
            done=True;break
    if not done:raise RuntimeError('Incomplete response')
    return ''.join(chunks)
try:
    components.install_package(components.OLLAMA_PACKAGE,root,lambda x:print(x,flush=True),task)
    with ollama.LocalService(root,task,lambda x:print(x,flush=True),reuse=False) as service:
        model=service.ensure_model(allow_download=True);result['model_digest']=model.get('digest')
        details=ollama.request_json(service.endpoint,'/api/show',{'model':ollama.MODEL})
        result['thinking']=details.get('thinking');result['runtime_version']=ollama.existing_status(service.endpoint)['version'];save()
        rows=list(source_blocks(TRANSCRIPT))[0]
        for lang in ('both','es','en'):
            t=time.monotonic()
            try:
                raw=raw_extract(service.endpoint,rows,lang)
                (root/(lang+'-raw.json')).write_text(raw,encoding='utf-8')
                items=validate_items(raw,rows,lang)
                evidence={'review_required':True,'items':items}
                checks=evaluate(evidence)
                (root/(lang+'-evidence.json')).write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
                (root/(lang+'-minutes.md')).write_text(render_minutes(items,'both',lang),encoding='utf-8')
                result['attempts'].append({'language':lang,'passed':all(checks.values()),'checks':checks,'seconds':round(time.monotonic()-t,2)})
            except Exception as exc:
                result['attempts'].append({'language':lang,'passed':False,'error':str(exc)[:800],'seconds':round(time.monotonic()-t,2)})
            save()
        result['ok']=len(result['attempts'])==3 and all(x['passed'] for x in result['attempts'])
except Exception as exc:
    result['error']=str(exc)[:1000];raise
finally:save()
if not result['ok']:raise SystemExit(2)
