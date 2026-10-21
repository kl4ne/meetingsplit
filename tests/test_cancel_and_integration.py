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
def test_export_transcript_srt_zip_integration(monkeypatch,tmp_path):
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
          'report':'both','report_language':'both','zip_output':True,'local_summary':False}
    progress=[]
    folder=run_job(conf,lambda message,pct:progress.append((message,pct)))
    manifest=json.loads((folder/'manifest.json').read_text())
    assert manifest['status']=='complete'
    assert manifest['transcription_segments']==1
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
