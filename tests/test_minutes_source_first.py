import json
import pytest
from engine.minutes_source_first import source_units,validate_grouping,compose_groups,translate_units
from engine.minutes_evidence import source_blocks

def test_units_preserve_compound_sentence_and_multiple_sentences():
    blocks=list(source_blocks('[00:00:01] La información debe estar en el mostrador; se distinguió el registro.\n[00:00:02] Visitors can use the entrance ramp. The guide describes accessible routes.'))
    u=source_units(blocks,[],[],'es')
    assert len(u)==3 and [x['source']['source_id'] for x in u]==[1,2,2]
    assert ';' in u[0]['text'] and 'entrance ramp' in u[1]['text']

def test_group_plan_exactly_once_preserves_text_and_sorting():
    units=[{'id':i,'source':{'source_id':i,'quote':f'Source {i}'},'text':f'Texto {i}.','status':'literal'} for i in range(1,5)]
    raw=json.dumps({'groups':[{'title':'Archivo','unit_ids':[4,3],'overview_id':4},
                              {'title':'Recepción','unit_ids':[2,1],'overview_id':1}]})
    groups=validate_grouping(raw,units,'es')
    themes,brief=compose_groups(groups,units,'es')
    assert themes[0]['summary_es']=='Texto 1. Texto 2.'
    assert themes[1]['summary_es']=='Texto 3. Texto 4.'
    assert brief==['Texto 1.','Texto 4.']

@pytest.mark.parametrize('groups',[
    [{'title':'Archivo','unit_ids':[1],'overview_id':1}],
    [{'title':'Archivo','unit_ids':[1,2,2],'overview_id':1}],
    [{'title':'Archivo','unit_ids':[1,3],'overview_id':1}],
    [{'title':'Archivo','unit_ids':[1],'overview_id':2},{'title':'Recepción','unit_ids':[2],'overview_id':2}],
    [{'title':'Se aprobó','unit_ids':[1,2],'overview_id':1}],
])
def test_invalid_plan_rejected(groups):
    with pytest.raises(ValueError):
        validate_grouping(json.dumps({'groups':groups}),[{'id':1},{'id':2}],'es')

def test_translation_failure_preserves_original_unit():
    u=[{'id':1,'source':{'source_id':1,'quote':'Visitors can use the entrance ramp.'},'text':'Visitors can use the entrance ramp.','status':'needs_translation'}]
    def fail(*args,**kwargs):return '{"translations":[{"id":0,"text":"Se aprobó eliminar la rampa."}]}'
    copies,bad,calls=translate_units(u,'es',fail)
    assert calls==1 and bad and copies[0]['status']=='source_only' and copies[0]['text']==u[0]['text']
    assert u[0]['status']=='needs_translation'


from engine.minutes_source_first import plan_grouping_repair,grouping_repair_request,apply_grouping_repair

def test_bounded_repair_preserves_fixed_partition():
    units=[{'id':i,'text':f'Texto {i}.'} for i in range(1,9)]
    raw=json.dumps({'groups':[{'title':'Archivo','unit_ids':[1,2,3,4],'overview_id':3},
                              {'title':'Recepción','unit_ids':[3,5,6,7],'overview_id':5}]})
    plan=plan_grouping_repair(raw,units,'es')
    assert plan['disputed']==[3,8] and plan['duplicates']==[3] and plan['missing']==[8]
    assert plan['fixed'][0]['overview_id']==1
    messages,schema=grouping_repair_request(plan,units,'es')
    assert [u['id'] for u in json.loads(messages[1]['content'])['disputed_units']]==[3,8]
    groups=apply_grouping_repair(json.dumps({'assignments':[{'unit_id':3,'group_id':2},{'unit_id':8,'group_id':1}]}),plan,units,'es')
    assert groups[0]['unit_ids']==[1,2,4,8] and groups[1]['unit_ids']==[3,5,6,7]
    assert plan['fixed'][0]['unit_ids']==[1,2,4]
    for bad in ([{'unit_id':3,'group_id':1},{'unit_id':3,'group_id':2}],
                [{'unit_id':1,'group_id':1},{'unit_id':8,'group_id':2}],
                [{'unit_id':3,'group_id':99},{'unit_id':8,'group_id':1}]):
        with pytest.raises(ValueError):
            apply_grouping_repair(json.dumps({'assignments':bad}),plan,units,'es')

def test_unbounded_or_unanchored_group_repair_rejected():
    units=[{'id':i} for i in range(1,9)]
    for groups in ([{'title':'Archivo','unit_ids':[1,2],'overview_id':1}],
                   [{'title':'Archivo','unit_ids':[1,2,3,4,5,6,7],'overview_id':1},
                    {'title':'Recepción','unit_ids':[1],'overview_id':1}],
                   [{'title':'Se aprobó','unit_ids':[1,2,3,4,5,6,7],'overview_id':1}]):
        with pytest.raises(ValueError):
            plan_grouping_repair(json.dumps({'groups':groups}),units,'es')


def test_grouping_fallback_retains_every_unit_and_warns():
    from engine.minutes_source_first import compose_source_first
    blocks=list(source_blocks('[00:00:01] Se explicó el uso de materiales de consulta.\n[00:00:02] Se habló de revisar los documentos de trabajo.'))
    def fail(*args,**kwargs):
        return '{"groups":[]}'
    out=compose_source_first(blocks,[],[],'es',fail)
    assert out['grouping_failures'] and len(out['units'])==2
    assert all(u['text'] in out['themes'][0]['summary_es'] for u in out['units'])

def test_long_grouping_windows_bounded_and_complete():
    from engine.minutes_source_first import compose_source_first
    text='\n'.join(f'[00:{i//60:02d}:{i%60:02d}] Se habló de revisar el documento de trabajo {i}.' for i in range(123))
    blocks=list(source_blocks(text));calls=[]
    def plan(messages,schema,**kw):
        ids=kw['scope']['unit_ids'];calls.append(ids)
        groups=[{'title':'Documentos de trabajo '+('local' if j==0 else 'general'),
                 'unit_ids':ids[j:j+20],'overview_id':ids[j]} for j in range(0,len(ids),20)]
        return json.dumps({'groups':groups})
    out=compose_source_first(blocks,[],[],'es',plan)
    assert all(len(ids)<=40 for ids in calls) and len(calls)>=4
    assert len(out['units'])==123
    assert sorted(i for w in out['windows'] for g in w['groups'] for i in g['unit_ids'])==list(range(1,124))

def test_optional_real_engine_path_preserves_bilingual_units_and_fallbacks(monkeypatch):
    from engine import summarize
    transcript='[00:00:01] Se explicó el uso de materiales de consulta.\n[00:00:02] The guide describes the accessible routes in the building.'
    calls=[];evidence={}
    def fake(messages,*args,json_output,**kwargs):
        p=json.loads(messages[1]['content']);calls.append(p)
        if 'source_rows' in p:return '{"items":[]}'
        if 'records' in p:
            result=[]
            spanish='into Spanish.' in messages[0]['content']
            for r in p['records']:
                result.append({'id':r['id'],'text':'La guía describe las rutas accesibles.' if spanish else 'The use of reference materials was explained.'})
            return json.dumps({'translations':result})
        if 'units' in p:
            ids=[u['id'] for u in p['units']]
            return json.dumps({'groups':[{'title':'Orientación' if 'Spanish.' in messages[0]['content'] else 'Guidance','unit_ids':ids,'overview_id':ids[0]}]})
        pytest.fail('Unexpected request')
    monkeypatch.setattr(summarize,'ollama_chat',fake)
    report=summarize.summarize_local(transcript,'both','both','qwen3.5:9b',
        evidence_sink=evidence.update,narrative_strategy='source_first')
    assert len(evidence['source_first'])==2
    assert all(len(d['units'])==2 and not d['translation_rejected'] and not d['grouping_failures'] for d in evidence['source_first'])
    assert '## Temas tratados' in report and '## Topics discussed' in report
    assert 'La guía describe las rutas accesibles.' in report and 'The use of reference materials was explained.' in report
    assert evidence['narrative_strategy']=='source_first'


def test_metadata_extraction_omits_duplicate_language_descriptions():
    from engine.minutes_source_first import source_first_extraction_request,validate_source_first_extraction
    rows=next(source_blocks('[00:00:01] Se aprobó mantener el horario actual.'))
    messages,schema=source_first_extraction_request(rows)
    fields=schema['properties']['items']['items']['properties']
    assert set(fields)=={'category','sources','owner','due'}
    assert len(messages[0]['content'])<1500
    raw=json.dumps({'items':[{'category':'decision','sources':[{'id':1,'quote':rows[0]['text']}],
                             'owner':None,'due':None}]})
    items=validate_source_first_extraction(raw,rows,'both')
    assert items[0]['category']=='decision'
    assert items[0]['sources'][0]['quote']==rows[0]['text']
    assert 'text_es' in items[0] and 'text_en' in items[0]
    with pytest.raises(ValueError):
        validate_source_first_extraction(raw.replace('horario actual','horario nuevo'),rows,'both')

def test_metadata_timeout_split_once_and_keeps_unresolved_rows():
    from engine.minutes_source_first import extract_source_first_block
    rows=next(source_blocks('\n'.join(f'[00:00:0{i}] Se revisó el documento {i}.' for i in range(1,5))))
    calls=[]
    def request(messages,schema,**kw):
        ids=kw['scope']['source_ids'];calls.append(ids)
        if 4 in ids:raise TimeoutError('test')
        return '{"items":[]}'
    items,failures=extract_source_first_block(rows,1,'both','qwen3.5:9b',request)
    assert calls==[[1,2,3,4],[1,2],[3,4]]
    assert failures==[{'block':1,'source_ids':[3,4],'reason':'TimeoutError'}]
    assert [i['sources'][0]['source_id'] for i in items]==[3,4]
    assert all(i['category']=='review' for i in items)

def test_metadata_cache_reuses_completed_empty_and_nonempty_results():
    from engine.minutes_source_first import extract_source_first_block
    rows=next(source_blocks('[00:00:01] Se explicó la guía.'))
    cache={};calls=[]
    def request(*args,**kwargs):
        calls.append(kwargs);return '{"items":[]}'
    kwargs={'read_block':cache.get,'write_block':cache.__setitem__}
    for _ in range(2):
        assert extract_source_first_block(rows,1,'es','qwen3.5:9b',request,**kwargs)==([],[])
    assert len(calls)==1 and len(cache)==1

def test_metadata_cancellation_not_swallowed():
    from engine.minutes_source_first import extract_source_first_block
    from engine.control import JobCancelled
    rows=next(source_blocks('[00:00:01] Se explicó la guía.'))
    def stop(*args,**kwargs):raise JobCancelled()
    with pytest.raises(JobCancelled):
        extract_source_first_block(rows,1,'es','qwen3.5:9b',stop)


def test_complete_proposal_not_split_if_localization_rejected():
    from engine.minutes_evidence import explicit_source_items
    source='Proposal only: extend support hours to Saturday. Not approved.'
    blocks=list(source_blocks('[00:00:01] '+source+'\n[00:00:02] Se explicó el uso de materiales.'))
    items=explicit_source_items([r for b in blocks for r in b],'es')
    assert len(items)==1 and items[0]['category']=='proposal'
    diagnostics=[{'language':'es','rejected':[{'id':0,'reason':'test'}]}]
    units=source_units(blocks,items,items,'es',diagnostics)
    assert [u['source']['source_id'] for u in units]==[2]

def test_partial_structured_quote_never_hides_unique_source_content():
    blocks=list(source_blocks('[00:00:01] Proposal only: extend support hours to Saturday. The entrance has a ramp.'))
    item={'category':'proposal','owner':None,'due':None,'text_es':'Consulta las palabras originales en la cita.',
          'sources':[{'source_id':1,'timestamp':'00:00:01','quote':'Proposal only: extend support hours to Saturday.'}]}
    units=source_units(blocks,[item],[item],'es')
    assert any('ramp' in u['text'] for u in units)

@pytest.mark.parametrize('text,valid',[
    ('Propuesta: ampliar las horas de soporte para incluir el sábado. No aprobado.',True),
    ('Propuesta: ampliar las horas de soporte hasta el sábado. No aprobado.',False),
    ('Propuesta: ampliar las horas de soporte para incluir el domingo. No aprobado.',False),
])
def test_observed_support_hours_translation(text,valid):
    from engine.minutes_localization import apply_translations
    item={'category':'proposal','owner':None,'due':None,'text_es':'Consulta las palabras originales en la cita.',
          'sources':[{'source_id':1,'quote':'Proposal only: extend support hours to Saturday.'},{'source_id':1,'quote':'Not approved.'}]}
    good,bad=apply_translations(json.dumps({'translations':[{'id':0,'text':text}]}),[item],[0],'es')
    assert bool(good)==valid and bool(bad)!=valid

@pytest.mark.parametrize('text,valid',[
    ('Approval was granted to maintain the current format of the visitor form.',True),
    ('Approval was not granted to maintain the current format of the visitor form.',False),
    ('Approval was granted to maintain the current format of the visitor form if the committee agrees.',False),
    ('Approval was pending for the current format of the visitor form.',False),
])
def test_narrow_passive_approval_translation(text,valid):
    from engine.minutes_localization import apply_translations
    item={'category':'decision','owner':None,'due':None,'text_en':'See the original wording in the source quotation.',
          'sources':[{'source_id':1,'quote':'Se aprobó mantener el formato actual del formulario de visitantes.'}]}
    good,bad=apply_translations(json.dumps({'translations':[{'id':0,'text':text}]}),[item],[0],'en')
    assert bool(good)==valid and bool(bad)!=valid


def test_every_source_sentence_accounted_without_normalized_dedup_or_personal_aside_loss():
    from engine.minutes_source_first import source_units_with_accounting
    text='\n'.join([
        '[00:00:01] Se explicó la rampa. Se explicó el registro.',
        '[00:00:02] Se explicó la rampa.',
        '[00:00:03] Se explicó LA rampa.',
        '[00:00:04] Yo podría revisar el plano.',
        '[00:00:05] Se aprobó conservar el horario. La puerta tiene una rampa.',
    ])
    blocks=list(source_blocks(text))
    item={'category':'decision','owner':None,'due':None,'text_es':'Se aprobó conservar el horario.',
          'sources':[{'source_id':5,'timestamp':'00:00:05','quote':'Se aprobó conservar el horario.'}]}
    units,account=source_units_with_accounting(blocks,[item],[item],'es')
    assert len(account)==7 and len(units)==5
    assert [a['status'] for a in account]==['detail','detail','exact_repeat','detail','detail','structured','detail']
    assert any(u['text']=='Yo podría revisar el plano.' for u in units)
    assert any('LA rampa' in u['text'] for u in units)
    assert any('puerta tiene una rampa' in u['text'] for u in units)

def test_source_first_modes_are_distinct_and_keep_structured_events_and_warnings():
    from engine.minutes_evidence import render_minutes
    item={'category':'decision','owner':None,'due':None,'text_es':'Se aprobó el horario.',
          'sources':[{'source_id':1,'timestamp':'00:00:01','quote':'Se aprobó el horario.'}]}
    kwargs={'narratives':{'es':[{'title':'Orientación','text':'Detalle de la rampa.','sources':[]}]},
            'executive_overview':{'es':['Introducción breve.']},
            'respect_mode':True,'show_timestamps':False,
            'narrative_fallbacks':[{'language':'es','theme_ids':[]}]}
    summary=render_minutes([item],'summary','es',**kwargs)
    minutes=render_minutes([item],'minutes','es',**kwargs)
    both=render_minutes([item],'both','es',**kwargs)
    assert 'Introducción breve.' in summary and 'Detalle de la rampa.' not in summary
    assert 'Introducción breve.' not in minutes and 'Detalle de la rampa.' in minutes
    assert 'Introducción breve.' in both and 'Detalle de la rampa.' in both
    assert all('Se aprobó el horario.' in d and 'revisión editorial no se completó' in d for d in (summary,minutes,both))
    assert summary.count('Resumen ejecutivo')==1 and '## Temas tratados' in minutes


def test_dense_synthetic_capacity_preserves_all_source_sentences_without_model():
    """Scale-only test; fake grouping does not establish semantic accuracy."""
    from engine.minutes_source_first import compose_source_first,source_units_with_accounting
    paragraphs=[]
    for i in range(270):
        # Distinct indexed rows, with repeated synthetic prose solely to
        # exercise byte limits at the historical workload size.
        text=('Se revisó el material de consulta de la sección '+str(i+1)+
              ', con atención a la descripción de los documentos, la organización del contenido '
              'y la localización de los anexos disponibles en el archivo. '
              'Se explicó la diferencia entre el documento original y la copia de trabajo '
              'utilizada durante la sesión de formación '+str(i+1)+'.')
        paragraphs.append(f'[{i*30//3600:02d}:{i*30//60%60:02d}:{i*30%60:02d}] {text}')
    transcript='\n'.join(paragraphs)
    assert len(transcript.split())>=16000
    blocks=list(source_blocks(transcript))
    calls=[]
    def request(messages,schema,**kw):
        assert kw['stage']=='source_first_grouping'
        ids=kw['scope']['unit_ids'];calls.append(ids)
        assert len(ids)<=40
        payload=json.loads(messages[1]['content'])['units']
        assert sum(len(json.dumps(u,ensure_ascii=False).encode('utf-8')) for u in payload)<=9500
        groups=[{'title':'Material de consulta' if j==0 else 'Documentos de trabajo',
                 'unit_ids':ids[j:j+20],'overview_id':ids[j]} for j in range(0,len(ids),20)]
        return json.dumps({'groups':groups})
    out=compose_source_first(blocks,[],[],'es',request)
    assert len(out['units'])==540
    assert len(out['source_accounting'])==540
    assert not out['translation_rejected'] and not out['grouping_failures']
    assert sorted(i for window in out['windows'] for g in window['groups'] for i in g['unit_ids'])==list(range(1,541))
    assert len(calls)>1
