import os
from pathlib import Path
import subprocess
import shutil
import pytest
from engine.audio import probe,detect_silences,export_clip
from engine.planning import Clip


@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg necesario')
def test_ffmpeg_file_and_export(tmp_path):
    source=tmp_path/'voz_prueba.wav'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=400:duration=5',
                    '-ac','1','-ar','24000',str(source)],check=True)
    assert abs(probe(source)-5)<.1
    clip=Clip(1,0,5,0,5)
    out=tmp_path/'parte01.mp3'
    meta=export_clip(source,out,clip,'mp3')
    assert out.is_file() and meta['bytes']>0
    assert abs(probe(out)-5)<.1

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg necesario')
def test_detect_tone_silence_tone(tmp_path):
    source=tmp_path/'pausas.wav'
    # Produce 1s tone, 1s silence and 1s tone by concat. Does not contain speech.
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',
       'sine=frequency=400:duration=1','-f','lavfi','-i',
       'anullsrc=channel_layout=mono:sample_rate=24000:d=1',
       '-f','lavfi','-i','sine=frequency=400:duration=1',
       '-filter_complex','[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]',
       '-map','[a]','-t','3',str(source)],check=True)
    silences=detect_silences(source)
    assert silences and .9<=silences[0][0]<=1.2 and 1.85<=silences[0][1]<=2.1
