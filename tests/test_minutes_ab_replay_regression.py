"""Regression from synthetic A/B run 45951175096, artifact 15177746760.

Exact captured offending theme and reviewed clause; no new model calls.
"""
import json
import pytest
from engine.minutes_brief import validate_editorial
from engine.minutes_evidence import (editorial_decision_error, explicit_source_items,
    find_coverage_gaps, source_blocks, changes_operational_meaning)
from engine.minutes_narrative import narrative_sections, validate_narrative
from qa.minutes_editorial_ab import TRANSCRIPT

ROWS=[r for block in source_blocks(TRANSCRIPT) for r in block]
SOURCES=[{'source_id':r['id'],'timestamp':r['timestamp'],'quote':r['text']}
         for r in ROWS if r['id'] in (1,2,3,7,8,11,12)]
CAPTURED_THEME={
    'source_ids':[2,7,12],
    'title_es':'Temas tratados: orientación e inventario',
    'summary_es':'Se explicaron procedimientos sobre la distribución de libros, el mantenimiento del inventario ordenado y las técnicas para orientar a los visitantes hacia recepción con respeto; además, se acordó preparar ejemplos prácticos de atención antes de la próxima sesión.',
}
CAPTURED_REVIEW='Se presentó una propuesta para extender las horas de recepción hasta el domingo; sin embargo, esto fue rechazado y no se convirtió en decisión oficial o acuerdo aprobado [E1].'
SAFE_NON_APPROVAL='Se presentó una propuesta para extender las horas de recepción hasta el domingo, sin aprobación [E1].'

def test_exact_captured_theme_rejected_without_losing_neighbor():
    good={'source_ids':[1],'title_es':'Objetivo de la reunión',
          'summary_es':'El equipo revisó la capacitación de voluntarios y la atención a visitantes.'}
    rejected=[];reasons=[]
    accepted=validate_editorial(json.dumps({'themes':[good,CAPTURED_THEME]}),
                SOURCES,'es',rejected=rejected,
                on_rejection=lambda theme,exc:reasons.append(str(exc)))
    assert len(accepted)==1 and accepted[0]['title_es']==good['title_es']
    assert [r['source_id'] for r in rejected]==[2,7,12]
    assert reasons==['Formal decisions belong in the separate evidence section']

def test_exact_review_rejection_distinguished_from_non_approval():
    theme={'title_es':'Propuesta no aprobada','summary_es':'Se propuso extender la recepción al domingo, sin aprobación.',
           'sources':[r for r in SOURCES if r['source_id']==8]}
    section=next(narrative_sections([theme],'es'))
    with pytest.raises(ValueError,match='Rejection is not supported'):
        validate_narrative(CAPTURED_REVIEW,section,'es')
    assert validate_narrative(SAFE_NON_APPROVAL,section,'es')[0]['text'].endswith('sin aprobación.')
    assert validate_narrative('No se convirtió en decisión oficial o acuerdo aprobado [E1].',section,'es')

@pytest.mark.parametrize('value,source',[
    ('Se aprobó la propuesta.','Proposal only. Not approved.'),
    ('No se aprobó el piloto, pero se aprobó la compra.','The pilot was not approved.'),
    ('The committee not only approved the pilot.','The pilot was not approved.'),
    ('No se aprobó la propuesta.','Se presentó una propuesta.'),
    ('La propuesta fue rechazada.','Proposal only. Not approved.'),
])
def test_unsupported_or_positive_agreement_still_rejected(value,source):
    assert editorial_decision_error(value,source)

def test_not_approved_does_not_authorize_implementation():
    assert changes_operational_meaning('Se implementará el piloto.','The pilot was not approved.')

def test_non_approval_stays_with_proposal_without_false_missing_agreement():
    rows=list(source_blocks('[00:07:00] Proposal only: extend the reception hours to Sunday. Not approved.'))[0]
    items=explicit_source_items(rows,'es')
    assert len(items)==1 and items[0]['category']=='proposal'
    assert [r['quote'] for r in items[0]['sources']]==['Proposal only: extend the reception hours to Sunday.','Not approved.']
    assert not find_coverage_gaps(rows,items)
    positive=list(source_blocks('[00:00:01] The board approved the pilot.'))[0]
    assert find_coverage_gaps(positive,[])[0]['kind']=='agreement'
