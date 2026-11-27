import json
import pytest
from engine.minutes_brief import validate_editorial,editorial_modality_error

@pytest.mark.parametrize('source,wording',[
    ('Se habló de preparar ejemplos que ayuden a los voluntarios a distinguir preguntas frecuentes de solicitudes excepcionales.',
     'Se propuso elaborar materiales que ayuden a los voluntarios a diferenciar preguntas frecuentes y solicitudes excepcionales.'),
    ('Se habló de revisar la claridad de las observaciones recibidas durante las actividades.',
     'Se propuso revisar la claridad de las observaciones recibidas durante las actividades.'),
    ('The group discussed reviewing the guidance notes.',
     'The group proposed reviewing the guidance notes.'),
])
def test_discussion_not_proposal(source,wording):
    refs=[{'source_id':1,'timestamp':'00:00:01','quote':source}]
    lang='en' if source.startswith('The') else 'es'
    raw=json.dumps({'themes':[{'source_ids':[1],'title_'+lang:'Guidance' if lang=='en' else 'Orientación',
                              'summary_'+lang:wording}]})
    rejected=[]
    assert validate_editorial(raw,refs,lang,rejected=rejected)==[]
    assert rejected==refs
    assert editorial_modality_error(wording,refs)

@pytest.mark.parametrize('source,wording',[
    ('Se habló de revisar la claridad de las observaciones.','Se habló de revisar la claridad de las observaciones.'),
    ('Se habló de la propuesta de ampliar horarios.','Se habló de la propuesta de ampliar horarios.'),
    ('Se habló de una dificultad y se propuso revisar el manual.','Se propuso revisar el manual.'),
    ('El comité propuso extender el horario.','Se propuso extender el horario.'),
    ('Se explicó qué significa una recomendación.','Se explicó el significado de una recomendación.'),
])
def test_preserve_explicit_proposals_and_discussion(source,wording):
    assert editorial_modality_error(wording,[{'quote':source}]) is None
