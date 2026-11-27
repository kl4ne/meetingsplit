import json,pytest
from qa.minutes_source_first_clauses import clause_request,validate_clauses,compose_lead
RECORDS=[
 {'id':1,'title':'Accesibilidad','units':['La rampa de entrada facilita el acceso de visitantes.'],
  'sources':[{'quote':'La rampa de entrada facilita el acceso de visitantes.'}]},
 {'id':2,'title':'Archivo','units':['Se habló de organizar borradores y documentos finales.'],
  'sources':[{'quote':'Se habló de organizar borradores y documentos finales.'}]},
]
def raw(a,b):return json.dumps({'topics':[{'group_id':1,'phrase':a},{'group_id':2,'phrase':b}]})
def test_complete_clauses_and_deterministic_render():
    good,bad=validate_clauses(raw('la rampa de entrada para los visitantes','la organización de borradores y documentos finales'),RECORDS,'es')
    assert not bad and set(good)=={1,2}
    result=compose_lead(RECORDS,good,'es')[0]
    assert 'rampa' in result and 'borradores' in result and result.startswith('Se abordaron ')
    _,schema=clause_request(RECORDS,'es')
    assert schema['properties']['topics']['minItems']==2

@pytest.mark.parametrize('phrase',[
    'se aprobó la rampa para los visitantes',
    'se propuso ampliar la entrada de visitantes',
    'la organización de borradores y documentos finales',
    'la rampa de entrada para 200 visitantes',
    'rampa',
])
def test_invalid_clause_is_not_silently_dropped(phrase):
    good,bad=validate_clauses(raw(phrase,'la organización de borradores y documentos finales'),RECORDS,'es')
    assert set(good)=={2} and bad[0]['id']==1
    with pytest.raises(ValueError):compose_lead(RECORDS,good,'es')

def test_missing_duplicate_unknown_ids():
    good,bad=validate_clauses(json.dumps({'topics':[{'group_id':1,'phrase':'la rampa de entrada para los visitantes'}]}),RECORDS,'es')
    assert set(good)=={1} and bad==[{'id':2,'reason':'Missing group phrase'}]
    for ids in ([1,1],[1,3]):
        with pytest.raises(ValueError):
            validate_clauses(json.dumps({'topics':[{'group_id':i,'phrase':'la rampa de entrada para los visitantes'} for i in ids]}),RECORDS,'es')
