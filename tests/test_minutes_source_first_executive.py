import json
import pytest
from qa.minutes_source_first_executive import validate_executive,executive_request
RECORDS=[
 {'id':1,'title':'Accesibilidad','units':['Se explicó la rampa de acceso para visitantes.'],
  'sources':[{'quote':'Se explicó la rampa de acceso para visitantes.'}]},
 {'id':2,'title':'Archivo','units':['Se habló de conservar borradores y documentos.'],
  'sources':[{'quote':'Se habló de conservar borradores y documentos.'}]},
]
def raw(text,ids):
    return json.dumps({'paragraphs':[{'text':text,'group_ids':ids}]})
def test_executive_lead_keeps_both_topics():
    result=validate_executive(raw('La reunión abordó la accesibilidad de los visitantes y la conservación de borradores y documentos.',[1,2]),RECORDS,'es')
    assert len(result)==1
    messages,schema=executive_request(RECORDS,'es')
    assert all('sources' not in r for r in json.loads(messages[1]['content'])['groups'])
@pytest.mark.parametrize('text,ids',[
    ('Se habló de conservar borradores y documentos.',[2]),
    ('Se habló de conservar borradores y documentos.',[1,2]),
    ('Se aprobó conservar documentos y mejorar la accesibilidad de visitantes.',[1,2]),
    ('Se propuso conservar documentos y mejorar la accesibilidad de visitantes.',[1,2]),
    ('Se habló de 20 documentos y de accesibilidad para visitantes.',[1,2]),
    ('Se habló de accesibilidad y documentos.',[1,1,2]),
    ('Se habló de accesibilidad y documentos.',[1,3]),
])
def test_invalid_executive_lead_rejected(text,ids):
    with pytest.raises(ValueError):
        validate_executive(raw(text,ids),RECORDS,'es')
