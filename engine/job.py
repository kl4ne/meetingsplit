"""Disk-first offline recording pipeline with persisted status and cooperative stop."""
from __future__ import annotations
import json
import gc
from pathlib import Path
import re
from datetime import datetime
from .audio import detect_silences, export_clip, probe
from .control import Cancellation, JobCancelled
from .output import format_srt, pack_result
from .planning import plan_clips
from .summarize import instructions, summarize_local
from .transcription import (format_transcript, load_whisper, load_cpu_whisper,
                            is_cuda_runtime_error, transcribe_clip)
from desktop.storage import validate_local_folder

ALLOWED={'.mp3','.m4a','.wav','.aac','.ogg','.flac','.mp4','.wma','.opus'}


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix('.json.partial')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


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


def run_job(config: dict, progress, cancel:Cancellation|None=None) -> Path:
    """Return project directory; errors/cancellation preserve auditable partial outputs."""
    task=cancel or Cancellation()
    x=_validate(config)
    src=x['source'];base=x['base']
    task.check()
    slug=re.sub(r'[^\w-]+','-',src.stem,flags=re.UNICODE).strip('-')[:56] or 'reunion'
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    folder=base/f'MeetingSplit-{slug}-{stamp}'
    suffix=2
    while folder.exists():
        folder=base/f'MeetingSplit-{slug}-{stamp}-{suffix}';suffix+=1
    folder.mkdir(parents=False,exist_ok=False)
    manifest={
        'version':'0.8.5', 'source_name':src.name,'source_bytes':src.stat().st_size,
        'created':datetime.now().isoformat(), 'status':'started',
        'mode':x['action'],'max_export_seconds':x['minutes']*60,
        'overlap_seconds':x['overlap'],'model':x['model'],
        'AI_provider':config.get('provider','chatgpt'),
        'subscription':config.get('plan','paid'),
        'privacy':'Archivo original no modificado. Procesamiento en disco local.',
        'transcription_segments':0,'clips':[],'exports':[],
        'warnings':['Verifica cifras, nombres, fechas y cambios entre idiomas en el audio original.'],
    }
    _write_json(folder/'manifest.json',manifest)
    try:
        progress('Inspeccionando duración y formato',4)
        task.check()
        duration=probe(src)
        if duration>4*3600:
            raise ValueError('Esta versión acepta grabaciones de hasta 4 horas.')
        manifest['duration_seconds']=round(duration,3)
        progress('Analizando silencios sin cargar todo el audio en RAM',10)
        silences=detect_silences(src,cancel=task)
        task.check()
        target=x['minutes']*60
        max_core=target-2*x['overlap']
        ideal_core=max(30,max_core-30)
        clips=plan_clips(duration,silences,target_seconds=ideal_core,
                          max_seconds=max_core,overlap_seconds=x['overlap'])
        if any(c.export_end-c.export_start>target+.01 for c in clips):
            raise RuntimeError('Plan de cortes supera la duración máxima solicitada.')
        manifest['clips']=[c.to_dict() for c in clips]
        _write_json(folder/'manifest.json',manifest)
        (folder/'INSTRUCCIONES_CHATGPT_GEMINI.txt').write_text(
            instructions(x['report'],x['language'])+
            '\n\nAdjunta TRANSCRIPCION_COMPLETA.txt o los audios numerados. '
            'Usa los tiempos para contrastar y evita repetir el solapamiento.\n',
            encoding='utf-8')
        do_transcribe=x['action'] in ('both','transcribe')
        do_export=x['action'] in ('both','split')
        lines=[]
        model=None
        if do_transcribe:
            task.check()
            model,device=load_whisper(x['model'],model_cache=base/'Modelos',
                                       on_status=lambda message:progress(message,15),cancel=task)
            manifest['device']=device
            if device == 'CPU':
                manifest['actual_model'] = 'small' if x['model'] in ('medium', 'large-v3') else x['model']
                manifest['warnings'].append('Modo CPU: modelo small para acelerar el procesamiento; revisa la precisión.')
            _write_json(folder/'manifest.json',manifest)
        for index,clip in enumerate(clips):
            task.check()
            file=folder/f'parte_{clip.number:02}.{x["fmt"]}'
            if do_export:
                progress(f'Exportando audio {index+1} de {len(clips)}', int(17+32*index/len(clips)))
                manifest['exports'].append(export_clip(src,file,clip,x['fmt'],cancel=task))
                _write_json(folder/'manifest.json',manifest)
            if do_transcribe:
                if not do_export:
                    file=folder/f'.temporal_{clip.number:02}.mp3'
                    export_clip(src,file,clip,'mp3',cancel=task)
                try:
                    task.check()
                    progress(f'Transcribiendo audio {index+1} de {len(clips)}. En CPU el primer fragmento puede tardar varios minutos; el tiempo transcurrido se muestra en pantalla.',
                             int(49+39*index/len(clips)))
                    try:
                        part=transcribe_clip(model,clip,file,language=x['audio_language'],cancel=task)
                    except Exception as exc:
                        # The first real CUDA call can occur while iterating the
                        # lazy Whisper generator, AFTER successful model creation.
                        # Retry only the current clip on CPU, never duplicate rows.
                        if device != 'NVIDIA GPU' or not is_cuda_runtime_error(exc):
                            raise
                        task.check()
                        progress('Fallo de bibliotecas NVIDIA/CUDA. Reintentando el audio por CPU.',
                                 int(49+39*index/len(clips)))
                        manifest['warnings'].append(
                            'GPU no disponible durante la inferencia; transcripción continuó por CPU. '
                            + str(exc)[:180])
                        model = None
                        gc.collect()
                        cpu_model = 'small' if x['model'] in ('medium','large-v3') else x['model']
                        progress('Reintentando con CPU y modelo '+cpu_model+'. Puede tardar varios minutos por fragmento.',
                                 int(49+39*index/len(clips)))
                        model = load_cpu_whisper(cpu_model,model_cache=base/'Modelos')
                        manifest['actual_model'] = cpu_model
                        device = 'CPU'
                        manifest['device'] = device
                        _write_json(folder/'manifest.json',manifest)
                        task.check()
                        part=transcribe_clip(model,clip,file,language=x['audio_language'],cancel=task)
                    lines.extend(part)
                    (folder/f'transcripcion_parte_{clip.number:02}.txt').write_text(
                        format_transcript(part),encoding='utf-8')
                    manifest['transcription_segments']=len(lines)
                    _write_json(folder/'manifest.json',manifest)
                finally:
                    if not do_export:file.unlink(missing_ok=True)
        if do_transcribe:
            lines.sort(key=lambda row:row['start'])
            transcript=format_transcript(lines)
            (folder/'TRANSCRIPCION_COMPLETA.txt').write_text(transcript,encoding='utf-8')
            (folder/'TRANSCRIPCION_SUBTITULOS.srt').write_text(format_srt(lines),encoding='utf-8')
            _write_json(folder/'TRANSCRIPCION_MARCAS_TIEMPO.json',{'segments':lines})
            if config.get('local_summary',False):
                # Release Whisper VRAM before asking Qwen to load on an 8 GB GPU.
                model=None
                gc.collect()
                task.check()
                progress('Preparando minuta local con Ollama',91)
                from .ollama import LocalService
                with LocalService(base,task,lambda msg:progress(msg,92)) as service:
                    service.ensure_model()
                    report=summarize_local(transcript,x['report'],x['language'],
                                            config.get('ollama_model','qwen3:4b'),
                                            progress=lambda message:progress(message,92),
                                            endpoint=service.endpoint,cancel=task)
                task.check()
                (folder/'RESUMEN_Y_MINUTA_LOCAL.md').write_text(report,encoding='utf-8')
            else:
                manifest['warnings'].append(
                    'La minuta automática requiere un modelo local adicional. '
                    'Se adjuntan instrucciones para ChatGPT/Gemini.')
        task.check()
        manifest['status']='complete'
        _write_json(folder/'manifest.json',manifest)
        if bool(config.get('zip_output',True)):
            progress('Creando paquete ZIP de resultados',96)
            pack_result(folder, folder/'RESULTADOS_COMPLETOS.zip',cancel=task)
        progress('Resultados terminados. Ya puedes abrirlos.',100)
        return folder
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
