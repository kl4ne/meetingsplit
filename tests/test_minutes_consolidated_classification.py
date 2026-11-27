"""Regression of actual recorded extraction errors from artifact 15180493657."""
import json
from engine.minutes_evidence import (
    explicit_source_items, reconcile_source_items, source_blocks, validate_items, render_minutes,
)
from engine.minutes_overview import build_overview

LINES=[
    'The reference guide distinguishes confidential notes from public materials. Volunteers should ask for clarification when unsure.',
    'Ya empezaremos el mes de abril con talleres de lectura.',
    'Este mes reservamos los sábados para realizar las prácticas en la biblioteca.',
    'Who will order replacement supplies? No responsible person or deadline was assigned.',
    'Ana Ruiz se comprometió a enviar el inventario el viernes.',
]
ROWS=next(source_blocks('\n'.join(f'[00:00:0{i}] {line}' for i,line in enumerate(LINES,1))))

def item(i,category,text,owner=None,due=None):
    return {'category':category,'sources':[{'id':i,'quote':LINES[i-1]}],
            'owner':owner,'due':due,'text_es':text}

def test_recorded_extraction_keeps_guidance_notices_pending_and_exact_commitment():
    raw=json.dumps({'items':[
        item(1,'topic','Distinción entre notas confidenciales y materiales públicos según la guía de referencia; los voluntarios deben pedir aclaraciones si tienen dudas.'),
        item(2,'topic','Inicio en abril de una serie de talleres dedicados a la lectura.'),
        item(3,'topic','Reserva de los días sábado del presente mes para llevar a cabo prácticas en la biblioteca.'),
        item(4,'pending','Asignación pendiente: falta determinar quién encargará los suministros de reemplazo y cuál será la fecha límite para dicha acción.'),
        item(5,'action','Envío del documento de inventario por parte de Ana Ruiz con fecha límite para este viernes.','Ana Ruiz','el viernes'),
    ]},ensure_ascii=False)
    verified=validate_items(raw,ROWS,'es')
    explicit=explicit_source_items(ROWS,'es')
    result=reconcile_source_items(verified,explicit)
    indexed={i['sources'][0]['source_id']:i for i in result}
    assert indexed[1]['category']=='topic'
    assert not any(i['category']=='proposal' for i in result)
    assert indexed[2]['text_es']==LINES[1]
    assert indexed[3]['text_es']==LINES[2]
    assert indexed[4]['category']=='pending' and indexed[4]['owner'] is None and indexed[4]['due'] is None
    assert indexed[5]['text_es']==LINES[4] and 'fecha límite' not in indexed[5]['text_es']
    overview=build_overview(result,[],'es')
    report=render_minutes(result,'both','es',show_timestamps=False,executive_overview={'es':overview})
    assert 'abril' in report and 'Este mes' in report
    assert '## Pendientes' in report and 'suministros de reemplazo' in report
    assert '## Propuestas' not in report

def test_bare_question_and_conditional_proposal_do_not_become_pending_or_decision():
    rows=next(source_blocks('[00:00:01] Who will order supplies?\n[00:00:02] If approved, we should extend the hours.'))
    explicit=explicit_source_items(rows,'es')
    assert not any(i['category'] in ('pending','decision','action') for i in explicit)

def test_actual_proposal_not_suppressed_by_guide_word():
    rows=next(source_blocks('[00:00:01] The board proposed changing the reference guide.'))
    assert explicit_source_items(rows,'en')[0]['category']=='proposal'
