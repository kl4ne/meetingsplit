"""Disk-streamed audio inspection, silence scanning and loss-conscious export."""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tempfile
from .control import Cancellation, JobCancelled
from .planning import Clip


def bundled_exe(name: str) -> str:
    ext='.exe' if os.name=='nt' else ''
    root=Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    for cand in (root/'bin'/f'{name}{ext}',root/f'{name}{ext}'):
        if cand.is_file():
            return str(cand)
    found=shutil.which(name)
    if found:
        return found
    raise FileNotFoundError(f'No se encontró {name}. Instala FFmpeg o colócalo en bin/.')


def _run(args: list[str], *, timeout: int|None=None, cancel: Cancellation|None=None) -> subprocess.CompletedProcess:
    """Run FFmpeg with disk-backed stdio, avoiding pipe deadlock on long recordings."""
    flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process=subprocess.Popen(args,stdout=stdout,stderr=stderr,**flags)
        start=time.monotonic()
        try:
            while process.poll() is None:
                if cancel: cancel.check()
                if timeout and time.monotonic()-start > timeout:
                    raise TimeoutError('FFmpeg excedió el tiempo máximo de espera')
                time.sleep(.1)
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait()
            raise
        stdout.seek(0);stderr.seek(0)
        result=subprocess.CompletedProcess(args,process.returncode,
                     stdout.read().decode('utf-8','replace'),
                     stderr.read().decode('utf-8','replace'))
        if result.returncode:
            raise RuntimeError(f"Fallo en FFmpeg: {(result.stderr or result.stdout)[-1600:]}")
        return result


def _probe_data(path: Path) -> dict:
    args=[bundled_exe('ffprobe'),'-v','error','-select_streams','a:0',
          '-show_entries','stream=index,duration,start_time:format=duration,start_time','-of','json',str(path)]
    return json.loads(_run(args,timeout=75).stdout)


def probe(path: Path) -> float:
    data=_probe_data(path)
    streams=data.get('streams',[])
    if not streams:
        raise ValueError('El archivo no contiene una pista de audio.')
    duration=streams[0].get('duration')
    if duration in (None, 'N/A'):
        duration=data.get('format',{}).get('duration','0')
    seconds=float(duration)
    if not math.isfinite(seconds) or seconds<=0 or seconds>24*3600:
        raise ValueError('Audio sin duración válida')
    return seconds


def audio_start_offset(path: Path) -> float:
    data=_probe_data(path)
    audio=data['streams'][0]
    def time_or_zero(value):
        stamp=float(value) if value not in (None,'N/A') else 0.
        return stamp if math.isfinite(stamp) else 0.
    return max(0.,time_or_zero(audio.get('start_time'))-
               time_or_zero(data.get('format',{}).get('start_time')))


def detect_silences(path: Path, threshold_db: int=-35, minimum_s: float=.65, cancel: Cancellation|None=None) -> list[tuple[float,float]]:
    cmd=[bundled_exe('ffmpeg'),'-hide_banner','-nostdin','-i',str(path),
         '-map','0:a:0','-vn','-af',f'asetpts=PTS-STARTPTS,silencedetect=noise={threshold_db}dB:d={minimum_s}',
         '-f','null','NUL' if os.name=='nt' else '/dev/null']
    p=_run(cmd,cancel=cancel)
    # Parse chronological start/end events; ignore unmatched final silence.
    # Match events in temporal order; end-of-file silence without end isn't used.
    events=re.findall(r'silence_(start|end):\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)',p.stderr)
    ranges=[]
    active=None
    for kind,value in events:
        if kind=='start': active=float(value)
        elif active is not None:
            end=float(value)
            if end>active: ranges.append((active,end))
            active=None
    return ranges


CODEC={
    'mp3': ['-ar','24000','-ac','1','-c:a','libmp3lame','-b:a','48k','-f','mp3'],
    'm4a': ['-ar','24000','-ac','1','-c:a','aac','-b:a','64k','-f','ipod'],
    'wav': ['-ar','16000','-ac','1','-c:a','pcm_s16le','-f','wav'],
}


def export_clip(source: Path, destination: Path, clip: Clip, fmt: str,
                cancel: Cancellation|None=None, *, source_offset: float=0.) -> dict:
    if fmt not in CODEC: raise ValueError('Formato no compatible')
    temp=destination.with_suffix(destination.suffix+'.partial')
    if temp.exists(): temp.unlink()
    cmd=[bundled_exe('ffmpeg'),'-hide_banner','-nostdin','-y',
         '-ss',f'{source_offset+clip.export_start:.6f}','-i',str(source),
         '-t',f'{clip.export_end-clip.export_start:.6f}',
         '-map','0:a:0','-vn',*CODEC[fmt],str(temp)]
    try:
        _run(cmd,cancel=cancel)
        recorded=probe(temp)
        expected=clip.export_end-clip.export_start
        if abs(recorded-expected)>max(0.5,expected*0.001):
            raise RuntimeError(f'Duración generada distinta ({recorded:.2f} vs {expected:.2f}s)')
        if destination.exists(): raise FileExistsError(str(destination))
        temp.replace(destination)
        return {'file':destination.name,'bytes':destination.stat().st_size,
                'duration':round(recorded,3)}
    finally:
        temp.unlink(missing_ok=True)
