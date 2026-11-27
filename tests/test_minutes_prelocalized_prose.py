import json
import pytest
from engine.minutes_prelocalized_prose import compose,prepare
def unit(i,text,original=None):
    return {'id':i,'source':{'source_id':i,'timestamp':'00:00:00','quote':original or text},
        'text':text,'status':'translated' if original else 'literal'}
ES='El equipo examinó la entrada y los baños accesibles sin divulgar datos privados.'
EN='The team examined the entrance and accessible restrooms without disclosing private data.'
OTHER='Se habló de revisar las instrucciones para las familias.'
def groups():
    return [{'id':'g1','units':[unit(1,ES,EN)]},{'id':'g2','units':[unit(2,OTHER)]}]
def test_one_call_no_translation_and_original_preserved():
    calls=[]
    def request(msg,schema):
        calls.append(msg)
        assert EN not in msg[1]['content']
        assert schema['required']==['g1','g2']
        return json.dumps({'g1':ES,'g2':OTHER})
    out=compose(groups(),'es',request)
    assert len(calls)==out['requests']==1
    assert all(g['status']=='candidate_semantic_review' for g in out['groups'])
    assert out['groups'][0]['units'][0]['source']['quote']==EN and out['review_required']
@pytest.mark.parametrize('bad',[
    'El equipo examinó la entrada y los baños accesibles divulgando datos privados.',
    'Se aprobó examinar la entrada y los baños accesibles sin divulgar datos privados.',
    'The team examined the entrance and the restrooms without disclosing private data.',
    'El equipo examinó 2 entradas y los baños accesibles sin divulgar datos privados.',
])
def test_bad_group_fallback_other_preserved(bad):
    out=compose(groups(),'es',lambda *a:json.dumps({'g1':bad,'g2':OTHER}))
    assert out['groups'][0]['candidate'] is None
    assert out['groups'][0]['baseline']==ES
    assert out['groups'][1]['candidate']==OTHER
def test_bad_schema_preserves_all():
    out=compose(groups(),'es',lambda *a:'{"g1":"x"}')
    assert all(g['status']=='fallback_original' for g in out['groups'])
def test_repeated_id_and_untranslated_source_rejected_before_inference():
    g=groups();g[1]['units'][0]['id']=1
    with pytest.raises(ValueError):prepare(g,'es')
    g=groups();g[0]['units'][0]['status']='source_only'
    with pytest.raises(ValueError):prepare(g,'es')
def test_wrong_day_relation_is_rejected():
    t='El formulario estará disponible el viernes.'
    g=[{'id':'g1','units':[unit(1,t)]}]
    out=compose(g,'es',lambda *a:json.dumps({'g1':'El formulario estará disponible antes del viernes.'}))
    assert out['groups'][0]['candidate'] is None
def test_no_retry_on_transport_error():
    calls=[]
    def fail(*a):
        calls.append(1);raise RuntimeError('timeout')
    out=compose(groups(),'es',fail)
    assert len(calls)==1 and all(g['status']=='fallback_original' for g in out['groups'])

def test_prior_translation_negative_knowledge_paraphrase():
    original='Se habló de preparar ejemplos de atención respetuosa para personas que no conocen los servicios disponibles.'
    text='Discussion focused on preparing examples of respectful service engagement for individuals unfamiliar with available services.'
    g=[{'id':'g1','units':[unit(1,text,original)]}]
    assert prepare(g,'en')[0]['g1']==[text]
