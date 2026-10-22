from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile
import pytest
from engine.audio import _run, probe
from engine.control import Cancellation, JobCancelled
from engine.job import run_job


@pytest.fixture(autouse=True)
def _accept_ephemeral_ci_test_directory(monkeypatch):
    # Windows GitHub runners use VIRTUAL disks. Production deliberately rejects
    # them; engine tests instead use a trusted pytest-only temporary folder.
    # Never weaken real desktop.storage.validate_local_folder for customers.
    import engine.job as job
    monkeypatch.setattr(job, 'validate_local_folder',
                        lambda folder: Path(folder).resolve(strict=True))


def test_long_stderr_never_deadlocks():
    # More stderr than a typical anonymous OS pipe can hold.
    p=_run([sys.executable,'-c','import sys; sys.stderr.write("A"*450000)'],timeout=12)
    assert len(p.stderr)==450000


def test_can_cancel_long_subprocess(tmp_path):
    from threading import Timer
    control=Cancellation()
    timer=Timer(.18,control.cancel)
    timer.start()
    try:
        with pytest.raises(JobCancelled):
            _run([sys.executable,'-c','import time;time.sleep(20)'],cancel=control)
    finally:timer.join()


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='requires FFmpeg')
@pytest.mark.parametrize('fail_optional_summary',[False,True])
def test_export_transcript_srt_zip_integration(monkeypatch,tmp_path,fail_optional_summary):
    import engine.job as job
    source=tmp_path/'bilingue.wav'
    # 6 seconds of tone, 1.5 seconds of silence, then tone. No network.
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
       '-f','lavfi','-i','sine=frequency=550:duration=6',
       '-f','lavfi','-i','anullsrc=channel_layout=mono:sample_rate=16000',
       '-f','lavfi','-i','sine=frequency=760:duration=6',
       '-filter_complex','[0:a]aresample=16000[a];[1:a]atrim=duration=1.5[b];[2:a]aresample=16000[c];[a][b][c]concat=n=3:v=0:a=1[d]',
       '-map','[d]','-c:a','pcm_s16le',str(source)],check=True,timeout=20)
    monkeypatch.setattr(job,'load_whisper',lambda *args,**kwargs:(object(),'CPU de prueba'))
    def fake_transcribe(model,clip,path,*,language,cancel):
        return [{'start':0.2,'end':1.2,'text':'Hola, welcome.','part':clip.number}]
    monkeypatch.setattr(job,'transcribe_clip',fake_transcribe)
    conf={'file':str(source),'output':str(tmp_path),'action':'both','format':'mp3',
          'minutes':5,'overlap':20,'model':'small','input_language':'auto',
          'report':'both','report_language':'both','zip_output':True,'local_summary':fail_optional_summary}
    if fail_optional_summary:
        class UnavailableLocalService:
            def __init__(self,*args,**kwargs): pass
            def __enter__(self): raise TimeoutError('Simulated local model timeout')
            def __exit__(self,*args): pass
        monkeypatch.setattr('engine.ollama.LocalService',UnavailableLocalService)
    progress=[]
    folder=run_job(conf,lambda message,pct:progress.append((message,pct)))
    manifest=json.loads((folder/'manifest.json').read_text())
    assert manifest['status']=='complete'
    assert manifest['transcription_segments']==1
    if fail_optional_summary:
        assert manifest['summary_status']=='failed'
        assert (folder/'MINUTA_NO_GENERADA.txt').is_file()
        assert not (folder/'RESUMEN_Y_MINUTA_LOCAL.md').exists()
    assert manifest['exports'][0]['duration']>13.0
    assert probe(folder/'parte_01.mp3')>13.0
    assert 'Hola, welcome.' in (folder/'TRANSCRIPCION_COMPLETA.txt').read_text()
    assert '00:00:00,200 --> 00:00:01,200' in (folder/'TRANSCRIPCION_SUBTITULOS.srt').read_text()
    with ZipFile(folder/'RESULTADOS_COMPLETOS.zip') as z:
        assert {'parte_01.mp3','TRANSCRIPCION_COMPLETA.txt','TRANSCRIPCION_SUBTITULOS.srt','manifest.json'}.issubset(z.namelist())
    assert progress[-1][1]==100


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),reason='requires FFmpeg')
def test_cancelled_job_records_status(monkeypatch,tmp_path):
    source=tmp_path/'stop.wav'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                    '-i','sine=duration=5','-ac','1',str(source)],check=True,timeout=12)
    control=Cancellation()
    def progress(msg,pct):
        if 'Analizando silencios' in msg:control.cancel()
    with pytest.raises(JobCancelled):
        run_job({'file':str(source),'output':str(tmp_path),'action':'split'},progress,control)
    project=next(tmp_path.glob('MeetingSplit-*'))
    manifest=json.loads((project/'manifest.json').read_text())
    assert manifest['status']=='cancelled'
    assert source.exists()


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='requires FFmpeg')
def test_cpu_only_transcription_does_not_reinit_cuda_on_runtime_failure(monkeypatch,tmp_path):
    import engine.job as job
    source=tmp_path/'cpu_only.wav'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                    '-i','sine=duration=2','-ac','1',str(source)],check=True,timeout=15)
    cpu=object()
    monkeypatch.setattr(job,'load_whisper',lambda *args,**kwargs:(cpu,'CPU'))
    monkeypatch.setattr(job,'load_cpu_whisper',
                        lambda *args,**kwargs:pytest.fail('CPU model must not be reloaded as a GPU fallback'))
    def synthetic_cuda_error(*args,**kwargs):
        raise RuntimeError('Synthetic CUDA library error while deliberately using CPU')
    monkeypatch.setattr(job,'transcribe_clip',synthetic_cuda_error)
    config={'file':str(source),'output':str(tmp_path),'action':'both',
            'format':'mp3','minutes':5,'model':'small','overlap':20,'zip_output':False}
    with pytest.raises(RuntimeError,match='Synthetic CUDA'):
        job.run_job(config,lambda *args:None)
    project=next(tmp_path.glob('MeetingSplit-*'))
    state=json.loads((project/'manifest.json').read_text())
    assert state['device']=='CPU'
    assert state['execution_policy']=='CPU_ONLY'
    assert state['status']=='failed'


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='requires FFmpeg')
def test_non_cuda_transcription_error_is_not_hidden_by_cpu_fallback(monkeypatch,tmp_path):
    import engine.job as job
    source=tmp_path/'invalid_audio_handling.wav'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi',
                    '-i','sine=duration=2','-ac','1',str(source)],check=True,timeout=15)
    monkeypatch.setattr(job,'load_whisper',lambda *args,**kwargs:(object(),'CPU'))
    monkeypatch.setattr(job,'load_cpu_whisper',lambda *args,**kwargs:pytest.fail('Should not use CPU'))
    def fail(*args,**kwargs):
        raise ValueError('Source audio is invalid')
    monkeypatch.setattr(job,'transcribe_clip',fail)
    with pytest.raises(ValueError,match='Source audio is invalid'):
        run_job({'file':str(source),'output':str(tmp_path),'action':'transcribe',
                 'minutes':5,'model':'small','overlap':20},lambda *args:None)
