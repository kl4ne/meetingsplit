"""Explicit local-only comparison of an existing MeetingSplit 0.8.19 result ZIP.

Default inspection does not connect to Ollama or write anything. Live mode is
opt-in, uses only an already-running verified loopback service, and never opens
audio members, starts services, installs components or changes the input ZIP.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import stat
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile, BadZipFile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from desktop.storage import validate_local_folder
from engine import ollama,summarize
from engine.control import Cancellation,JobCancelled
from engine.minutes_evidence import source_blocks
from engine.minutes_context_windows import plan_context

MODEL_DIGEST='56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90'
RUNTIMES={'0.40.6','0.40.18'}
MEMBERS={
    'transcript':'RESULTADOS_COMPLETOS/Transcripciones/TRANSCRIPCION_COMPLETA.txt',
    'baseline':'RESULTADOS_COMPLETOS/Minutas/RESUMEN_Y_MINUTA_LOCAL.md',
    'evidence':'RESULTADOS_COMPLETOS/Datos_JSON/MINUTA_EVIDENCIAS.json',
    'manifest':'RESULTADOS_COMPLETOS/Datos_JSON/manifest.json'}
LIMITS={'transcript':4*1024**2,'baseline':4*1024**2,
        'evidence':32*1024**2,'manifest':2*1024**2}
CALL_CAP=32
WALL_CAP=3600
PER_CALL=300
CONSENT='ACEPTO-PROCESAMIENTO-LOCAL'
class BudgetExceeded(AssertionError):pass

def safe_path(path):
    path=Path(path).expanduser()
    # Fail closed on reparse/symlink ancestors rather than merely resolving them.
    for p in (path,*path.parents):
        info=p.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Unsafe linked/reparse path')
    return path.resolve(strict=True)

def input_path(path):
    p=safe_path(path)
    if not p.is_file() or p.suffix.lower()!='.zip':raise ValueError('Select the existing results ZIP')
    validate_local_folder(p.parent)
    return p

def read_input(path):
    p=input_path(path)
    data={}
    with ZipFile(p,'r') as z:
        for key,name in MEMBERS.items():
            matches=[m for m in z.infolist() if m.filename.casefold()==name.casefold()]
            if len(matches)!=1 or matches[0].filename!=name:
                raise ValueError('Required unique archive member missing or ambiguous: '+key)
            info=matches[0]
            if (info.is_dir() or info.flag_bits&1 or stat.S_ISLNK(info.external_attr>>16)
                    or info.file_size>LIMITS[key]):
                raise ValueError('Unsafe archive member: '+key)
            with z.open(info,'r') as f:raw=f.read(LIMITS[key]+1)
            if len(raw)!=info.file_size or len(raw)>LIMITS[key]:
                raise ValueError('Archive member size mismatch')
            data[key]=raw
    manifest=json.loads(data['manifest'].decode('utf-8-sig'))
    old=json.loads(data['evidence'].decode('utf-8-sig'))
    settings=manifest.get('resume_signature',{}).get('settings',{})
    if (manifest.get('version')!='0.8.19' or manifest.get('status')!='complete'
        or manifest.get('summary_status') not in ('complete','needs_review')
        or settings.get('ollama_model')!=ollama.MODEL
        or old.get('narrative_strategy')!='localized_editorial'):
        raise ValueError('Expected a completed local 0.8.19 baseline')
    mode,language=settings.get('report'),settings.get('language')
    if mode not in ('summary','minutes','both') or language not in ('es','en','both'):
        raise ValueError('Missing original report mode or language')
    transcript=data['transcript'].decode('utf-8-sig')
    baseline=data['baseline'].decode('utf-8-sig')
    blocks=list(source_blocks(transcript))
    rows={r['id']:r for block in blocks for r in block}
    if len(rows)>5000:raise ValueError('Source exceeds the local QA size limit')
    for ref in [r for i in old['items'] for r in i['sources']]+[r for t in old['editorial_themes'] for r in t['sources']]+old['editorial_gaps']:
        r=rows.get(ref['source_id'])
        if not r or r['timestamp']!=ref['timestamp'] or not ref['quote'] or ref['quote'] not in r['text']:
            raise ValueError('Baseline evidence does not match source')
    plan=plan_context(blocks,old['items'])
    return p,data,transcript,baseline,old,mode,language,blocks,plan

def hash_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def metrics(report,evidence):
    return {'document_words':len(report.split()),
        'themes':len(evidence['editorial_themes']),
        'editorial_gaps':len(evidence['editorial_gaps']),
        'review_records':sum(i['category']=='review' for i in evidence['items']),
        'structured_records':{cat:sum(i['category']==cat for i in evidence['items'])
            for cat in ('notice','decision','action','proposal','pending','disagreement')},
        'uncited_passages':len((evidence.get('source_accounting') or {}).get('uncited_passages',[]))}

def inspect(path,*,claim_reuse=False):
    p,data,transcript,baseline,old,mode,language,blocks,plan=read_input(path)
    if claim_reuse:
        from engine.minutes_claim_frozen import frozen_extraction
        from engine.minutes_claim_structured_refs import restore_structured_periods
        from engine.minutes_evidence import explicit_source_items
        items,empty=frozen_extraction(old,blocks,language)
        items,repairs=restore_structured_periods(items,explicit_source_items([r for b in blocks for r in b],language),blocks)
        plan=plan_context(blocks,items)
    return {'scope':'read-only source planning; no Ollama connection or inference',
            'version':'0.8.19','mode':mode,'language':language,
            'rows':sum(map(len,blocks)),'source_words':sum(len(r['text'].split()) for b in blocks for r in b),
            'extraction_blocks':len(blocks),'context_units':len(plan['units']),
            'context_windows':len(plan['windows']),
            'overbudget_rows':len(plan['overbudget_sources']),
            'baseline':metrics(baseline,old),'model_requests':0,
            **({'strategy':'contextual_claim_qa','reused_extraction_records':len(items),'original_empty_block_ids':empty,'planned_period_repairs':len(repairs)} if claim_reuse else {}),
            'semantic_acceptance':False}

def verify_model():
    # Existing default service only. Do not start a managed server or pull.
    state=ollama.existing_status(ollama.DEFAULT_ENDPOINT)
    model=state.get('model') or {}
    if (not state.get('available') or state.get('version') not in RUNTIMES
        or model.get('digest')!=MODEL_DIGEST or not ollama.reusable_existing(ollama.DEFAULT_ENDPOINT)):
        raise RuntimeError('Existing verified local model/runtime required; no download performed')
    return {'runtime':state['version'],'digest':model['digest'],'model':ollama.MODEL,
            'runtime_matches_linux_qa':state['version']=='0.40.18'}

def run_comparison(path,parent,consent,*,cpu_only=False,claim_reuse=False):
    if consent!=CONSENT:raise ValueError('Explicit local-processing consent required')
    p,data,transcript,baseline,old,mode,language,blocks,plan=read_input(path)
    if claim_reuse:
        from engine.minutes_claim_frozen import frozen_extraction
        frozen_extraction(old,blocks,language)
    root=validate_local_folder(safe_path(parent))
    if not root.is_dir():raise ValueError('Select an existing internal output folder')
    server=verify_model()
    before=hash_file(p)
    # New unique folder only; never write to the existing project or extract input.
    from tempfile import mkdtemp
    out=Path(mkdtemp(prefix='MeetingSplit-claim-QA-' if claim_reuse else 'MeetingSplit-contextual-QA-',dir=root))
    cancel=Cancellation()
    timer=threading.Timer(WALL_CAP,cancel.cancel);timer.daemon=True
    started=time.monotonic();calls=[];evidence={}
    original=summarize.ollama_chat
    call_cap=16 if claim_reuse else CALL_CAP
    last={}
    def record_stage(event):
        if event['event']=='request':
            last.clear();last.update(stage=event['stage'])
            if event['stage']=='contextual_claim_editorial':last['window']=event['scope']['window']
    def progress(message):
        if claim_reuse and ('contexto temático' in message or 'Traduciendo descripciones' in message):
            print(message,flush=True,file=sys.stderr)
    def bounded(messages,model,**kwargs):
        cancel.check()
        remaining=WALL_CAP-(time.monotonic()-started)
        if len(calls)>=call_cap or remaining<1:raise BudgetExceeded('Local QA call/time budget exhausted')
        if model!=ollama.MODEL or kwargs.get('endpoint')!=ollama.DEFAULT_ENDPOINT:
            raise ValueError('Unexpected model or endpoint')
        kwargs.update(timeout=min(PER_CALL,remaining),cancel=cancel,
                      cpu_only=bool(cpu_only or kwargs.get('cpu_only')))
        if claim_reuse and last.get('stage') not in ('contextual_claim_editorial','localization'):
            raise BudgetExceeded('Unexpected extraction or other request in frozen QA')
        entry={'cpu_only':kwargs['cpu_only'],**(last if claim_reuse else {})};calls.append(entry)
        t=time.monotonic()
        try:return original(messages,model,**kwargs)
        except Exception as exc:
            entry['error_type']=type(exc).__name__;raise
        finally:entry['seconds']=round(time.monotonic()-t,3)
    result={'scope':'private local transcript-only contextual QA, not production release',
            'completed':False,'mode':mode,'language':language,'server':server,
            'baseline':metrics(baseline,old),'call_cap':call_cap,
            **({'strategy':'contextual_claim_qa','extraction_reused':True,'reused_extraction_records':len(old['items'])} if claim_reuse else {}),'wall_cap_seconds':WALL_CAP,
            'per_call_cap_seconds':PER_CALL,'semantic_acceptance':False}
    try:
        timer.start()
        with patch.object(summarize,'ollama_chat',bounded):
            report=summarize.summarize_local(transcript,mode,language,ollama.MODEL,
                endpoint=ollama.DEFAULT_ENDPOINT,cancel=cancel,narrative_strategy='contextual_claim_qa' if claim_reuse else 'contextual_qa',
                evidence_sink=evidence.update,progress=progress,
                **({'qa_frozen_extraction':old,'qa_trace':record_stage} if claim_reuse else {}))
        cancel.check()
        result['candidate']=metrics(report,evidence)
        if claim_reuse:
            diag=evidence['context_diagnostics']
            result['candidate'].update(claims=sum(len(t['claims']) for t in evidence['editorial_themes']),
                context_windows=diag['window_count'],windows_without_themes=sum(not w['accepted_themes'] for w in diag['windows']),
                rejections=sum(len(w['rejections']) for w in diag['windows']),
                quote_repairs=sum(len(w['quote_repairs']) for w in diag['windows']),
                structured_period_repairs=len(diag['structured_period_repairs']))
            result['thematic_output_present']=bool(evidence['editorial_themes'])
        (out/'CANDIDATO_CONTEXTUAL.md').write_text(report,encoding='utf-8')
        (out/'CANDIDATO_EVIDENCIAS.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        result['completed']=True
    except KeyboardInterrupt:
        cancel.cancel();result['error_type']='KeyboardInterrupt'
    except Exception as exc:
        # No exception string or raw prompt/response in the aggregate diagnostic.
        result['error_type']=type(exc).__name__
    finally:
        timer.cancel()
        result.update(requests=len(calls),calls=calls,seconds=round(time.monotonic()-started,3),
                      original_zip_unchanged=hash_file(p)==before)
        if not result['original_zip_unchanged']:result['completed']=False
        (out/'COMPARACION_TECNICA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return out,result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results_zip',type=Path)
    parser.add_argument('--run-local',action='store_true')
    parser.add_argument('--output-parent',type=Path)
    parser.add_argument('--consent')
    parser.add_argument('--cpu-only',action='store_true')
    parser.add_argument('--claim-reuse',action='store_true',help='Compare claim-local synthesis using original extraction ledger')
    a=parser.parse_args(argv)
    try:
        if not a.run_local:
            if a.output_parent or a.consent or a.cpu_only:parser.error('Live options require --run-local')
            print(json.dumps(inspect(a.results_zip,claim_reuse=a.claim_reuse),ensure_ascii=True,indent=2));return 0
        if not a.output_parent or a.consent!=CONSENT:
            parser.error('Live comparison requires --output-parent and --consent '+CONSENT)
        out,result=run_comparison(a.results_zip,a.output_parent,a.consent,cpu_only=a.cpu_only,claim_reuse=a.claim_reuse)
        print(json.dumps({'output_folder':str(out),'completed':result['completed'],
                          'requests':result['requests'],'error_type':result.get('error_type')},ensure_ascii=True))
        return 0 if result['completed'] else 2
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,BadZipFile) as exc:
        print('QA blocked: '+type(exc).__name__,file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
