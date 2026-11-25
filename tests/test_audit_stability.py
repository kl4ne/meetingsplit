"""Regression tests for audit repairs; no network or GPU required."""
import json
from types import SimpleNamespace
import pytest
from engine import audio, job
from engine.planning import Clip
from engine.output import pack_result
from engine.control import Cancellation, JobCancelled


@pytest.mark.parametrize('duration',['nan','inf','-inf'])
def test_probe_rejects_nonfinite_duration(monkeypatch,duration,tmp_path):
    monkeypatch.setattr(audio,'bundled_exe',lambda name:name)
    monkeypatch.setattr(audio,'_run',lambda *a,**k:SimpleNamespace(stdout=json.dumps({'format':{'duration':duration}})))
    with pytest.raises(ValueError):
        audio.probe(tmp_path/'input.wav')


def test_zip_space_budget_counts_second_copy():
    clips=[Clip(1,0,600,0,600)]
    plain=job._estimated_output_bytes(clips,'wav',True,False)
    packed=job._estimated_output_bytes(clips,'wav',True,True)
    assert packed-plain >= 600*32000


def test_low_disk_rejected(monkeypatch,tmp_path):
    monkeypatch.setattr(job.shutil,'disk_usage',lambda path:SimpleNamespace(free=1))
    with pytest.raises(OSError,match='Insufficient disk space'):
        job._check_space(tmp_path,2)


def test_zip_cancel_during_file_preserves_no_partial(tmp_path):
    (tmp_path/'audio.wav').write_bytes(b'x'*(2*1024*1024))
    class Stop(Cancellation):
        def __init__(self): super().__init__(); self.calls=0
        def check(self):
            self.calls+=1
            if self.calls>=3: self.cancel()
            super().check()
    with pytest.raises(JobCancelled):
        pack_result(tmp_path,tmp_path/'result.zip',Stop())
    assert not (tmp_path/'result.zip').exists()
    assert not (tmp_path/'result.zip.partial').exists()
