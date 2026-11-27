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
