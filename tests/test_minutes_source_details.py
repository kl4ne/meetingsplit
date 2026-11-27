import json
import pytest
from engine.minutes_source_details import compose_details,detail_markdown
from engine.control import JobCancelled
def ref(i,text):
    return {'source_id':i,'timestamp':'00:00:00','quote':text}
ES='Se habló de revisar la claridad de las observaciones recibidas durante las actividades.'
EN='Visitors who need assistance can use the entrance ramp. The discussion covered how to describe accessible routes without disclosing private contact information.'
TARGET=['Los visitantes que necesitan asistencia pueden utilizar la rampa de entrada.',
        'Se habló de cómo describir rutas accesibles sin divulgar datos privados de contacto.']
def test_literal_source_no_request():
    def no(*a):raise AssertionError('literal source requires no model')
    r=compose_details([ref(1,ES)],'es',no)
    assert r['requests']==0 and r['records'][0]['text_es']==ES
    assert r['records'][0]['sources']==[ref(1,ES)]
def test_one_translation_request_with_separate_sentence_ids():
    calls=[]
    def reply(messages,schema):
        calls.append(json.loads(messages[1]['content']))
        return json.dumps({'translations':[{'id':1,'text':TARGET[0]},{'id':2,'text':TARGET[1]}]})
    r=compose_details([ref(1,ES),ref(2,EN)],'es',reply)
    assert len(calls)==r['requests']==1 and not r['rejected']
    assert [x['source'] for x in calls[0]['records']]==[EN.split('. ')[0]+'.',EN.split('. ')[1]]
    assert [x['text_es'] for x in r['records']]==[ES,*TARGET]
    assert r['records'][1]['sources'][0]['quote']==EN.split('. ')[0]+'.'
    assert r['records'][2]['sources'][0]['quote']==EN.split('. ')[1]
    assert r['review_required'] and 'Cita original' in detail_markdown(r)
def test_negation_rejected_and_source_preserved():
    def reply(*a):
        return json.dumps({'translations':[{'id':0,'text':TARGET[0]},
            {'id':1,'text':'Se habló de describir las rutas accesibles divulgando datos privados de contacto.'}]})
    r=compose_details([ref(2,EN)],'es',reply)
    assert len(r['rejected'])==1 and r['records'][1]['status']=='source_only'
    assert 'without disclosing' in r['records'][1]['text_es']
    assert 'Sin traducción validada' in detail_markdown(r)
def test_transport_failure_no_retry():
    calls=[]
    def fail(*a):
        calls.append(1);raise RuntimeError('timeout')
    r=compose_details([ref(2,EN)],'es',fail)
    assert len(calls)==1 and len(r['rejected'])==2
def test_over_budget_preserves_all():
    r=compose_details([ref(i,EN) for i in range(3)],'es',lambda *a:pytest.fail('too many sentences'))
    assert r['requests']==0 and len(r['records'])==6 and len(r['rejected'])==6
def test_cancellation_propagates():
    def stop(*a):raise JobCancelled()
    with pytest.raises(JobCancelled):compose_details([ref(2,EN)],'es',stop)
