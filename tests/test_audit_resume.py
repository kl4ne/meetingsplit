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


def test_job_lock_blocks_second_instance(tmp_path):
    with job._job_lock(tmp_path):
        with pytest.raises(RuntimeError,match='already in use'):
            with job._job_lock(tmp_path):
                pytest.fail('second writer acquired lock')
    with job._job_lock(tmp_path):
        pass


def test_atomic_result_write_does_not_modify_hardlinked_original(tmp_path):
    import os
    original=tmp_path/'original.txt'
    original.write_text('original')
    result=tmp_path/'result.txt'
    os.link(original,result)
    job._write_text(result,'updated')
    assert original.read_text()=='original'
    assert result.read_text()=='updated'


def test_source_change_during_export_is_not_checkpointed(tmp_path,monkeypatch):
    source=tmp_path/'source.wav'
    source.write_bytes(b'original')
    monkeypatch.setattr(job,'validate_local_folder',lambda p:Path(p).resolve(strict=True))
    monkeypatch.setattr(job,'probe',lambda p:600)
    monkeypatch.setattr(job,'detect_silences',lambda *a,**k:[])
    monkeypatch.setattr(job.shutil,'disk_usage',lambda p:SimpleNamespace(free=10*1024**3))
    def export(src,dest,clip,fmt,cancel):
        dest.write_bytes(b'not verified')
        src.write_bytes(b'changed during export')
        return {'file':dest.name}
    monkeypatch.setattr(job,'export_clip',export)
    with pytest.raises(ValueError,match='changed during processing'):
        job.run_job({'file':str(source),'output':str(tmp_path),'action':'split','minutes':5},lambda *a:None)
    manifest=json.loads((next(tmp_path.glob('MeetingSplit-*'))/'manifest.json').read_text())
    assert manifest['status']=='failed' and manifest['exports']==[]
