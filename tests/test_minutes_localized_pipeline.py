import json
import pytest
from engine import summarize
from engine.control import JobCancelled
from engine.minutes_localization import localize_items
from engine.minutes_evidence import _LOCALES

SOURCE='Ana Ruiz will send the access draft by Friday.'
TRANSCRIPT='[00:00:01] '+SOURCE

@pytest.mark.parametrize('response,accepted',[
    ('Ana Ruiz enviará el borrador de acceso antes del viernes.',True),
    ('Ana Ruiz enviará el borrador de acceso antes del lunes.',False),
])
def test_localized_pipeline_keeps_evidence_and_corrects_only_protected_day(monkeypatch,response,accepted):
    calls=[];evidence={}
    def stub(messages,*args,json_output,**kwargs):
        calls.append(json_output)
        if 'items' in json_output['properties']:
            return json.dumps({'items':[{'category':'action','owner':'Ana Ruiz','due':'Friday',
                'sources':[{'id':1,'quote':SOURCE}],'text_es':_LOCALES['es']['source_only']}]})
        assert 'translations' in json_output['properties']
        return json.dumps({'translations':[{'id':0,'text':response}]})
    monkeypatch.setattr(summarize,'ollama_chat',stub)
    report=summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',
            evidence_sink=evidence.update,narrative_strategy='localized_editorial')
    assert len(calls)==2
    assert evidence['items'][0]['due']=='Friday'
    assert evidence['items'][0]['sources'][0]['quote']==SOURCE
    assert evidence['items'][0]['text_es']==_LOCALES['es']['source_only']
    assert bool(evidence['localization'][0]['accepted'])==accepted
    assert bool(evidence['localization'][0]['rejected'])!=accepted
    assert SOURCE in report and 'Fecha o plazo mencionado: viernes' in report
    if accepted:
        assert 'a más tardar el viernes' in report and 'antes del viernes' not in report
        assert evidence['localization'][0]['protected_weekdays']==[0]
    else:
        assert 'No se pudo traducir fielmente' in report and 'lunes' not in report

def test_localization_transport_failure_retains_source_and_diagnostic():
    item={'category':'action','owner':'Ana Ruiz','due':'Friday',
          'sources':[{'source_id':1,'timestamp':'00:00:01','quote':SOURCE}],
          'text_es':'Enviar el borrador de acceso.'}
    def fail(*args,**kwargs):
        raise RuntimeError('model unavailable')
    displayed,result=localize_items([item],'es',fail)
    assert displayed[0]['text_es']==_LOCALES['es']['source_only']
    assert result['rejected'] and item['text_es']=='Enviar el borrador de acceso.'

def test_localization_cancellation_is_not_swallowed():
    item={'category':'action','owner':'Ana Ruiz','due':'Friday',
          'sources':[{'source_id':1,'timestamp':'00:00:01','quote':SOURCE}],
          'text_es':_LOCALES['es']['source_only']}
    def fail(*args,**kwargs):
        raise JobCancelled()
    with pytest.raises(JobCancelled):
        localize_items([item],'es',fail)
