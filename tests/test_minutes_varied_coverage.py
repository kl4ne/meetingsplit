"""Observed varied fixture regressions, no model needed."""
import json
import pytest
from engine.minutes_brief import repair_editorial_omissions,omitted_editorial_sources
from engine.minutes_evidence import source_blocks,validate_items,explicit_source_items,reconcile_source_items
from engine.minutes_localization import prepare_presentation,apply_translations,local_day

def refs(n):
    return [{'source_id':i,'timestamp':'00:00:01','quote':f'Se revisó un tema distinto del archivo {i}.'} for i in range(1,n+1)]
def theme(ref):
    return {'sources':[ref],'title_es':'Tema del archivo '+str(ref['source_id']),
            'summary_es':ref['quote']}

def test_omission_repair_keeps_accepted_and_limits_requests():
    sources=refs(14); accepted=[theme(sources[0])]
    calls=[]
    def request(messages,schema,**kw):
        ids=kw['scope']['source_ids'];calls.append(ids)
        assert schema['properties']['themes']['minItems']==0
        r=sources[ids[0]-1]
        return json.dumps({'themes':[{'source_ids':[r['source_id']],
            'title_es':'Tema del archivo '+str(r['source_id']),'summary_es':r['quote']}]})
    repaired,gaps,initial=repair_editorial_omissions(sources,accepted,[],'es',request)
    assert calls==[list(range(2,7)),list(range(7,12))]
    assert repaired[0]==accepted[0] and len(repaired)==3
    assert {r['source_id'] for r in gaps}==set(range(2,15))-{2,7}
    assert len(initial)==13

def test_empty_or_failed_repair_does_not_clear_omissions_or_repeat_rejected():
    sources=refs(4); calls=[]
    def request(messages,schema,**kw):
        calls.append(kw['scope']['source_ids']);return '{"themes":[]}'
    kept,gaps,initial=repair_editorial_omissions(sources,[theme(sources[0])],[sources[1]],'es',request)
    assert calls==[[3,4]]
    assert gaps==sources[1:] and initial==sources[2:]
    assert kept==[theme(sources[0])]

@pytest.mark.parametrize('source,category,expected',[
    ('Se anunció que el material de consulta está disponible en recepción.','notice','notice'),
    ('Se explicó que una instrucción técnica y una recomendación pedagógica tienen funciones distintas.','topic','topic'),
    ('Participants reviewed a fictional example of a follow-up conversation in which the original question was still unresolved.','review','topic'),
    ('Se habló de preparar ejemplos prácticos de orientación para la siguiente sesión de formación.','proposal','topic'),
])
def test_observed_classification(source,category,expected):
    rows=next(source_blocks('[00:00:01] '+source))
    raw=json.dumps({'items':[{'category':category,'sources':[{'id':1,'quote':source}],
                              'owner':None,'due':None,'text_es':'Se revisó el tema.'}]})
    items=reconcile_source_items(validate_items(raw,rows,'es'),explicit_source_items(rows,'es'))
    assert len(items)==1 and items[0]['category']==expected
    assert items[0]['sources'][0]['quote']==source

def test_real_proposal_and_pending_are_not_suppressed():
    rows=next(source_blocks('[00:00:01] El equipo propuso extender el horario.\n[00:00:02] Who will order replacement supplies? No responsible person or deadline was assigned.'))
    assert [x['category'] for x in explicit_source_items(rows,'es')]==['proposal','pending']

@pytest.mark.parametrize('text,valid',[
    ('Ana Ruiz enviará la guía del visitante a más tardar el viernes.',True),
    ('Ana Ruiz enviará la guía del visitante antes del viernes.',False),
    ('Ana Ruiz enviará la guía del visitante a más tardar el jueves.',False),
])
def test_full_literal_due_relation(text,valid):
    original={'category':'action','sources':[{'source_id':6,'timestamp':'00:07:30',
              'quote':'Ana Ruiz will send the visitor guide by Friday.'}],
              'owner':'Ana Ruiz','due':'by Friday','text_es':'Consulta las palabras originales en la cita.'}
    copies,todo=prepare_presentation([original],'es')
    accepted,rejected=apply_translations(json.dumps({'translations':[{'id':0,'text':text}]}),copies,todo,'es')
    assert bool(accepted)==valid and bool(rejected)!=valid
    assert copies[0]['due']=='by Friday' and original['due']=='by Friday'
    assert local_day('by Friday','es')=='a más tardar el viernes'
