from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from engine import job
from engine.control import Cancellation,JobCancelled


def test_resume_reuses_verified_clip_and_rejects_other_source(tmp_path,monkeypatch):
    source=tmp_path/'source.wav'
    source.write_bytes(b'original')
    monkeypatch.setattr(job,'validate_local_folder',lambda p:Path(p).resolve(strict=True))
    monkeypatch.setattr(job,'probe',lambda p:600)
    monkeypatch.setattr(job,'detect_silences',lambda *a,**k:[])
    monkeypatch.setattr(job.shutil,'disk_usage',lambda p:SimpleNamespace(free=10*1024**3))
    calls=[]
    task=Cancellation()
    def export(src,dest,clip,fmt,cancel):
        calls.append(clip.number)
        dest.write_bytes(str(clip.number).encode())
        return {'file':dest.name,'bytes':dest.stat().st_size,'duration':clip.export_end-clip.export_start}
    monkeypatch.setattr(job,'export_clip',export)
    conf={'file':str(source),'output':str(tmp_path),'action':'split','minutes':5,'zip_output':False}
    def progress(message,pct):
        if 'Exportando audio 2' in message:
            task.cancel()
            task.check()
    with pytest.raises(JobCancelled):
        job.run_job(conf,progress,task)
    folder=next(tmp_path.glob('MeetingSplit-*'))
    assert calls==[1]
    conf['resume_folder']=str(folder)
    source.write_bytes(b'changed')
    with pytest.raises(ValueError,match='same recording'):
        job.run_job(conf,lambda *a:None)
    source.write_bytes(b'original')
    result=job.run_job(conf,lambda *a:None)
    assert result==folder and calls.count(1)==1
    assert json.loads((folder/'manifest.json').read_text())['status']=='complete'
