"""Disk-first offline recording pipeline with persisted status and cooperative stop."""
from __future__ import annotations
import json
import gc
import hashlib
import os
import tempfile
from contextlib import contextmanager
import uuid
import math
import shutil
from pathlib import Path
import re
from datetime import datetime
from .audio import audio_start_offset, detect_silences, export_clip, probe
from .control import Cancellation, JobCancelled
from .output import format_srt, pack_result
from .planning import Clip, plan_clips
from .inference_worker import InferenceWorker, NativeInferenceError
from .summarize import instructions, summarize_local
from .ollama import MODEL
from .transcription import (format_transcript, load_whisper, load_cpu_whisper,
                            is_cuda_runtime_error, transcribe_clip)
from desktop.storage import validate_local_folder
from desktop.version import VERSION

ALLOWED={'.mp3','.m4a','.wav','.aac','.ogg','.flac','.mp4','.wma','.opus'}


def _write_text(path: Path, text: str) -> None:
    # Unique exclusive staging file, not a predictable .partial that could
    # point at another file. Replacement does not modify a hardlink target.
    if path.is_symlink():
        raise ValueError('Unsafe result path: '+path.name)
    fd,name=tempfile.mkstemp(prefix='.write-',suffix='.partial',dir=path.parent)
    tmp=Path(name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def _write_json(path: Path, data: dict) -> None:
    _write_text(path,json.dumps(data,ensure_ascii=False,indent=2))


@contextmanager
def _job_lock(folder: Path):
    # OS-backed advisory lock: released automatically even on process death.
    # Keep the small lock file, avoiding unlink/recreate races between instances.
    path=folder/'.job.lock'
    if path.is_symlink(): raise ValueError('Unsafe job lock')
    fd=os.open(path,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
    locked=False
    try:
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            locked=True
        except OSError as exc:
            raise RuntimeError('This MeetingSplit job is already in use') from exc
        yield
    finally:
        try:
            if locked:
                if os.name=='nt':
                    os.lseek(fd,0,os.SEEK_SET)
                    msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
                else:
                    fcntl.flock(fd,fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _source_identity(path):
    stat=path.stat()
    return stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,stat.st_dev,stat.st_ino


def _check_source(path, identity):
    if _source_identity(path)!=identity:
        raise ValueError('Source recording changed during processing; previous verified parts preserved')


def _validate(config: dict) -> dict:
    src=Path(config['file']).expanduser().resolve(strict=True)
    if not src.is_file() or src.suffix.lower() not in ALLOWED:
        raise ValueError('Selecciona un archivo de audio compatible.')
    if not src.stat().st_size:
        raise ValueError('El archivo de audio está vacío.')
    base=validate_local_folder(Path(config['output']).expanduser())
    action=config.get('action','both')
    fmt=config.get('format','mp3')
    minutes=int(config.get('minutes',10))
    overlap=int(config.get('overlap',20))
    model=config.get('model','medium')
    audio_language=config.get('input_language','auto')
    report=config.get('report','both')
    language=config.get('report_language','es')
    if action not in ('split','transcribe','both'): raise ValueError('Acción inválida')
    if fmt not in ('mp3','m4a','wav'):raise ValueError('Formato inválido')
    if minutes not in (5,10,15,20):raise ValueError('Duración inválida')
    if overlap not in (10,20,30):raise ValueError('Solapamiento inválido')
    if model not in ('small','medium','large-v3'):raise ValueError('Modelo inválido')
    if audio_language not in ('auto','es','en'):raise ValueError('Idioma del audio inválido')
    if report not in ('summary','minutes','both') or language not in ('es','en','both'):
        raise ValueError('Idioma o formato de informe inválido')
    return {'source':src,'base':base,'action':action,'fmt':fmt,'minutes':minutes,
            'overlap':overlap,'model':model,'audio_language':audio_language,
            'report':report,'language':language}


def _sha256(path: Path, task: Cancellation) -> str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024*1024):
            task.check()
            h.update(chunk)
    return h.hexdigest()


def _resume_signature(source, x, config, task):
    stat=source.stat()
    sha=_sha256(source,task)
    if (stat.st_size,stat.st_mtime_ns)!=(source.stat().st_size,source.stat().st_mtime_ns):
        raise ValueError('Source changed while checking its integrity')
    settings={k:v for k,v in x.items() if k not in ('source','base')}
    settings.update(zip_output=bool(config.get('zip_output',True)),
                    local_summary=bool(config.get('local_summary',False)),
                    preserve_cpu_quality=bool(config.get('preserve_cpu_quality',False)),
                    provider=config.get('provider','chatgpt'),plan=config.get('plan','paid'),
                    ollama_model=MODEL)
    return {'schema':1,'source_sha256':sha,'source_bytes':stat.st_size,'settings':settings}


def _matches_resume_signature(previous, current):
    if previous == current:
        return True
    if not isinstance(previous, dict) or not isinstance(previous.get('settings'), dict):
        return False
    settings = previous['settings']
    if settings.get('ollama_model') not in ('qwen3:4b', 'qwen3.5:4b', 'qwen3.8:27b'):
        return False
    # Minutes are regenerated with the current model; the recording and audio settings must match.
    return dict(previous, settings=dict(settings, ollama_model=MODEL)) == current


def _verify_checkpoint(path, expected, task):
    if not expected or not path.is_file() or path.is_symlink() or _sha256(path,task)!=expected:
        raise ValueError('Checkpoint integrity failed; original files preserved: '+path.name)


def _quarantine(path):
    if path.exists() or path.is_symlink():
        path.rename(path.with_name('.orphan-'+uuid.uuid4().hex+'-'+path.name))


def _check_space(folder: Path, required: int) -> None:
    if shutil.disk_usage(folder).free < required:
        raise OSError(f'Insufficient disk space / Espacio insuficiente: {required} bytes required')


def _estimated_output_bytes(clips, fmt: str, export: bool, zip_output: bool) -> int:
    # PCM upper bound for each current mono output format, plus metadata.
    rate = {'mp3': 8000, 'm4a': 12000, 'wav': 32000}[fmt]
    total = sum(math.ceil((c.export_end-c.export_start)*rate)+65536 for c in clips)
    return 128*1024**2 + (total*(2 if zip_output else 1) if export else
                          max((math.ceil((c.export_end-c.export_start)*8000)+65536 for c in clips), default=0))


def run_job(config: dict, progress, cancel:Cancellation|None=None, *, on_transcription_device=lambda _:None) -> Path:
    """Return project directory; errors/cancellation preserve auditable partial outputs."""
    task=cancel or Cancellation()
    notify=progress
    last_pct=0
    def progress(message, pct):
        nonlocal last_pct
        last_pct=max(last_pct, min(100, max(0, int(pct))))
        notify(message,last_pct)
    x=_validate(config)
    src=x['source'];base=x['base']
    task.check()
    slug=re.sub(r'[^\w-]+','-',src.stem,flags=re.UNICODE).strip('-')[:56] or 'reunion'
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    folder=base/f'MeetingSplit-{slug}-{stamp}'
    suffix=2
    while folder.exists():
        folder=base/f'MeetingSplit-{slug}-{stamp}-{suffix}';suffix+=1
    _check_space(base, 128*1024**2)
    progress('Verificando integridad de la grabación / Checking source integrity',2)
    identity=_source_identity(src)
    signature=_resume_signature(src,x,config,task)
    _check_source(src,identity)
    resume=config.get('resume_folder')
    if resume:
        folder=_project_folder(resume,base)
    else:
        folder.mkdir(parents=False,exist_ok=False)
    with _job_lock(folder):
        return _run_locked(config,x,src,base,folder,signature,identity,resume,progress,task,on_transcription_device)


def _project_folder(folder, base):
    folder=validate_local_folder(Path(folder))
    if folder.parent!=base or not folder.name.startswith('MeetingSplit-'):
        raise ValueError('Choose a MeetingSplit job inside the configured data folder')
    return folder


def _read_manifest(folder):
    path=folder/'manifest.json'
    if path.is_symlink():
        raise ValueError('Unsafe job manifest')
    return json.loads(path.read_text(encoding='utf-8'))


def _minutes_pending(manifest):
    return (manifest.get('transcript_ready') or manifest.get('status')=='complete') and \
        manifest.get('summary_status') in ('started','failed','needs_review')


def _generate_minutes(folder, base, manifest, settings, transcript, progress, task):
    from .ollama import LocalService
    settings['ollama_model'] = MODEL
    manifest['summary_status']='started'
    for key in ('summary_evidence','summary_evidence_items','summary_empty_source_blocks',
                'summary_review_required','summary_coverage_gaps'):
        manifest.pop(key,None)
    _write_json(folder/'manifest.json',manifest)
    diagnostic=folder/'MINUTA_NO_GENERADA.txt'
    try:
        task.check()
        progress('Preparando minuta local con Ollama',91)
        evidence={}
        def read_block(key):
            path=folder/f'.minutes-{key}.json'
            if path.is_symlink():
                raise ValueError('Unsafe minutes checkpoint')
            return path.read_text(encoding='utf-8') if path.is_file() else None

        with LocalService(base,task,lambda msg:progress(msg,92)) as service:
            service.ensure_model()
            report=summarize_local(transcript,settings['report'],settings['language'],
                                   MODEL,
                                   progress=lambda msg:progress(msg,92),endpoint=service.endpoint,
                                   cancel=task,evidence_sink=evidence.update,read_block=read_block,
                                   write_block=lambda key,raw:_write_text(folder/f'.minutes-{key}.json',raw),
                                   narrative_strategy='localized_editorial')
        task.check()
        _write_json(folder/'MINUTA_EVIDENCIAS.json',evidence)
        _write_text(folder/'RESUMEN_Y_MINUTA_LOCAL.md',report)
        diagnostic.unlink(missing_ok=True)
        gaps=len(evidence.get('coverage_gaps',[]))
        items=evidence.get('items',[])
        repetition=evidence.get('repetition_coverage')
        unresolved_empty=(repetition['unresolved_empty_block_ids'] if repetition is not None
                          else evidence.get('empty_block_ids',[]))
        # Preserve review classification until editorial acceptance. Exact
        # repetitions are accounted for, not a semantic approval.
        needs_review=bool(gaps or not items or unresolved_empty or evidence.get('editorial_gaps')
                          or evidence.get('narrative_fallbacks')
                          or (evidence.get('source_accounting') or {}).get('uncited_passages')
                          or any((evidence.get('source_accounting') or {}).get('compound_review',{}).values())
                          or any(entry.get('rejected') for entry in evidence.get('localization',[]))
                          or any(item.get('category')=='review' for item in items))
        manifest.update(summary_status='needs_review' if needs_review else 'complete',
                        summary_review_required=True,summary_evidence='MINUTA_EVIDENCIAS.json',
                        summary_evidence_items=len(evidence.get('items',[])),
                        summary_empty_source_blocks=evidence.get('empty_blocks',0),
                        summary_coverage_gaps=gaps)
    except JobCancelled:
        raise
    except Exception as exc:
        manifest['summary_status']='failed'
        warning=('La minuta local no se generó; audio y transcripción conservados. / '
                 'Local minutes failed; audio and transcript preserved.\n'+str(exc)[:500])
        _write_text(diagnostic,warning)


def _finish_job(folder, manifest, zip_output, progress, task):
    task.check()
    manifest['status']='complete'
    manifest.pop('error',None)
    _write_json(folder/'manifest.json',manifest)
    if zip_output:
        target=folder/'RESULTADOS_COMPLETOS.zip'
        _check_space(folder, sum(f.stat().st_size for f in folder.iterdir()
                                 if f.is_file() and f!=target and not f.name.startswith('.'))+16*1024**2)
        progress('Creando paquete ZIP de resultados',96)
        pack_result(folder,target,cancel=task)
    progress('Resultados terminados. Ya puedes abrirlos.',100)
    return folder


def _retry_minutes_locked(folder, base, manifest, progress, task):
    settings=manifest['resume_signature']['settings']
    if settings.get('action') not in ('transcribe','both') or not settings.get('local_summary'):
        raise ValueError('This project does not include local minutes.')
    if not _minutes_pending(manifest):
        raise ValueError('This project has no local minutes to retry.')
    rows=[]
    clips=manifest.get('clips',[])
    if not clips:
        raise ValueError('No saved transcript for this project.')
    for clip in clips:
        number=clip['number']
        path=folder/f'transcripcion_parte_{number:02}.json'
        _verify_checkpoint(path,manifest.get('checkpoints',{}).get(str(number)),task)
        rows.extend(json.loads(path.read_text(encoding='utf-8'))['segments'])
    rows.sort(key=lambda row:row['start'])
    manifest['transcript_ready']=True
    try:
        _generate_minutes(folder,base,manifest,settings,format_transcript(rows),progress,task)
        return _finish_job(folder,manifest,settings.get('zip_output',True),progress,task)
    except JobCancelled:
        manifest['status']='cancelled'
        _write_json(folder/'manifest.json',manifest)
        raise
    except Exception as exc:
        manifest.update(status='failed',error=str(exc)[:800])
        _write_json(folder/'manifest.json',manifest)
        raise


def can_retry_minutes(folder, output):
    base=validate_local_folder(Path(output))
    folder=_project_folder(folder,base)
    return bool(_minutes_pending(_read_manifest(folder)))


def retry_minutes(folder, output, progress, cancel=None):
    """Retry only local minutes from the project's verified transcript checkpoints."""
    base=validate_local_folder(Path(output))
    folder=_project_folder(folder,base)
    with _job_lock(folder):
        return _retry_minutes_locked(folder,base,_read_manifest(folder),progress,cancel or Cancellation())


def _run_locked(config,x,src,base,folder,signature,identity,resume,progress,task,on_transcription_device):
    if resume:
        manifest=_read_manifest(folder)
        if not _matches_resume_signature(manifest.get('resume_signature'), signature):
            raise ValueError('Resume requires the same recording and settings')
        manifest['resume_signature'] = signature
        if _minutes_pending(manifest):
            return _retry_minutes_locked(folder,base,manifest,progress,task)
        if manifest.get('status')=='complete' and (not signature['settings']['zip_output'] or (folder/'RESULTADOS_COMPLETOS.zip').is_file()):
            raise ValueError('This job is already complete')
        if manifest.get('status') not in ('started','failed','cancelled','complete'):
            raise ValueError('Invalid resumable job status')
        manifest['status']='started'
        manifest.pop('error',None)
    else:
        manifest={
        'version':VERSION, 'source_name':src.name,'source_bytes':src.stat().st_size,
        'created':datetime.now().isoformat(), 'status':'started',
        'mode':x['action'],'max_export_seconds':x['minutes']*60,
        'overlap_seconds':x['overlap'],'model':x['model'],
        'AI_provider':config.get('provider','chatgpt'),
        'subscription':config.get('plan','paid'),
        'privacy':'Archivo original no modificado. Procesamiento en disco local.',
        'transcription_segments':0,'clips':[],'exports':[],
        'warnings':['Verifica cifras, nombres, fechas y cambios entre idiomas en el audio original.'],
        'resume_signature':signature,'checkpoints':{},
        }
    _write_json(folder/'manifest.json',manifest)
    model=None
    isolated=bool(config.get('isolated_inference',False))
    preserve=bool(config.get('preserve_cpu_quality',False))
    cpu_model=x['model'] if preserve else ('small' if x['model'] in ('medium','large-v3') else x['model'])
    def close_model():
        nonlocal model
        if isinstance(model,InferenceWorker): model.close()
        model=None
    def start_isolated(name,cpu=False):
        nonlocal model
        model=InferenceWorker(folder,base/'Modelos',task,preserve)
        return model.load(name,cpu=cpu)
    def infer(clip,path):
        if isolated: return model.transcribe(clip,path,x['audio_language'])
        kwargs={'language':x['audio_language'],'cancel':task}
        if preserve: kwargs['preserve_quality']=True
        return transcribe_clip(model,clip,path,**kwargs)
    try:
        progress('Inspeccionando duración y formato',4)
        task.check()
        duration=probe(src)
        media_options={}
        if src.suffix.lower() in ('.mp4','.m4a'):
            offset=audio_start_offset(src)
            if offset:
                media_options['source_offset']=offset
        _check_source(src,identity)
        if duration>4*3600:
            raise ValueError('Esta versión acepta grabaciones de hasta 4 horas.')
        manifest['duration_seconds']=round(duration,3)
        progress('Analizando silencios sin cargar todo el audio en RAM',10)
        silences=detect_silences(src,cancel=task)
        _check_source(src,identity)
        task.check()
        target=x['minutes']*60
        max_core=target-2*x['overlap']
        ideal_core=max(30,max_core-30)
        clips=plan_clips(duration,silences,target_seconds=ideal_core,
                          max_seconds=max_core,overlap_seconds=x['overlap'])
        if any(c.export_end-c.export_start>target+.01 for c in clips):
            raise RuntimeError('Plan de cortes supera la duración máxima solicitada.')
        plan=[c.to_dict() for c in clips]
        saved_plan=manifest.get('clips')
        if resume and saved_plan and saved_plan!=plan:
            # v0.8.6 rounded cuts to milliseconds before applying overlap.
            # Keep completed parts on exactly their old timeline when only
            # that rounding differs.
            coordinates=('core_start','core_end','export_start','export_end')
            if len(saved_plan)!=len(plan) or any(
                old['number']!=new['number'] or any(abs(old[k]-new[k])>.001 for k in coordinates)
                for old,new in zip(saved_plan,plan)
            ):
                raise ValueError('The saved clip plan differs; previous outputs preserved')
            clips=[Clip(**part) for part in saved_plan]
            plan=saved_plan
        manifest['clips']=plan
        _write_json(folder/'manifest.json',manifest)
        _write_text(folder/'INSTRUCCIONES_CHATGPT_GEMINI.txt',
            instructions(x['report'],x['language'])+
            '\n\nAdjunta TRANSCRIPCION_COMPLETA.txt o los audios numerados. '
            'Usa los tiempos para contrastar y evita repetir el solapamiento.\n')
        do_transcribe=x['action'] in ('both','transcribe')
        do_export=x['action'] in ('both','split')
        checkpoints=manifest.setdefault('checkpoints',{})
        saved_exports={entry['file']:entry for entry in manifest.get('exports',[])}
        remaining=[c for c in clips if f'parte_{c.number:02}.{x["fmt"]}' not in saved_exports]
        _check_space(folder, _estimated_output_bytes(remaining if do_export else clips,x['fmt'],do_export,bool(config.get('zip_output',True))))
        lines=[]
        model=None
        if do_transcribe and any(str(c.number) not in checkpoints for c in clips):
            task.check()
            if isolated:
                progress('Preparing isolated Whisper worker / Preparando motor aislado',15)
                try:
                    device=start_isolated(x['model'])
                except NativeInferenceError:
                    close_model()
                    task.check()
                    manifest['warnings'].append('Native model startup failed; retrying on CPU.')
                    device=start_isolated(cpu_model,cpu=True)
            else:
                kwargs={'model_cache':base/'Modelos','on_status':lambda message:progress(message,15),'cancel':task}
                if preserve: kwargs['preserve_quality']=True
                model,device=load_whisper(x['model'],**kwargs)
            manifest['device']=device
            manifest['actual_model']=x['model']
            if device == 'CPU':
                manifest['actual_model'] = cpu_model
                manifest['warnings'].append('Modo CPU: '+cpu_model+'; revisa la precisión.')
            _write_json(folder/'manifest.json',manifest)
        for index,clip in enumerate(clips):
            task.check()
            _check_source(src,identity)
            _check_space(folder, 64*1024**2)
            file=folder/f'parte_{clip.number:02}.{x["fmt"]}'
            if do_export:
                progress(f'Exportando audio {index+1} de {len(clips)}', int(17+71*index/len(clips)))
                if file.name in saved_exports:
                    _verify_checkpoint(file,saved_exports[file.name].get('sha256'),task)
                else:
                    if resume: _quarantine(file)
                    entry=export_clip(src,file,clip,x['fmt'],cancel=task,**media_options)
                    _check_source(src,identity)
                    entry['sha256']=_sha256(file,task)
                    manifest['exports'].append(entry)
                    _write_json(folder/'manifest.json',manifest)
            if do_transcribe:
                part_path=folder/f'transcripcion_parte_{clip.number:02}.json'
                if str(clip.number) in checkpoints:
                    _verify_checkpoint(part_path,checkpoints[str(clip.number)],task)
                    part=json.loads(part_path.read_text(encoding='utf-8'))['segments']
                    lines.extend(part)
                    _write_text(folder/f'transcripcion_parte_{clip.number:02}.txt',format_transcript(part))
                    continue
                if resume: _quarantine(part_path)
                if not do_export:
                    file=folder/f'.temporal_{clip.number:02}.mp3'
                    if resume: _quarantine(file)
                    export_clip(src,file,clip,'mp3',cancel=task,**media_options)
                    _check_source(src,identity)
                try:
                    task.check()
                    on_transcription_device(device)
                    progress(f'Transcribiendo audio {index+1} de {len(clips)}',
                             int(17+71*(index+.5)/len(clips)))
                    try:
                        part=infer(clip,file)
                    except Exception as exc:
                        # The first real CUDA call can occur while iterating the
                        # lazy Whisper generator, AFTER successful model creation.
                        # Retry only the current clip on CPU, never duplicate rows.
                        if device != 'NVIDIA GPU' or not (isinstance(exc,NativeInferenceError) or is_cuda_runtime_error(exc)):
                            raise
                        task.check()
                        progress('Fallo de bibliotecas NVIDIA/CUDA. Reintentando el audio por CPU.',
                                 int(17+71*(index+.5)/len(clips)))
                        manifest['warnings'].append(
                            'GPU no disponible durante la inferencia; transcripción continuó por CPU. '
                            + str(exc)[:180])
                        close_model()
                        gc.collect()
                        progress('Reintentando con CPU y modelo '+cpu_model+'. Puede tardar varios minutos por fragmento.',
                                 int(17+71*(index+.5)/len(clips)))
                        if isolated: start_isolated(cpu_model,cpu=True)
                        else: model = load_cpu_whisper(cpu_model,model_cache=base/'Modelos')
                        manifest['actual_model'] = cpu_model
                        device = 'CPU'
                        on_transcription_device(device)
                        manifest['device'] = device
                        _write_json(folder/'manifest.json',manifest)
                        task.check()
                        part=infer(clip,file)
                    # Persist timestamped rows before marking this clip complete.
                    _write_json(part_path,{'segments':part,'device':device,
                                          'model':manifest.get('actual_model',x['model'])})
                    checkpoints[str(clip.number)]=_sha256(part_path,task)
                    lines.extend(part)
                    _write_text(folder/f'transcripcion_parte_{clip.number:02}.txt',format_transcript(part))
                    manifest['transcription_segments']=len(lines)
                    _write_json(folder/'manifest.json',manifest)
                finally:
                    if not do_export:file.unlink(missing_ok=True)
        on_transcription_device('')
        _check_source(src,identity)
        if do_transcribe:
            manifest['transcription_segments']=len(lines)
            lines.sort(key=lambda row:row['start'])
            transcript=format_transcript(lines)
            _write_text(folder/'TRANSCRIPCION_COMPLETA.txt',transcript)
            _write_text(folder/'TRANSCRIPCION_SUBTITULOS.srt',format_srt(lines))
            _write_json(folder/'TRANSCRIPCION_MARCAS_TIEMPO.json',{'segments':lines})
            manifest['transcript_ready']=True
            if config.get('local_summary',False):
                # Release Whisper before Qwen needs the same memory.
                close_model()
                gc.collect()
                _generate_minutes(folder,base,manifest,signature['settings'],transcript,progress,task)
            else:
                manifest['summary_status']='not_requested'
                manifest['warnings'].append(
                    'La minuta automática requiere un modelo local adicional. '
                    'Se adjuntan instrucciones para ChatGPT/Gemini.')
        else:
            manifest['summary_status']='excluded'
            if config.get('local_summary',False):
                manifest['warnings'].append(
                    'Solo dividir no usa transcripción y no genera una minuta local.')
        close_model()
        _check_source(src,identity)
        return _finish_job(folder,manifest,signature['settings']['zip_output'],progress,task)
    except JobCancelled:
        manifest['status']='cancelled'
        manifest['warnings'].append('Cancelado; se conservaron los archivos completos anteriores a la cancelación.')
        _write_json(folder/'manifest.json',manifest)
        raise
    except Exception as exc:
        manifest['status']='failed'
        manifest['error']=str(exc)[:800]
        _write_json(folder/'manifest.json',manifest)
        raise
    finally:
        close_model()
