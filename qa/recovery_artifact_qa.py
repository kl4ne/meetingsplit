"""QA-only source orchestration with the exact compiled worker and FFmpeg.
The storage override is confined to the disposable runner's test directory.
Never modifies the production source or processes a personal recording.
"""
import hashlib,json,os,subprocess,sys,time,threading
from pathlib import Path
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='kl4ne/meetingsplit':
    raise SystemExit('CI only')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import job,audio
from engine.control import Cancellation,JobCancelled
from engine.inference_worker import InferenceWorker
exe=Path(sys.argv[1]).resolve(strict=True)
root=Path(sys.argv[2]).resolve(strict=True)
out=root/'recovery-report.json'
source=root/'synthetic.wav'
data=root/'data';data.mkdir()
report={'candidate':'b48f7e190c5418ba0a34d91aacc0c80a0ccc37b2','portable_artifact_id':14997442379,'scope':'source orchestration with exact frozen worker and FFmpeg; synthetic speech; CI-only storage override','ok':False,'stages':[]}
def save():
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def confined(path):
    p=Path(path).resolve(strict=True)
    if not p.is_dir() or not p.is_relative_to(data):raise ValueError('Outside test data directory')
    return p
job.validate_local_folder=confined
def bundled(name):
    p=exe.parent/'_internal'/'bin'/(name+'.exe')
    if not p.is_file():raise FileNotFoundError(p)
    return str(p)
audio.bundled_exe=bundled
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original_sha=sha(source)
class FrozenWorker(InferenceWorker):
    def __init__(self,folder,cache,cancel,preserve_quality=False):
        import tempfile
        self.temp=tempfile.TemporaryDirectory(prefix='.inference-',dir=folder)
        self.root=Path(self.temp.name);self.cancel=cancel;self.cache=cache
        self.preserve_quality=preserve_quality
        self.process=subprocess.Popen([str(exe),'--inference-worker',str(self.root),str(os.getpid())],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def load(self,model,cpu=False):
        # Force CPU on runner, which has no NVIDIA hardware.
        return super().load(model,cpu=True)
job.InferenceWorker=FrozenWorker
save()
try:
    # Six minutes with speech at the beginning and end, silence between.
    # Silence keeps real CPU decoding workload manageable.
    long_audio=root/'synthetic-long.wav'
    subprocess.run([bundled('ffmpeg'),'-y','-v','error','-i',str(source),'-f','lavfi','-i','anullsrc=r=16000:cl=mono','-i',str(source),'-filter_complex','[0:a]aresample=16000,aformat=channel_layouts=mono[a];[1:a]atrim=duration=310[b];[2:a]aresample=16000,aformat=channel_layouts=mono[c];[a][b][c]concat=n=3:v=0:a=1[out]','-map','[out]',str(long_audio)],check=True,timeout=60)
    long_sha=sha(long_audio)
    conf={'file':str(long_audio),'output':str(data),'action':'both','format':'mp3','minutes':5,'overlap':10,'model':'small','input_language':'en','report':'both','report_language':'both','zip_output':True,'local_summary':False,'isolated_inference':True,'preserve_cpu_quality':True}
    task=Cancellation()
    def progress(msg,pct):
        print(pct,msg,flush=True)
        if msg.startswith('Exportando audio 2 de'):task.cancel()
    try:job.run_job(conf,progress,task)
    except JobCancelled:pass
    else:raise AssertionError('Expected deliberate cancellation')
    folder=next(data.glob('MeetingSplit-*'))
    before=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    assert before['status']=='cancelled' and '1' in before['checkpoints'] and len(before['exports'])==1
    checkpoint=folder/'transcripcion_parte_01.json'; exported=folder/'parte_01.mp3'
    hashes={p.name:sha(p) for p in (checkpoint,exported)}
    report['stages'].append({'stage':'cancel_after_completed_clip','passed':True,'preserved_hashes':hashes});save()
    conf['resume_folder']=str(folder)
    resumed=job.run_job(conf,lambda msg,pct:print(pct,msg,flush=True))
    assert resumed==folder
    after=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    assert after['status']=='complete' and after['device']=='CPU'
    assert len(after['checkpoints'])==len(after['clips'])>=2
    assert {p.name:sha(p) for p in (checkpoint,exported)}==hashes
    assert sha(source)==original_sha and sha(long_audio)==long_sha
    import zipfile
    with zipfile.ZipFile(folder/'RESULTADOS_COMPLETOS.zip') as z:
        assert z.testzip() is None
        assert 'TRANSCRIPCION_COMPLETA.txt' in z.namelist()
    report['stages'].append({'stage':'resume_verified_clip','passed':True,'clip_count':len(after['clips']),'segments':after['transcription_segments'],'zip_valid':True,'original_unchanged':True});report['ok']=True
except Exception as exc:
    report['error']=str(exc)[:1000];raise
finally:save()
