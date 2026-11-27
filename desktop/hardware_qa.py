"""Explicit internal QA entry point for the frozen app, using synthetic files only.

Never part of normal startup or automatic installer actions. Requires a caller-
selected internal test folder containing the two Windows-generated fake meetings,
prepared optional components and cached models. Does not install components.
"""
from __future__ import annotations
import gc
import json
from pathlib import Path
import time
from desktop.storage import validate_local_folder


def main(root_path, output_path):
    root=validate_local_folder(Path(root_path))
    output=Path(output_path)
    validate_local_folder(output.parent)
    report={'ok':False,'synthetic_only':True,'stages':[]}
    def save():
        temporary=output.with_suffix('.partial')
        temporary.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        temporary.replace(output)
    save()
    try:
        from engine.inference_worker import InferenceWorker
        from engine.control import Cancellation
        from engine.audio import probe
        from engine.planning import Clip
        for language in ('en','es'):
            if not (root/f'synthetic-meeting-{language}.wav').is_file():
                raise ValueError('Required synthetic TTS fixture missing: '+language)
        worker=InferenceWorker(root,root/'Modelos',Cancellation())
        try:
            worker_info=worker.ping()
            device=worker.load('medium')
            if device!='NVIDIA GPU': raise RuntimeError('Frozen GPU check entered CPU fallback')
            for language in ('en','es'):
                audio=root/f'synthetic-meeting-{language}.wav'
                duration=probe(audio);start=time.monotonic()
                rows=worker.transcribe(Clip(1,0,duration,0,duration),audio,language)
                if not rows: raise RuntimeError('Frozen GPU did not transcribe synthetic speech')
                report['stages'].append({'stage':'cuda-speech','language':language,'device':device,
                    'isolated_worker':True,'worker_protocol':worker_info['protocol'],
                    'seconds':round(time.monotonic()-start,2),'rows':rows})
                save()
        finally:
            worker.close()
        gc.collect()
        from engine.ollama import LocalService,MODEL
        from engine.summarize import summarize_local
        source='[00:00:01] Ana will send the draft on Friday.\n[00:00:06] Luis agreed to review it on Monday.'
        with LocalService(root) as service:
            service.ensure_model()
            for language in ('en','es'):
                start=time.monotonic()
                result=summarize_local(source,'minutes',language,MODEL,endpoint=service.endpoint)
                if not all(name in result for name in ('Ana','Luis')):
                    raise RuntimeError('Frozen minutes omitted required names')
                report['stages'].append({'stage':'ollama-minutes','language':language,
                    'seconds':round(time.monotonic()-start,2),'text':result,'factual_review_required':True})
                save()
        report['ok']=True;save();return 0
    except Exception as exc:
        report['error']=str(exc)[:700];save();return 2


def minutes_recovery(root_path):
    """Run the frozen retry path in a fresh project with caller-supplied synthetic fixtures."""
    from shutil import copyfile
    from tempfile import mkdtemp
    from zipfile import BadZipFile, ZipFile
    from desktop.version import VERSION
    from engine.control import Cancellation
    from engine.job import _sha256, _write_json, retry_minutes
    from engine.ollama import existing_status, reusable_existing
    from engine.transcription import format_transcript

    root = validate_local_folder(Path(root_path))
    project = Path(mkdtemp(prefix='MeetingSplit-minutes-qa-', dir=root))
    result_path = project / '.qa-result.json'
    result = {'ok': False, 'version': VERSION}
    _write_json(result_path, result)
    started = time.monotonic()
    try:
        source = root / 'synthetic-transcript.json'
        source_audio = root / 'synthetic-part.mp3'
        if any(not path.is_file() or path.is_symlink() for path in (source, source_audio)):
            raise ValueError('Provide synthetic-transcript.json and synthetic-part.mp3 in the QA folder.')
        rows = json.loads(source.read_text(encoding='utf-8'))['segments']
        if not isinstance(rows, list) or not rows or not all(
            isinstance(row, dict) and set(row) == {'start', 'end', 'text'} for row in rows
        ):
            raise ValueError('The synthetic transcript must contain start, end and text for each segment.')
        if not reusable_existing():
            raise RuntimeError('QA requires an existing verified Ollama model on the normal local server.')
        server = existing_status()
        result.update(ollama=server['version'], model=server['model']['name'], digest=server['model'].get('digest'))
        _write_json(result_path, result)

        task = Cancellation()
        checkpoint = project / 'transcripcion_parte_01.json'
        transcript = project / 'TRANSCRIPCION_COMPLETA.txt'
        audio = project / 'parte_01.mp3'
        _write_json(checkpoint, {'segments': rows})
        transcript.write_text(format_transcript(rows), encoding='utf-8')
        copyfile(source_audio, audio)
        hashes = {path: _sha256(path, task) for path in (audio, transcript, checkpoint)}
        _write_json(project / 'manifest.json', {
            'status': 'complete',
            'summary_status': 'failed',
            'clips': [{'number': 1}],
            'checkpoints': {'1': hashes[checkpoint]},
            'resume_signature': {'settings': {
                'action': 'both', 'report': 'both', 'language': 'es',
                'local_summary': True, 'zip_output': True,
            }},
        })
        with (project / '.qa-progress.log').open('w', encoding='utf-8', buffering=1) as log:
            retry_minutes(project, root, lambda message, pct: log.write(f'{pct}% {message}\n'), task)

        manifest = json.loads((project / 'manifest.json').read_text(encoding='utf-8'))
        result['summary_status'] = manifest['summary_status']
        if manifest['summary_status'] not in ('complete', 'needs_review'):
            raise RuntimeError((project / 'MINUTA_NO_GENERADA.txt').read_text(encoding='utf-8')[:700])
        if any(_sha256(path, task) != before for path, before in hashes.items()):
            raise RuntimeError('Minutes recovery changed audio or transcription.')
        with ZipFile(project / 'RESULTADOS_COMPLETOS.zip') as archive:
            entries = set(archive.namelist())
            required = {
                'RESULTADOS_COMPLETOS/Audio/parte_01.mp3',
                'RESULTADOS_COMPLETOS/Transcripciones/TRANSCRIPCION_COMPLETA.txt',
                'RESULTADOS_COMPLETOS/Minutas/RESUMEN_Y_MINUTA_LOCAL.md',
                'RESULTADOS_COMPLETOS/Datos_JSON/MINUTA_EVIDENCIAS.json',
            }
            roots = {entry.split('/', 1)[0] for entry in entries}
            if roots != {'RESULTADOS_COMPLETOS'} or not required <= entries or archive.testzip():
                raise RuntimeError('Recovered ZIP is corrupt or its files are misplaced.')
        result.update(ok=True, preserved_input=True, organized_zip=True)
    except (BadZipFile, OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        result['error'] = str(exc)[:700]
    finally:
        result['seconds'] = round(time.monotonic() - started, 2)
        _write_json(result_path, result)
    return 0 if result['ok'] else 2

