import json

import pytest

from engine.minutes_evidence import render_minutes, source_blocks, validate_items


def classify(source, proposed_category, quote=None, owner=None, due=None):
    rows=next(source_blocks('[00:00:12] '+source))
    item={
        'category':proposed_category,'sources':[{'id':1,'quote':source if quote is None else quote}],
        'owner':owner,'due':due,'text_en':'A draft description.','text_es':'Descripción preliminar.',
    }
    return validate_items(json.dumps({'items':[item]}),rows,'both')[0]


@pytest.mark.parametrize('source,person,due',[
    ('Nora Chen promised to deliver the inventory on Friday.','Nora Chen','Friday'),
    ('Valeria Núñez se comprometió a revisar el inventario el martes.','Valeria Núñez','el martes'),
])
def test_personal_commitment_is_an_action_and_preserves_owner_and_deadline(source,person,due):
    item=classify(source,'decision',due=due)
    assert item['category']=='action' and item['owner']==person and item['due']==due
    assert item['sources'][0]['quote']==source
    report=render_minutes([item],'minutes','both')
    assert '## Possible action items' in report and '## Posibles tareas' in report
    assert person in report and due in report
    assert '## Possible confirmed agreements' not in report


@pytest.mark.parametrize('source,amount',[
    ('The operating budget totals USD 8,200.','USD 8,200'),
    ('El presupuesto operativo asciende a 2,500 pesos.','2,500 pesos'),
])
def test_stated_budget_is_a_topic_and_preserves_the_amount(source,amount):
    item=classify(source,'proposal')
    assert item['category']=='topic'
    report=render_minutes([item],'minutes','both')
    assert '## Topics' in report and '## Temas' in report and report.count(amount)==2
    assert '## Proposals' not in report and '## Propuestas' not in report


@pytest.mark.parametrize('source,category',[
    ('The steering group proposed a budget of $800.','proposal'),
    ('El comité propuso asignar 800 pesos.','proposal'),
    ('The steering group approved the budget of $800.','decision'),
    ('El comité aprobó el presupuesto de 800 pesos.','decision'),
])
def test_explicit_proposals_and_approvals_retain_their_categories(source,category):
    assert classify(source,category)['category']==category


@pytest.mark.parametrize('source,quote,category',[
    ('If the grant is signed, Tania promised to coordinate training.',
     'Tania promised to coordinate training.','decision'),
    ('Si se confirma el aporte, el presupuesto es de 800 pesos.',
     'el presupuesto es de 800 pesos.','proposal'),
    ('The outline was discussed.',None,'decision'),
    ('Se discutió el borrador.',None,'proposal'),
])
def test_unclear_category_uses_the_original_quote_under_review(source,quote,category):
    item=classify(source,category,quote=quote)
    assert item['category']=='review'
    report=render_minutes([item],'minutes','both')
    assert '## Classification pending review' in report and '## Clasificación pendiente de revisión' in report
    assert '## Possible confirmed agreements' not in report
    assert '## Proposals' not in report


def test_reserved_schedule_and_its_purpose_stay_together_as_a_notice():
    from engine.minutes_evidence import explicit_source_items

    transcript=(
        '[00:03:10] En abril empiezan los talleres de lectura.\n'
        '[00:03:16] Como saben, este mes reservamos los sábados.\n'
        '[00:03:20] Para realizar las prácticas en la biblioteca.'
    )
    rows=[row for block in source_blocks(transcript) for row in block]
    items=explicit_source_items(rows,'es')
    assert len(items)==1 and items[0]['category']=='notice'
    assert [ref['timestamp'] for ref in items[0]['sources']]==['00:03:16','00:03:20']
    report=render_minutes(items,'minutes','es',show_timestamps=False)
    assert '## Avisos' in report and 'prácticas en la biblioteca' in report
    assert '## Posibles acuerdos confirmados' not in report and '## Posibles tareas' not in report
    assert '00:03' not in report


def test_conditional_calendar_idea_is_not_an_announcement():
    item=classify('Si reservamos los sábados, podríamos usar el salón.','notice')
    assert item['category']=='review'


def test_announced_start_and_current_schedule_are_separate_notices():
    from engine.minutes_evidence import explicit_source_items

    transcript=(
        '[00:01:10] En el anuncio, ya empezaremos el mes de abril con talleres de lectura.\n'
        '[00:01:17] Para este mes reservamos los sábados.\n'
        '[00:01:20] Para realizar las prácticas en la biblioteca.'
    )
    rows=[row for block in source_blocks(transcript) for row in block]
    notices=explicit_source_items(rows,'es')
    assert [item['category'] for item in notices]==['notice','notice']
    assert [[ref['timestamp'] for ref in item['sources']] for item in notices]==[
        ['00:01:10'],['00:01:17','00:01:20']]

