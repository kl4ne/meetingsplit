"""Regressions from actual run 45955174164; no model call."""
import pytest
from engine.minutes_narrative import narrative_sections,validate_narrative,recover_narrative
from engine.minutes_evidence import explicit_source_items,source_blocks,render_minutes

def section():
    data=[
        ('Objetivo de la reunión','El equipo revisó la capacitación de voluntarios y atención a visitantes.'),
        ('Orientación e inventario','Se discutió la distribución de libros y el mantenimiento del inventario ordenado.'),
        ('Manejo de materiales confidenciales','La guía distingue notas confidenciales y materiales públicos.'),
        ('Preparación de ejemplos','Se habló de preparar ejemplos y revisar su claridad antes de la próxima capacitación.'),
    ]
    themes=[{'title_es':title,'summary_es':text,'sources':[{'source_id':i,'timestamp':f'00:00:0{i}','quote':text}]}
            for i,(title,text) in enumerate(data,1)]
    return next(narrative_sections(themes,'es'))

def test_unrelated_citation_cannot_suppress_confidentiality_or_examples():
    sec=section()
    # The real model attached IDs for confidentiality and examples to a
    # paragraph solely about inventory. Remapped IDs for this minimal fixture.
    bad='Se abordó la distribución de libros y el inventario ordenado [E2] [E3] [E4].'
    with pytest.raises(ValueError,match='distinctive theme anchor'):
        validate_narrative(bad,sec,'es')
    recovered,selection=recover_narrative(sec,'es',revised=bad)
    assert selection['themes']==[1,2,3,4]
    assert any('confidenciales' in p['text'] for p in recovered)
    assert any('ejemplos' in p['text'] for p in recovered)

def test_genuine_multi_theme_prose_is_retained():
    sec=section()
    raw='La distribución de libros y el inventario ordenado fueron discutidos. [E2]\n\nLa guía distingue notas confidenciales de los materiales públicos. [E3]'
    _,selection=recover_narrative(sec,'es',revised=raw)
    assert selection['review']==[2,3]
    assert selection['themes']==[1,4]

@pytest.mark.parametrize('lang,source,expected',[
    ('es','The budget is USD 2,400.','El presupuesto es de USD 2,400.'),
    ('en','El presupuesto es de 800 pesos.','The budget is 800 pesos.'),
])
def test_literal_standalone_budget_localized_without_inventing_allocation(lang,source,expected):
    items=explicit_source_items(next(source_blocks('[00:00:01] '+source)),lang)
    assert items[0]['text_'+lang]==source
    report=render_minutes(items,'both',lang,show_timestamps=False)
    assert '- '+expected in report
    assert '"'+source+'"' in report
    assert items[0]['sources'][0]['quote']==source

def test_literal_nonapproval_is_not_presented_as_foreign_language_prose():
    source='Proposal only: extend the reception hours to Sunday. Not approved.'
    items=explicit_source_items(next(source_blocks('[00:00:01] '+source)),'es')
    report=render_minutes(items,'both','es',show_timestamps=False)
    assert '- Propuesta sin aprobación confirmada' in report
    assert 'Cita literal de la fuente:' in report and '"Not approved."' in report
    assert '- '+source not in report
