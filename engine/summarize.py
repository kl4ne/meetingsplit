"""Grounded meeting prompts + optional entirely local Ollama summarization."""
from __future__ import annotations
import re
from .ollama import chat, DEFAULT_ENDPOINT

_TIMESTAMP=re.compile(r'\[(\d{2}:\d{2}:\d{2})\]')


def validate_report_references(report: str, transcript: str) -> None:
    if not report.lstrip().startswith('#'):
        raise RuntimeError('Ollama did not return a finished Markdown report')
    available=set(_TIMESTAMP.findall(transcript))
    cited=set(_TIMESTAMP.findall(report))
    if cited-available or (available and not cited):
        raise RuntimeError('Report references missing or absent from original transcript; review required')



def instructions(mode: str='both', language: str='es') -> str:
    goal={
        'summary':'Produce un resumen ejecutivo fiel',
        'minutes':'Produce una minuta formal y detallada',
        'both':'Produce primero un resumen ejecutivo y luego una minuta formal',
    }[mode]
    lang={
        'es':'en español',
        'en':'in English',
        'both':'en dos secciones independientes: español e inglés',
    }[language]
    return f'''Actúa como secretario documental, sin inventar información.
{goal} {lang} a partir de la transcripción de la reunión.
La grabación puede alternar español e inglés; conserva nombres propios,
cifras, cargos, acuerdos y matices. No interpretes una propuesta como resolución.
Distingue acuerdos confirmados, ideas discutidas, desacuerdos y pendientes.
Para las tareas, registra descripción, responsable, fecha y estado solamente
cuando esté expresado; si falta algo indica «No especificado».
Incluye referencias exactas a marcas de tiempo [HH:MM:SS] copiadas de la fuente para acuerdos y tareas. Nunca inventes ni redondees marcas. Si hay marcas de tiempo, incluye al menos una.
No inventes nombres de oradores: usa «Participante no identificado».
Marca [REVISAR AUDIO] ante palabras dudosas, cortes o fechas ambiguas.
Encabezados: fecha (si se conoce), título, participantes (si constan),
resumen, temas, acuerdos confirmados, tareas, pendientes y seguimiento.
No agregues hechos que no estén en el texto.
Devuelve SOLO el documento final en Markdown, empezando por un título #.
No muestres razonamiento, instrucciones ni comentarios sobre cómo redactarlo.'''


def ollama_chat(messages: list[dict], model: str='qwen3:4b', timeout: int=900, **kwargs) -> str:
    """Talk ONLY to loopback Ollama, not the public Internet."""
    return chat(messages, model=model, timeout=timeout, **kwargs)


def summarize_local(transcript: str, mode: str, language: str, model: str,
                    progress=lambda msg:None, *, endpoint=DEFAULT_ENDPOINT, cancel=None,
                    evidence_sink=None) -> str:
    """Extract bounded structured candidates, validate literal evidence, then render."""
    from .minutes_evidence import source_blocks, validate_items, render_minutes, extraction_prompt
    if mode not in ('summary','minutes','both') or language not in ('es','en','both'):
        raise ValueError('Invalid report mode or language')
    blocks=list(source_blocks(transcript))
    items=[];seen=set();empty=[]
    for number,rows in enumerate(blocks,1):
        if cancel: cancel.check()
        progress(f'Analizando evidencias / Checking evidence: {number}/{len(blocks)}')
        messages=extraction_prompt(rows,language)
        for attempt in range(2):
            if cancel: cancel.check()
            raw=ollama_chat(messages,model,endpoint=endpoint,cancel=cancel,progress=progress,json_output=True)
            try:
                extracted=validate_items(raw,rows,language)
                break
            except ValueError as exc:
                if attempt:
                    raise RuntimeError(f'Invalid source evidence in section {number}; review transcript') from exc
                messages=extraction_prompt(rows,language)+[
                    {'role':'user','content':'The last response failed mechanical validation. Regenerate JSON using only exact source quotations and IDs, null for missing owner or date.'}]
        if not extracted: empty.append(number)
        for item in extracted:
            # Deduplicate identical evidence only; do not merge distinct obligations.
            key=(item['category'],tuple((s['source_id'],s['quote']) for s in item['sources']),item['owner'],item['due'],
                 item.get('text_es'),item.get('text_en'))
            if key not in seen:
                seen.add(key);items.append(item)
    if cancel: cancel.check()
    report=render_minutes(items,mode,language,empty)
    if evidence_sink is not None:
        evidence_sink({'schema':1,'review_required':True,'verification':'literal_source_match_only',
                       'source_blocks':len(blocks),'empty_blocks':len(empty),'empty_block_ids':empty,'items':items})
    return report
