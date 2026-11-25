"""Grounded meeting prompts + optional entirely local Ollama summarization."""
from __future__ import annotations
import hashlib
import json
import re
from .ollama import chat, DEFAULT_ENDPOINT, OutputLimitError

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
                    evidence_sink=None, read_block=None, write_block=None) -> str:
    """Extract bounded structured candidates, validate literal evidence, then render."""
    from .minutes_evidence import (source_blocks, validate_items, render_minutes,
                                   extraction_prompt, extraction_schema, find_coverage_gaps,
                                   explicit_source_items, reconcile_source_items)
    if mode not in ('summary','minutes','both') or language not in ('es','en','both'):
        raise ValueError('Invalid report mode or language')
    blocks=list(source_blocks(transcript))
    items=[];seen=set();empty=[]

    def extract(rows, number):
        if cancel: cancel.check()
        messages=extraction_prompt(rows,language)
        key=hashlib.sha256(json.dumps([1,model,language,messages],ensure_ascii=False).encode()).hexdigest()
        cached=read_block(key) if read_block else None
        if cached is not None:
            try:
                saved=validate_items(cached,rows,language)
                if not find_coverage_gaps(rows,saved) and all(item['category']!='review' for item in saved):
                    return saved
            except ValueError:
                pass
        schema=extraction_schema(rows,language)
        for attempt in range(2):
            if cancel: cancel.check()
            try:
                raw=ollama_chat(messages,model,endpoint=endpoint,cancel=cancel,progress=progress,json_output=schema)
            except OutputLimitError:
                if len(rows)==1:
                    raise
                break
            try:
                extracted=validate_items(raw,rows,language,source_only_on_mismatch=bool(attempt))
            except ValueError as exc:
                if attempt:
                    if len(rows)==1:
                        raise RuntimeError(f'Invalid source evidence in section {number}; review transcript') from exc
                    break
                messages=messages+[
                    {'role':'user','content':'Use exact source quotations and IDs. Leave digits and currency values in the quotations, not the descriptions.'}]
                continue
            gaps=find_coverage_gaps(rows,extracted)
            if extracted and not gaps and write_block and all(item['category']!='review' for item in extracted):
                verified=[
                    dict(item,sources=[{'id':ref['source_id'],'quote':ref['quote']} for ref in item['sources']])
                    for item in extracted
                ]
                write_block(key,json.dumps({'items':verified},ensure_ascii=False))
            return extracted
        progress(f'Dividiendo sección {number} / Splitting evidence section {number}')
        midpoint=len(rows)//2
        return extract(rows[:midpoint],number)+extract(rows[midpoint:],number)

    for number,rows in enumerate(blocks,1):
        progress(f'Analizando evidencias / Checking evidence: {number}/{len(blocks)}')
        extracted=extract(rows,number)
        if not extracted: empty.append(number)
        for item in extracted:
            # Deduplicate identical evidence only; do not merge distinct obligations.
            key=(item['category'],tuple((s['source_id'],s['quote']) for s in item['sources']),item['owner'],item['due'],
                 item.get('text_es'),item.get('text_en'))
            if key not in seen:
                seen.add(key);items.append(item)
    if cancel: cancel.check()
    rows=[row for block in blocks for row in block]
    items=reconcile_source_items(items,explicit_source_items(rows,language))
    coverage_gaps=find_coverage_gaps(rows,items)
    report=render_minutes(items,mode,language,empty,coverage_gaps)
    if evidence_sink is not None:
        evidence_sink({'schema':1,'review_required':True,'verification':'literal_source_match_only',
                       'source_blocks':len(blocks),'empty_blocks':len(empty),'empty_block_ids':empty,
                       'coverage_gaps':coverage_gaps,'items':items})
    return report
