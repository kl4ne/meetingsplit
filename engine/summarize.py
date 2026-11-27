"""Grounded meeting prompts + optional entirely local Ollama summarization."""
from __future__ import annotations
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from .ollama import chat, DEFAULT_ENDPOINT, MODEL, OllamaHTTPError, OutputLimitError

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
Redacta con títulos, párrafos y listas breves. No uses tablas.
No agregues hechos que no estén en el texto.
Devuelve SOLO el documento final en Markdown, empezando por un título #.
No muestres razonamiento, instrucciones ni comentarios sobre cómo redactarlo.'''


def ollama_chat(messages: list[dict], model: str=MODEL, timeout: int=900, **kwargs) -> str:
    """Talk ONLY to loopback Ollama, not the public Internet."""
    return chat(messages, model=model, timeout=timeout, **kwargs)


def summarize_local(transcript: str, mode: str, language: str, model: str,
                    progress=lambda msg:None, *, endpoint=DEFAULT_ENDPOINT, cancel=None,
                    evidence_sink=None, read_block=None, write_block=None, qa_trace=None) -> str:
    """Extract evidence, draft and review prose, then render the minutes.

    qa_trace is an explicit in-memory callback for synthetic QA only. It is never
    configured by the desktop job and writes nothing to logs or meeting files.
    """
    from .minutes_evidence import (source_blocks, validate_items, render_minutes,
                                   extraction_prompt, extraction_schema, find_coverage_gaps,
                                   explicit_source_items, reconcile_source_items, recover_evidence_items)
    if mode not in ('summary','minutes','both') or language not in ('es','en','both'):
        raise ValueError('Invalid report mode or language')
    guide_path = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1])) / 'docs' / 'Guia_Owll_y_Minutas_para_Ollama.md'
    guide = guide_path.read_text(encoding='utf-8')

    def with_guide(messages, *, prose=False):
        instruction = ('Redacta y revisa en prosa, según el formato solicitado.' if prose else
                       'Mantén el esquema JSON solicitado; aplica la guía a las descripciones.')
        return [dict(messages[0], content=messages[0]['content'] +
                     '\n\nGuía editorial. ' + instruction + '\n' +
                     guide + '\n\nPara esta etapa, sigue el encargo y el esquema específicos del comienzo.'), *messages[1:]]

    blocks=list(source_blocks(transcript))
    items=[];seen=set();empty=[]
    cpu_only=False

    def trace(stage, event, scope, **details):
        if qa_trace is not None:
            qa_trace({'stage':stage,'event':event,'model':model,'scope':scope,**details})

    def request(messages, schema=False, *, stage, scope):
        nonlocal cpu_only
        options={} if schema else {'think':False}
        def invoke():
            start=time.monotonic()
            trace(stage,'request',scope,messages=messages,schema=schema,cpu_only=cpu_only)
            try:
                raw=ollama_chat(messages,model,endpoint=endpoint,cancel=cancel,progress=progress,
                                json_output=schema,cpu_only=cpu_only,**options)
            except Exception as exc:
                trace(stage,'request_error',scope,error_type=type(exc).__name__,
                      reason=str(exc),http_status=getattr(exc,'status',None),
                      elapsed_seconds=time.monotonic()-start)
                raise
            trace(stage,'response',scope,raw=raw,elapsed_seconds=time.monotonic()-start)
            return raw
        try:
            return invoke()
        except OllamaHTTPError as exc:
            if exc.status!=500 or cpu_only:
                raise
            if cancel: cancel.check()
            cpu_only=True
            progress('Ollama falló. Reintentando la minuta por CPU.')
            return invoke()

    def extract(rows, number):
        if cancel: cancel.check()
        messages=with_guide(extraction_prompt(rows,language))
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
                raw=request(messages,schema,stage='extraction',scope={'block':number,'source_ids':[row['id'] for row in rows],'attempt':attempt+1,'language':language})
            except OutputLimitError:
                if len(rows)==1:
                    raise
                break
            try:
                extracted=validate_items(raw,rows,language,source_only_on_mismatch=bool(attempt))
            except ValueError as exc:
                trace('extraction','validation_error',{'block':number,'source_ids':[row['id'] for row in rows],'attempt':attempt+1,'language':language},reason=str(exc))
                if attempt:
                    recovered=recover_evidence_items(raw,rows,language)
                    if recovered is not None:
                        progress('Conservando evidencias válidas / Keeping verified evidence')
                        return recovered
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
    explicit_items=explicit_source_items(rows,language)
    items=reconcile_source_items(items,explicit_items)
    coverage_gaps=find_coverage_gaps(rows,items)
    from .control import JobCancelled
    from .minutes_brief import editorial_input, editorial_request, validate_editorial
    editorial=[]
    editorial_gaps=[]
    sections=editorial_input(blocks,items,explicit_items=explicit_items) if len(rows)>=4 else ()
    for section in sections:
        if cancel: cancel.check()
        progress('Preparando la síntesis temática / Preparing the thematic overview')
        messages,schema=editorial_request(section,language)
        scope={'source_ids':[row['source_id'] for row in section],'language':language}
        try:
            raw=request(with_guide(messages),schema,stage='editorial',scope=scope)
            accepted=validate_editorial(raw,section,language,rejected=editorial_gaps,
                        on_rejection=lambda theme,exc:trace('editorial','theme_rejected',scope,theme=theme,reason=str(exc)))
            editorial.extend(accepted)
            trace('editorial','accepted',scope,themes=accepted)
        except JobCancelled:
            raise
        except (OSError,RuntimeError,ValueError) as exc:
            trace('editorial','section_rejected',scope,error_type=type(exc).__name__,reason=str(exc))
            editorial_gaps.extend(section)
    from .minutes_narrative import (narrative_sections, narrative_request,
                                    review_request, validate_narrative, recover_narrative)
    narratives={}
    narrative_fallbacks=[]
    if len(editorial)>=2:
        for lang in ('es','en') if language=='both' else (language,):
            paragraphs=[]
            for section in narrative_sections(editorial,lang):
                if cancel: cancel.check()
                progress('Redactando la minuta / Drafting the minutes')
                messages=with_guide(narrative_request(section,lang),prose=True)
                scope={'language':lang,'theme_ids':list(section)}
                validated_draft=None
                draft=None
                revised=None
                stage='draft'
                try:
                    draft=request(messages,stage=stage,scope=scope)
                    try:
                        validated_draft=validate_narrative(draft,section,lang)
                        trace(stage,'accepted',scope,paragraphs=validated_draft)
                    except ValueError as exc:
                        trace(stage,'validation_error',scope,reason=str(exc))
                    if cancel: cancel.check()
                    progress('Revisando la minuta / Reviewing the minutes')
                    stage='review_prompt'
                    review_messages=review_request(messages,draft)
                    stage='review'
                    revised=request(review_messages,stage=stage,scope=scope)
                    stage='review_validation'
                    accepted=validate_narrative(revised,section,lang)
                    paragraphs.extend(accepted)
                    trace(stage,'accepted',scope,paragraphs=accepted)
                except JobCancelled:
                    raise
                except (OSError,RuntimeError,ValueError) as exc:
                    narrative_fallbacks.append({'language':lang,'theme_ids':list(section)})
                    if validated_draft is not None:
                        # A failed optional rewrite cannot erase already validated prose.
                        # Retain the review warning; literal validation is not semantic proof.
                        paragraphs.extend(validated_draft)
                        trace(stage,'fallback',scope,reason=str(exc),error_type=type(exc).__name__,retained='validated_draft')
                    else:
                        recovered,selection=recover_narrative(section,lang,draft=draft,revised=revised)
                        paragraphs.extend(recovered)
                        trace(stage,'fallback',scope,reason=str(exc),error_type=type(exc).__name__,
                              retained='partial_narrative' if selection['review'] or selection['draft'] else 'editorial_themes',
                              selection=selection)
            narratives[lang]=paragraphs
    report=render_minutes(items,mode,language,empty,coverage_gaps,
                          editorial=editorial,editorial_gaps=editorial_gaps,
                          narratives=narratives,narrative_fallbacks=narrative_fallbacks,
                          show_timestamps=False)
    if evidence_sink is not None:
        evidence_sink({'schema':1,'review_required':True,'verification':'literal_source_match_only',
                       'source_blocks':len(blocks),'empty_blocks':len(empty),'empty_block_ids':empty,
                       'coverage_gaps':coverage_gaps,'editorial_themes':editorial,
                       'editorial_gaps':editorial_gaps,'narrative_fallbacks':narrative_fallbacks,'items':items})
    return report
