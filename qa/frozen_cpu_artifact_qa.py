"""Disposable runner only: actual frozen CPU inference using synthetic speech."""
import hashlib,json,os,subprocess,sys,tempfile,time,wave
from pathlib import Path
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='kl4ne/meetingsplit':
    raise SystemExit('CI only')
exe=Path(sys.argv[1]).resolve(strict=True)
audio=Path(sys.argv[2]).resolve(strict=True)
output=Path(sys.argv[3]).resolve()
report={'candidate':'b48f7e190c5418ba0a34d91aacc0c80a0ccc37b2','portable_artifact_id':14997442379,'synthetic_only':True,'ok':False,'stages':[]}
def save():
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
save()
with tempfile.TemporaryDirectory(prefix='ms-frozen-qa-') as temp:
    root=Path(temp)
    ipc=root/'ipc';ipc.mkdir()
    log=(root/'worker.log').open('wb')
    worker=subprocess.Popen([str(exe),'--inference-worker',str(ipc),str(os.getpid())],stdin=subprocess.DEVNULL,stdout=log,stderr=log)
    def call(command,timeout):
        staging=ipc/'request.tmp'
        staging.write_text(json.dumps(command),encoding='utf-8')
        staging.replace(ipc/'request.json')
        response=ipc/'response.json'
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            if response.is_file():
                result=json.loads(response.read_text(encoding='utf-8'));response.unlink()
                if not result.get('ok'):raise RuntimeError(result.get('error','Worker error'))
                return result
            if worker.poll() is not None:raise RuntimeError(f'Worker exited {worker.returncode}')
            time.sleep(.2)
        raise TimeoutError('Frozen worker timeout: '+command['op'])
    try:
        ping=call({'op':'ping'},45)
        assert ping['protocol']==1
        report['stages'].append({'stage':'frozen_ipc','passed':True});save()
        started=time.monotonic()
        result=call({'op':'load','cache':str(root/'models'),'model':'small','cpu':True,'preserve_quality':True},900)
        assert result['device']=='CPU'
        report['stages'].append({'stage':'real_cpu_model_load','device':result['device'],'seconds':round(time.monotonic()-started,2)});save()
        with wave.open(str(audio),'rb') as wav: duration=wav.getnframes()/wav.getframerate()
        started=time.monotonic()
        rows=call({'op':'clip','clip':{'number':1,'core_start':0,'core_end':duration,'export_start':0,'export_end':duration},'path':str(audio),'language':'en','preserve_quality':True},300)['rows']
        text=' '.join(r['text'] for r in rows).lower()
        matches=[word for word in ('meeting','budget','friday','report') if word in text]
        report['stages'].append({'stage':'real_cpu_speech','seconds':round(time.monotonic()-started,2),'rows':rows,'matched_keywords':matches})
        if len(matches)<3:raise RuntimeError('Synthetic speech accuracy smoke threshold not met')
        report['ok']=True
    except Exception as exc:
        report['error']=str(exc)[:700]
        raise
    finally:
        (ipc/'stop').touch()
        try:worker.wait(timeout=8)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(worker.pid),'/T','/F'],capture_output=True,timeout=10)
            worker.wait(timeout=10)
        log.close()
        report['worker_exited']=worker.poll() is not None
        save()
