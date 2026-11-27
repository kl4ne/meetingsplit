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
                    evidence_sink=None, read_block=None, write_block=None, qa_trace=None,
                    narrative_strategy='reviewed') -> str:
    """Extract evidence, draft and review prose, then render the minutes.

    qa_trace is an explicit in-memory callback for synthetic QA only. It is never
    configured by the desktop job and writes nothing to logs or meeting files.
    """
    from .minutes_evidence import (source_blocks, validate_items, render_minutes,
                                   extraction_prompt, extraction_schema, find_coverage_gaps,
                                   explicit_source_items, reconcile_source_items, recover_evidence_items,
                                   plan_quote_retry, unresolved_retry_items)
    if narrative_strategy not in ('reviewed','validated_editorial','localized_editorial','source_first'):
        raise ValueError('Invalid narrative strategy')
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
        options={'think':False} if not schema or stage.startswith('source_first_') else {}
        if stage=='source_first_extraction':
            options['timeout']=240
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
                if not attempt:
                    plan=plan_quote_retry(raw,rows,language)
                    if plan is not None:
                        kept,subset=plan
                        trace('extraction','selective_retry',{'block':number,'language':language,
                              'source_ids':[row['id'] for row in subset]},retained_records=len(kept))
                        if cancel: cancel.check()
                        progress('Reintentando solo citas afectadas / Retrying affected quotations')
                        retried=extract(subset,number)
                        combined=kept+retried+unresolved_retry_items(subset,retried,language)
                        return sorted(combined,key=lambda item:item['sources'][0]['source_id'])
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

    source_first_extraction_failures=[]
    for number,rows in enumerate(blocks,1):
        progress(f'Analizando evidencias / Checking evidence: {number}/{len(blocks)}')
        if narrative_strategy=='source_first':
            from .minutes_source_first import extract_source_first_block
            extracted,failed=extract_source_first_block(rows,number,language,model,request,
                cancel=cancel,read_block=read_block,write_block=write_block,progress=progress)
            source_first_extraction_failures.extend(failed)
        else:
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
    if narrative_strategy=='source_first':
        # Optional comparison strategy, not selected by the desktop.
        from .minutes_source_first import compose_source_first
        from .minutes_localization import localize_items
        from .minutes_overview import build_overview
        from .minutes_evidence import repeated_topic_coverage
        langs=('es','en') if language=='both' else (language,)
        presentation=[dict(i) for i in items]
        localization=[]
        for lang in langs:
            presentation,diag=localize_items(presentation,lang,request,cancel=cancel,progress=progress)
            localization.append(diag)
        diagnostics=[];narratives={};overview={};fallbacks=[];themes=[]
        for lang in langs:
            composed=compose_source_first(blocks,items,presentation,lang,request,
                explicit_items=explicit_items,localization=localization,cancel=cancel,progress=progress)
            diagnostics.append(composed)
            local_themes=composed['themes']
            themes.extend(local_themes)
            narratives[lang]=[{'title':t['title_'+lang],'text':t['summary_'+lang],'sources':t['sources']}
                              for t in local_themes]
            representative_themes=[{'summary_'+lang:r} for r in composed['representatives']]
            overview[lang]=build_overview(presentation,representative_themes,lang)
            if composed['grouping_failures'] or composed['translation_rejected'] or source_first_extraction_failures:
                fallbacks.append({'language':lang,'theme_ids':[],
                    'reason':'source_first incomplete validation'})
            trace('source_first','accepted',{'language':lang},diagnostics=composed)
        # An empty metadata extraction is valid for a purely descriptive block.
        # Preserve the raw empty IDs; separately flag every actual extraction failure.
        repetition=repeated_topic_coverage(blocks,items,themes,[])
        report=render_minutes(presentation,mode,language,repetition['unresolved_empty_block_ids'],coverage_gaps,
            editorial_gaps=[],narratives=narratives,narrative_fallbacks=fallbacks,
            executive_overview=overview,show_timestamps=False,repetition_coverage=repetition,localization=localization)
        if evidence_sink is not None:
            evidence_sink({'schema':1,'review_required':True,'verification':'literal_source_match_only',
                'source_blocks':len(blocks),'empty_blocks':len(empty),'empty_block_ids':empty,
                'coverage_gaps':coverage_gaps,'editorial_themes':themes,'editorial_gaps':[],
                'editorial_initial_omissions':[],'narrative_fallbacks':fallbacks,'narrative_strategy':narrative_strategy,
                'repetition_coverage':repetition,'localization':localization,'presentation':presentation,
                'source_first':diagnostics,'source_first_extraction_failures':source_first_extraction_failures,'items':items})
        return report
    from .control import JobCancelled
    from .minutes_brief import (editorial_input, editorial_request, validate_editorial,
                                editorial_retry_sources, merge_editorial_retry, repair_editorial_omissions)
    editorial=[]
    editorial_gaps=[]
    editorial_omissions=[]
    sections=editorial_input(blocks,items,explicit_items=explicit_items) if len(rows)>=4 else ()
    for section in sections:
        if cancel: cancel.check()
        progress('Preparando la síntesis temática / Preparing the thematic overview')
        messages,schema=editorial_request(section,language)
        scope={'source_ids':[row['source_id'] for row in section],'language':language}
        try:
            raw=request(with_guide(messages),schema,stage='editorial',scope=scope)
            rejected=[]
            accepted=validate_editorial(raw,section,language,rejected=rejected,
                        on_rejection=lambda theme,exc:trace('editorial','theme_rejected',scope,theme=theme,reason=str(exc)))
            if rejected:
                # One repair request only for individually rejected themes.
                # Transport failure and whole-document invalidity do not start
                # a recursive retry chain; their original warning is preserved.
                subset=editorial_retry_sources(rejected)
                repair_scope={'source_ids':[row['source_id'] for row in subset],'language':language}
                if cancel: cancel.check()
                retry_messages,retry_schema=editorial_request(subset,language)
                retry_messages[0]['content'] += (' Repair only these previously rejected excerpts. '
                    'Describe what was discussed; never assert a decision, invent a number, or change a deadline.')
                try:
                    retry_raw=request(with_guide(retry_messages),retry_schema,stage='editorial_retry',scope=repair_scope)
                    retry_rejected=[]
                    repaired=validate_editorial(retry_raw,subset,language,rejected=retry_rejected,
                        on_rejection=lambda theme,exc:trace('editorial_retry','theme_rejected',repair_scope,theme=theme,reason=str(exc)))
                    accepted,rejected=merge_editorial_retry(accepted,rejected,repaired,retry_rejected,language)
                    trace('editorial_retry','accepted',repair_scope,themes=repaired,remaining_gaps=rejected)
                except JobCancelled:
                    raise
                except (OSError,RuntimeError,ValueError) as exc:
                    trace('editorial_retry','section_rejected',repair_scope,error_type=type(exc).__name__,reason=str(exc))
            if narrative_strategy=='localized_editorial':
                accepted,rejected,initial_omissions=repair_editorial_omissions(
                    section,accepted,rejected,language,
                    lambda messages,schema,**kw:request(with_guide(messages),schema,**kw),
                    cancel=cancel,trace=trace)
                editorial_omissions.extend(initial_omissions)
            editorial_gaps.extend(rejected)
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
    if narrative_strategy=='reviewed' and len(editorial)>=2:
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
    displayed_themes=editorial
    repeated_themes=[]
    if narrative_strategy=='localized_editorial':
        from .minutes_theme_presentation import compact_repeated_theme_sources
        displayed_themes,repeated_themes=compact_repeated_theme_sources(blocks,editorial)
    overview=None
    presentation=items
    localization=[]
    if narrative_strategy=='localized_editorial':
        from .minutes_localization import localize_items
        presentation=[dict(item) for item in items]
        for lang in (('es','en') if language=='both' else (language,)):
            translated,diagnostic=localize_items(presentation,lang,request,cancel=cancel,progress=progress)
            presentation=translated
            localization.append(diagnostic)
            trace('localization','accepted',{'language':lang},diagnostic=diagnostic)
    structured_theme_moves=[]
    if narrative_strategy=='localized_editorial':
        from .minutes_theme_presentation import separate_structured_themes
        languages=('es','en') if language=='both' else (language,)
        prior_themes=displayed_themes
        displayed_themes,structured_theme_moves=separate_structured_themes(
            blocks,prior_themes,presentation,languages,localization)
        # Store original editorial indices, even if the repetition pass
        # already removed earlier entries.
        removed={entry['theme_index'] for entry in repeated_themes}
        original_indices=[i for i in range(len(editorial)) if i not in removed]
        for entry in structured_theme_moves:
            entry['theme_index']=original_indices[entry['theme_index']]
    if narrative_strategy in ('validated_editorial','localized_editorial') and (editorial or items):
        from .minutes_overview import build_overview
        overview={lang:build_overview(presentation,displayed_themes,lang)
                  for lang in (('es','en') if language=='both' else (language,))}
        trace('narrative','strategy',{'language':language},
              strategy=narrative_strategy,retained_themes=len(editorial))
    from .minutes_evidence import repeated_topic_coverage
    repetition=repeated_topic_coverage(blocks,items,editorial,empty)
    report=render_minutes(presentation,mode,language,repetition['unresolved_empty_block_ids'],coverage_gaps,
                          editorial=displayed_themes,editorial_gaps=editorial_gaps,
                          narratives=narratives,narrative_fallbacks=narrative_fallbacks,
                          executive_overview=overview,show_timestamps=False,repetition_coverage=repetition,
                          localization=localization,repeated_themes=repeated_themes)
    if evidence_sink is not None:
        evidence_sink({'schema':1,'review_required':True,'verification':'literal_source_match_only',
                       'source_blocks':len(blocks),'empty_blocks':len(empty),'empty_block_ids':empty,
                       'coverage_gaps':coverage_gaps,'editorial_themes':editorial,
                       'editorial_gaps':editorial_gaps,'editorial_initial_omissions':editorial_omissions,'narrative_fallbacks':narrative_fallbacks,
                       'narrative_strategy':narrative_strategy,'repetition_coverage':repetition,
                       'localization':localization,'presentation':presentation if localization else [],
                       'repeated_theme_presentation':repeated_themes,'structured_theme_presentation':structured_theme_moves,'items':items})
    return report
