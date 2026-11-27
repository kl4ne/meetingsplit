import json
import pytest
from engine.minutes_evidence import source_blocks,validate_items

SOURCE='Al final se habló de preparar ejemplos de atención a visitantes y revisar su claridad antes de la próxima capacitación.'
def extract(text,category='review',quote=None,owner=None,due=None):
    rows=next(source_blocks('[00:00:01] '+text))
    return validate_items(json.dumps({'items':[{'category':category,'sources':[{'id':1,'quote':quote or text}],
        'owner':owner,'due':due,'text_es':'Propuesta preliminar pendiente de confirmación formal.'}]}),rows,'es')[0]

def test_actual_discussion_review_is_not_pending_proposal():
    item=extract(SOURCE)
    assert item['category']=='topic'
    assert item['owner'] is None and item['due'] is None
    assert item['sources'][0]['quote']==SOURCE
    assert 'Propuesta preliminar' not in item['text_es']

@pytest.mark.parametrize('source',[
    'Al final se habló de preparar ejemplos y se acordó distribuirlos.',
    'Al final se habló de preparar ejemplos si se aprueba el presupuesto.',
    'Al final se habló de preparar ejemplos y se asignó a Ana Ruiz la tarea.',
    'Al final se habló de preparar ejemplos y queda pendiente el responsable.',
    'Al final se habló de preparar ejemplos para una inversión de $100.',
    'Al final se habló de preparar ejemplos. Se decidió distribuirlos.',
])
def test_mixed_or_operational_discussion_not_automatically_recovered(source):
    assert extract(source)['category']!='topic'

def test_partial_quote_and_explicit_task_metadata_do_not_recover():
    assert extract(SOURCE,quote='se habló de preparar ejemplos')['category']=='review'
    assert extract(SOURCE,due='la próxima capacitación')['category']=='review'


@pytest.mark.parametrize('sentence,quote',[
    ('Se explicó que una instrucción técnica y una recomendación pedagógica tienen funciones diferentes.',None),
    ('The discussion distinguished feedback on a service from a proposal to change the service and considered the usefulness of preserving the original context of a question.',None),
    ('Se habló de preparar ejemplos que permitan distinguir preguntas frecuentes de solicitudes excepcionales.','Se habló de preparar ejemplos que permitan distinguir preguntas frecuentes de solicitudes excepcionales'),
])
def test_descriptive_sentence_in_multi_sentence_row_is_not_operational(sentence,quote):
    from engine.minutes_evidence import validate_items,explicit_source_items
    text='Se examinó la guía. '+sentence+' Se revisó el archivo.'
    rows=next(source_blocks('[00:00:01] '+text))
    raw=json.dumps({'items':[{'category':'proposal','owner':None,'due':None,
        'sources':[{'id':1,'quote':quote or sentence}],'text_es':'Propuesta de trabajo.'}]})
    items=validate_items(raw,rows,'es')
    assert items[0]['category']=='topic'
    assert not explicit_source_items(rows,'es')
    assert items[0]['sources'][0]['quote']==(quote or sentence)

@pytest.mark.parametrize('sentence',[
    'Se explicó que una instrucción técnica y una recomendación pedagógica tienen funciones diferentes, y se acordó cambiar el manual.',
    'The discussion distinguished feedback from a proposal to change the service and the committee proposed extending hours.',
    'Se habló de preparar ejemplos y se asignó a Ana Ruiz la tarea.',
])
def test_operational_content_does_not_get_descriptive_exemption(sentence):
    from engine.minutes_evidence import _descriptive_sentence_for_quote
    assert not _descriptive_sentence_for_quote(sentence,sentence)

def test_short_clause_not_used_to_clear_review():
    from engine.minutes_evidence import _descriptive_sentence_for_quote
    sentence='Se habló de preparar ejemplos que permitan distinguir preguntas frecuentes de solicitudes excepcionales.'
    assert not _descriptive_sentence_for_quote('Se habló de preparar ejemplos',sentence)
