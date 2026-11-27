import json

import pytest

from engine.minutes_brief import editorial_input, validate_editorial
from engine.minutes_evidence import render_minutes


def make_item(index, category='topic', text='Preparación de equipos'):
    source={'source_id':index, 'timestamp':f'00:00:{index:02d}', 'quote':'El equipo revisó la preparación de los nuevos voluntarios.'}
    return {'category':category, 'sources':[source], 'owner':None, 'due':None, 'text_es':text}


def test_editorial_groups_repeated_topics_and_keeps_verified_actions():
    items = [make_item(i) for i in range(1, 20)]
    action = make_item(20, 'action', 'Ana Ruiz enviará el inventario')
    action.update(owner='Ana Ruiz', due='viernes')
    action['sources'][0]['quote']='Ana Ruiz se comprometió a enviar el inventario el viernes.'
    items.extend((action, make_item(21, 'review')))
    sources = next(editorial_input([[{'id':1,'timestamp':'00:00:01','text':items[0]['sources'][0]['quote']}]]))
    theme = {'source_ids':[1], 'title_es':'Formación de voluntarios',
             'summary_es':'El equipo revisó la preparación de los nuevos voluntarios.'}
    overview = validate_editorial(json.dumps({'themes':[theme]}), sources, 'es')
    report = render_minutes(items, 'minutes', 'es', editorial=overview)
    assert 'Formación de voluntarios' in report and '[00:00:01]' in report
    assert 'Ana Ruiz' in report and 'viernes' in report
    assert 'Un elemento' in report and 'JSON' in report
    assert 'Preparación de equipos' not in report
    assert 'Interpretación de IA' not in report and 'Consulta las palabras originales' not in report


@pytest.mark.parametrize('changes,english', [
    ({'source_ids':[999]}, False),
    ({'summary_es':'El equipo aprobó un monto de $20,000.'}, False),
    ({'summary_es':'The team reviewed the program and discussed support for the new volunteers.'}, True),
])
def test_editorial_rejects_unsupported_citations_amounts_and_wrong_language(changes, english):
    sources=next(editorial_input([[{'id':1,'timestamp':'00:00:01','text':make_item(1)['sources'][0]['quote']}]]))
    theme={'source_ids':[1], 'title_es':'Formación de voluntarios',
           'summary_es':'El equipo revisó la preparación de los nuevos voluntarios.'}
    theme.update(changes)
    with pytest.raises(ValueError, match='language' if english else None):
        validate_editorial(json.dumps({'themes':[theme]}), sources, 'es')


def test_editorial_fallback_bounds_repeated_material_without_empty_summary():
    items=[make_item(i) for i in range(1,20)]
    report=render_minutes(items,'minutes','es')
    assert '## Resumen ejecutivo' in report
    assert report.count('Preparación de equipos') == 1


def test_identical_repeated_proposals_use_one_entry_with_all_timestamps():
    report=render_minutes([make_item(i,'proposal','Revisar los horarios') for i in (1,2,3)],'minutes','es')
    assert report.count('Revisar los horarios') == 1
    assert '[00:00:01], [00:00:02], [00:00:03]' in report


def test_editorial_input_retains_distinct_middle_and_late_evidence():
    blocks = [[{'id':i, 'timestamp':'00:00:01', 'text':f'El equipo trató el tema {i}.'}
               for i in range(first, first+20)] for first in (1,21,41)]
    assert [ref['source_id'] for section in editorial_input(blocks) for ref in section] == list(range(1,61))


def test_local_extraction_receives_bundled_guide(monkeypatch):
    from engine import summarize

    def stub(messages, *args, **kwargs):
        assert 'Owll' in messages[0]['content']
        assert 'No uses tablas en ninguna sección' in messages[0]['content']
        assert json.loads(messages[1]['content'])['source_rows']
        return '{"items": []}'

    monkeypatch.setattr(summarize, 'ollama_chat', stub)
    summarize.summarize_local('[00:00:01] Bienvenidos.', 'both', 'es', 'qwen3:4b')


@pytest.mark.parametrize('revision, accepted', [
    ('La sesión trató la preparación del equipo [E1].\n\nSe habló de cómo explicar la orientación. [E2]', True),
    ('La sesión trató la preparación del equipo. [E1]', False),
    ('Equipo | Preparación [E1] [E2]', False),
    ('La sesión trató la preparación de 200 equipos. [E1] [E2]', False),
    ('El comité aprobó la orientación. [E1] [E2]', False),
])
def test_revised_prose_uses_draft_history_and_preserves_original_evidence(monkeypatch, revision, accepted):
    from engine import summarize

    transcript = '\n'.join((
        '[00:00:01] Se habló de la preparación del equipo.',
        '[00:08:02] Les recordamos que la orientación es el sábado. Se habló de cómo explicar la orientación.',
        '[00:17:03] El comité aprobó USD 2,400 para materiales.',
        '[00:23:04] Ana Ruiz se comprometió a enviar el inventario el viernes.',
        '[00:29:05] Yo debería hablar de otra actividad más adelante.',
    ))
    draft = 'Equipo | Preparación [E1] [E2]'
    prose_calls = []

    def stub(messages, *args, json_output, **kwargs):
        if json_output:
            if 'items' in json_output['properties']:
                return json.dumps({'items':[{
                    'category':'proposal',
                    'sources':[{'id':5,'quote':'Yo debería hablar de otra actividad más adelante.'}],
                    'text_es':'Se propuso conversar sobre otra actividad.',
                    'owner':None, 'due':None,
                }]})
            return json.dumps({'themes':[
                {'source_ids':[1], 'title_es':'Preparación del equipo',
                 'summary_es':'Se habló de la preparación del equipo.'},
                {'source_ids':[2], 'title_es':'Orientación',
                 'summary_es':'Se habló de cómo explicar la orientación.'},
            ]})
        prose_calls.append(messages)
        assert 'Owll' in messages[0]['content']
        return draft if len(messages)==2 else revision

    monkeypatch.setattr(summarize,'ollama_chat',stub)
    evidence = {}
    report = summarize.summarize_local(transcript,'both','es','qwen3:4b',evidence_sink=evidence.update)
    assert len(prose_calls)==2
    assert prose_calls[1][:2]==prose_calls[0]
    assert prose_calls[1][2]=={'role':'assistant','content':draft}
    assert not any(line.lstrip().startswith('|') for line in report.splitlines())
    assert 'USD 2,400' in report and 'Ana Ruiz' in report and 'viernes' in report
    assert '## Avisos' in report and '[00:08:02]' not in report
    assert any(ref['timestamp']=='00:08:02' for item in evidence['items'] for ref in item['sources'])
    assert '## Propuestas' not in report
    assert any(item['category']=='review' for item in evidence['items'])
    if accepted:
        assert 'La sesión trató la preparación del equipo.' in report
        assert 'Se habló de cómo explicar la orientación.' in report
        assert not evidence['narrative_fallbacks']
    else:
        assert 'Se habló de la preparación del equipo.' in report
        assert 'Se habló de cómo explicar la orientación.' in report
        assert evidence['narrative_fallbacks']==[{'language':'es','theme_ids':[1,2]}]
        assert 'Parte de la revisión editorial no se completó.' in report


def test_standalone_decision_stays_in_record_and_does_not_displace_later_topics():
    from engine.minutes_brief import editorial_request

    items=[make_item(1,'decision'),make_item(2,'decision')]
    original=items[0]['sources'][0]['quote']='Se aprobó la compra.'
    items[1]['sources'][0]['quote']=original
    block=[
        {'id':1,'timestamp':'00:00:01','text':original},
        {'id':2,'timestamp':'00:00:02','text':original+' Luego trataron atención a visitantes.'},
        *({'id':i,'timestamp':f'00:00:{i:02d}','text':f'Se habló del tema {i}.'} for i in range(3,8)),
    ]
    sources=next(editorial_input([block],items))
    assert [ref['source_id'] for ref in sources]==[2,3,4,5,6,7]
    _,schema=editorial_request(sources,'es')
    assert schema['properties']['themes']['maxItems']==6


@pytest.mark.parametrize('wording',[
    'El inventario se enviará antes del viernes.',
    'Se implementará el registro de incidentes.',
])
def test_edited_prose_cannot_invent_deadline_or_implementation(wording):
    from engine.minutes_narrative import narrative_sections, validate_narrative

    source={'source_id':1, 'timestamp':'00:01:02',
            'quote':'Ana enviará el inventario el viernes. Se explicó cómo registrar incidentes.'}
    theme={'title_es':'Seguimiento','summary_es':source['quote'],'sources':[source]}
    section=next(narrative_sections([theme],'es'))
    with pytest.raises(ValueError,match='deadline or implementation'):
        validate_narrative(wording+' [E1]',section,'es')


@pytest.mark.parametrize(('language', 'rows', 'titles', 'merged', 'heading'), [
    ('es', (
        'Ya empezaremos el mes de abril con talleres de lectura. Se habló de la distribución de libros.',
        'Se revisó el material de apoyo.',
        'Este mes reservamos los sábados.',
        'Para realizar las prácticas en la biblioteca.',
    ), ('Distribución de libros', 'Material de apoyo'),
        'Las prácticas en la biblioteca serán los sábados de abril.', '## Avisos'),
    ('en', (
        'We will start in April with reading workshops. The team discussed distributing books.',
        'The team reviewed the reference materials.',
        'This month we reserved the Saturdays.',
        'To hold the practice sessions in the library.',
    ), ('Book distribution', 'Reference materials'),
        'Library practice will take place on Saturdays in April.', '## Announcements'),
])
def test_local_minutes_keep_calendar_notices_out_of_prose_rewriting(
    monkeypatch, language, rows, titles, merged, heading
):
    from engine import summarize

    start, discussion = rows[0].split('. ', 1)
    start += '.'
    evidence = {}
    editorial_sources = []
    prose_input = []

    def stub(messages, *args, json_output, **kwargs):
        if json_output:
            if 'items' in json_output['properties']:
                return '{"items": []}'
            sources = json.loads(messages[1]['content'])['sources']
            editorial_sources.extend(sources)
            quotes = {source['id']: source['quote'] for source in sources}
            themes = [
                {'source_ids':[key], f'title_{language}':title, f'summary_{language}':quotes[key]}
                for key,title in zip((1,2),titles)
            ]
            if 3 in quotes and 4 in quotes:
                themes.insert(0, {'source_ids':[1,3,4], f'title_{language}':'Calendario' if language=='es' else 'Calendar',
                                  f'summary_{language}':merged})
            return json.dumps({'themes':themes})
        prose = json.loads(messages[1]['content'])
        prose_input.extend(prose.values())
        return '\n\n'.join(f"{entry['summary']} [{key}]" for key,entry in prose.items())

    transcript = '\n'.join(f'[00:00:{i:02d}] {row}' for i,row in enumerate(rows,1))
    monkeypatch.setattr(summarize,'ollama_chat',stub)
    report = summarize.summarize_local(
        transcript, 'both', language, 'qwen3.8:27b', evidence_sink=evidence.update,
    )
    summary, notices = report.split(heading, 1)
    assert editorial_sources == [{'id':1,'quote':discussion}, {'id':2,'quote':rows[1]}]
    assert len(prose_input) == 4
    assert all(entry['quotes'] in ([rows[1]], [discussion]) for entry in prose_input)
    assert not evidence['narrative_fallbacks']
    assert rows[1] in summary and discussion in summary
    assert merged not in report
    assert all(report.count(quote) == 1 and quote in notices for quote in (start, rows[2], rows[3]))
    assert '00:00:' not in report and '|' not in report
    assert all(item['category'] == 'notice' for item in evidence['items'])
    assert [[ref['source_id'] for ref in item['sources']] for item in evidence['items']] == [[1], [3,4]]


@pytest.mark.parametrize('first, expected_error', [
    ('Se revisó la lista de materiales', None),
    ('Se revisó un gasto de USD 2,000', 'Unsupported number or amount'),
])
@pytest.mark.parametrize('first_end, punctuation', [
    (' [E1].', '.'), ('. [E1]', '.'), (' [E1],', ','), (' [E1];', ';'),
])
def test_revised_paragraph_validates_citations_at_sentence_boundaries(first, expected_error, first_end, punctuation):
    from engine.minutes_narrative import narrative_sections, validate_narrative

    instructions = (
        (4, 'Materiales', 'Se revisó la lista de materiales.'),
        (8, 'Finanzas', 'El presupuesto es de USD 2,000.'),
    )
    themes = [
        {'title_es': title, 'summary_es': quote,
         'sources':[{'source_id':row, 'timestamp':'00:01:02', 'quote':quote}]}
        for row,title,quote in instructions
    ]
    section = next(narrative_sections(themes, 'es'))
    raw = f'{first}{first_end} El presupuesto es de USD 2,000 [E2].'
    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            validate_narrative(raw, section, 'es')
        return
    assert validate_narrative(raw, section, 'es') == [{
        'text': f'Se revisó la lista de materiales{punctuation} El presupuesto es de USD 2,000.',
        'sources': [themes[0]['sources'][0], themes[1]['sources'][0]],
    }]


@pytest.mark.parametrize('language, budget, discussion, amount, implied_use', [
    ('es', 'El presupuesto es de USD 2,400.', 'Se habló de la distribución de libros.',
     'USD 2,400', 'Se asignó el monto a los libros'),
    ('en', 'The budget is USD 2,400.', 'The team discussed distributing books.',
     'USD 2,400', 'The amount was earmarked for books'),
])
def test_standalone_budget_stays_verbatim_and_does_not_enter_the_editorial_input(
    language, budget, discussion, amount, implied_use
):
    from engine.minutes_evidence import explicit_source_items, reconcile_source_items, source_blocks

    blocks = list(source_blocks(f'[00:01:02] {budget} {discussion}'))
    explicit = explicit_source_items(blocks[0], language)
    assert len(explicit) == 1 and explicit[0]['category'] == 'topic'
    model_budget = {**explicit[0], f'text_{language}':implied_use}
    items = reconcile_source_items([model_budget], explicit)
    assert items == explicit
    excerpts = list(editorial_input(blocks, items, explicit_items=explicit))
    assert excerpts[0][0]['quote'] == discussion
    report = render_minutes(items, 'minutes', language, show_timestamps=False)
    assert report.count(amount) == 1 and budget in report
    assert implied_use not in report

