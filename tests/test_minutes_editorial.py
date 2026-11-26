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
