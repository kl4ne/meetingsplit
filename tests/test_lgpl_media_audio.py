"""QA regression: the LGPL media replacement must keep every user export format."""
from __future__ import annotations
import math
from pathlib import Path
import shutil
import struct
import wave
import pytest

from engine.audio import probe, export_clip
from engine.planning import Clip


def test_mp3_m4a_wav_outputs_and_pyav_decode(tmp_path):
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg is not available on this platform')
    try:
        from faster_whisper.audio import decode_audio
    except ImportError:
        pytest.skip('Faster-Whisper/PyAV not installed in this local check')
    source=tmp_path/'synthetic.wav'
    rate=16000
    with wave.open(str(source),'wb') as wav:
        wav.setparams((1,2,rate,0,'NONE','not compressed'))
        wav.writeframes(b''.join(struct.pack('<h',int(10000*math.sin(2*math.pi*440*i/rate)))
                                 for i in range(rate*2)))
    for fmt in ('mp3','m4a','wav'):
        out=tmp_path/f'clip.{fmt}'
        meta=export_clip(source,out,Clip(1,0,2,0,2),fmt)
        assert out.is_file() and out.stat().st_size > 100
        assert meta['duration']>1.8
        assert abs(probe(out)-2.0)<.2
        samples=decode_audio(str(out),sampling_rate=16000)
        assert len(samples) >= 30000
        assert float(abs(samples).max()) > .02