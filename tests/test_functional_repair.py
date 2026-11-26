"""Synthetic regressions for media, transcription boundaries and minutes recovery."""
import hashlib
import json
import shutil
import subprocess
from types import SimpleNamespace
import wave
from zipfile import ZipFile

import pytest

from engine import job, summarize
from engine.audio import probe
from engine.control import Cancellation, JobCancelled
from engine.minutes_evidence import find_coverage_gaps, source_blocks, validate_items
from engine.planning import Clip
from engine.transcription import transcribe_clip


def read_manifest(folder):
    return json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))


def run_split(source, output, **settings):
    config = {'file': str(source), 'output': str(output), 'action': 'split',
              'format': 'wav', 'zip_output': False}
    return job.run_job(config | settings, lambda *_: None)


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg required')
def test_submillisecond_wav_duration_keeps_coverage_and_original(tmp_path):
    source = tmp_path / 'fractional.wav'
    with wave.open(str(source), 'wb') as out:
        out.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        out.writeframes(b'\0\0' * 40012)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    result = run_split(source, tmp_path, local_summary=True)
    manifest = read_manifest(result)
    assert manifest['status'] == 'complete'
    assert manifest['summary_status'] == 'excluded'
    assert manifest['clips'][-1]['core_end'] == pytest.approx(2.500750)
    with wave.open(str(result / 'parte_01.wav')) as part:
        assert part.getnframes() == 40012
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg required')
@pytest.mark.parametrize('offset', [0, 1])
def test_mp4_uses_first_audio_stream_instead_of_video_duration(tmp_path, offset):
    # At 48 kHz an AAC frame is about 21 ms. Keep the same assertion across FFmpeg muxer versions.
    source = tmp_path / 'sample.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                    'color=size=32x32:rate=5:duration=3', '-itsoffset', str(offset), '-f', 'lavfi', '-i',
                    'sine=frequency=400:sample_rate=48000:duration=1.5',
                    '-c:v', 'mpeg4', '-c:a', 'aac', str(source)], check=True)
    original = source.read_bytes()
    result = run_split(source, tmp_path)
    duration = probe(source)
    assert duration == pytest.approx(1.5, abs=.07)
    assert read_manifest(result)['duration_seconds'] == pytest.approx(duration, abs=.001)
    assert probe(result / 'parte_01.wav') == pytest.approx(duration, abs=.05)
    assert source.read_bytes() == original


def response(rows):
    return json.dumps({'items': [
        {'category': 'decision', 'sources': [{'id': row['id'], 'quote': row['text']}],
         'owner': None, 'due': None, 'text_es': 'Acuerdo de presupuesto.',
         'text_en': 'Budget decision.'} for row in rows
    ]})


def test_bilingual_coverage_reports_both_gaps_and_rejects_invented_numbers():
    rows = next(source_blocks('[00:04:12] Se aprobó el presupuesto de $1,250.50.'))
    assert {(gap['kind'], gap['text']) for gap in find_coverage_gaps(rows, [])} == {
        ('agreement', 'Se aprobó'), ('amount', '$1,250.50')
    }
    assert not find_coverage_gaps(rows, validate_items(response(rows), rows, 'both'))
    changed = json.loads(response(rows))
    changed['items'][0]['text_en'] = 'Approved $1,520.50.'
    with pytest.raises(ValueError, match='Numeric claims'):
        validate_items(json.dumps(changed), rows, 'both')
    changed['items'][0]['text_en'] = 'Approved EUR 1,250.50.'
    with pytest.raises(ValueError, match='Monetary units'):
        validate_items(json.dumps(changed), rows, 'both')


def test_truncated_quote_does_not_turn_rejected_proposal_into_decision():
    rows = next(source_blocks('[00:00:10] The budget was not approved.'))
    changed = json.loads(response(rows))
    changed['items'][0]['sources'][0]['quote'] = 'approved'
    with pytest.raises(ValueError, match='negated agreement'):
        validate_items(json.dumps(changed), rows, 'both')


def test_minutes_retries_only_failed_block_using_verified_transcript(tmp_path, monkeypatch):
    import engine.ollama

    class Service:
        endpoint = 'mock'
        def __init__(self, *args):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def ensure_model(self):
            pass

    folder = tmp_path / 'MeetingSplit-synthetic'
    folder.mkdir()
    phrases = ['Se aprobó $100. ', 'It was agreed to spend US$200. ', 'Se acordó invertir 300 pesos. ']
    rows = [{'start': i * 90, 'end': i * 90 + 1, 'text': phrase + 'x' * 1690}
            for i, phrase in enumerate(phrases)]
    checkpoint = folder / 'transcripcion_parte_01.json'
    job._write_json(checkpoint, {'segments': rows})
    manifest = {'status': 'complete', 'summary_status': 'failed',
                'clips': [{'number': 1}],
                'checkpoints': {'1': job._sha256(checkpoint, Cancellation())},
                'resume_signature': {'settings': {'action': 'both', 'language': 'both',
                    'report': 'both', 'local_summary': True, 'zip_output': True}}}
    job._write_json(folder / 'manifest.json', manifest)
    monkeypatch.setattr(engine.ollama, 'LocalService', Service)
    calls = []
    fail = True
    cancel = Cancellation()

    def fake_chat(messages, *_args, **_kwargs):
        source = json.loads(messages[1]['content'])['source_rows']
        calls.append([row['id'] for row in source])
        if fail and any(row['id'] == 3 for row in source):
            return 'invalid'
        return response(source)

    monkeypatch.setattr(summarize, 'ollama_chat', fake_chat)
    def stop_before_extraction(_message, _pct):
        cancel.cancel()

    with pytest.raises(JobCancelled):
        job.retry_minutes(folder, tmp_path, stop_before_extraction, cancel)
    assert read_manifest(folder)['status'] == 'cancelled'
    assert job.can_retry_minutes(folder, tmp_path)
    job.retry_minutes(folder, tmp_path, lambda *_: None)
    assert calls == [[1, 2], [3], [3]]
    assert read_manifest(folder)['summary_status'] == 'failed'
    assert len(list(folder.glob('.minutes-*.json'))) == 1
    fail = False
    calls.clear()
    job.retry_minutes(folder, tmp_path, lambda *_: None)
    assert calls == [[3]]
    assert read_manifest(folder)['summary_status'] == 'complete'
    assert not (folder / 'MINUTA_NO_GENERADA.txt').exists()
    report = (folder / 'RESUMEN_Y_MINUTA_LOCAL.md').read_text(encoding='utf-8')
    assert '# Minuta de reunión' in report and '# Meeting minutes' in report
    evidence = json.loads((folder / 'MINUTA_EVIDENCIAS.json').read_text(encoding='utf-8'))
    assert {item['sources'][0]['quote'] for item in evidence['items']} == {row['text'] for row in rows}
    with ZipFile(folder / 'RESULTADOS_COMPLETOS.zip') as archive:
        assert 'RESULTADOS_COMPLETOS/Minutas/RESUMEN_Y_MINUTA_LOCAL.md' in archive.namelist()
        assert not any('/.minutes-' in name for name in archive.namelist())
        assert 'RESULTADOS_COMPLETOS/Minutas/MINUTA_NO_GENERADA.txt' not in archive.namelist()


def test_whisper_cpu_keeps_word_timestamps_and_discards_out_of_bounds_padding(tmp_path):
    observed = {}
    words = [SimpleNamespace(start=0, end=1, word=' overlap'),
             SimpleNamespace(start=2.2, end=3, word=' speech'),
             SimpleNamespace(start=6, end=7, word=' outside'),
             SimpleNamespace(start=float('nan'), end=4, word=' invalid')]

    def infer(_path, **options):
        observed.update(options)
        return [SimpleNamespace(words=words)], None

    model = SimpleNamespace(model=SimpleNamespace(device='cpu'), transcribe=infer)
    rows = transcribe_clip(model, Clip(2, 10, 13, 8, 14), tmp_path / 'speech.wav')
    assert observed['vad_filter'] and observed['word_timestamps'] and observed['beam_size'] == 2
    assert rows == [{'start': 10.2, 'end': 11, 'text': 'speech', 'part': 2}]
