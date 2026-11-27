import json
import pytest
from engine.minutes_localization import prepare_presentation,apply_translations,local_day,translation_request
from engine.minutes_evidence import _LOCALES

def item(category,source,owner=None,due=None,text=None):
    return {'category':category,'owner':owner,'due':due,'text_es':text or _LOCALES['es']['source_only'],
        'sources':[{'source_id':1,'timestamp':'00:00:01','quote':source}]}

def test_literal_same_language_fallback_and_foreign_candidate():
    original=[item('action','Inés Ramos se comprometió a enviar el inventario el viernes.','Inés Ramos','el viernes'),
              item('decision','The committee approved the access pilot with a cap of $12,500.')]
    copies,todo=prepare_presentation(original,'es')
    assert copies[0]['text_es']==original[0]['sources'][0]['quote']
    assert todo==[1]
    assert original[0]['text_es']==_LOCALES['es']['source_only']
    raw=json.dumps({'translations':[{'id':1,'text':'El comité aprobó el piloto de acceso con un tope de $12,500.'}]})
    assert apply_translations(raw,copies,todo,'es')==([1],[])
    assert copies[1]['sources']==original[1]['sources']

@pytest.mark.parametrize('text',[
    'El comité aprobó el piloto de acceso con un tope de $15,000.',
    'El comité discutió el piloto de acceso con un tope de $12,500.',
    'El comité aprobó el piloto de acceso con un tope de 12,500 pesos.',
])
def test_reject_changed_fact(text):
    original=[item('decision','The committee approved the access pilot with a cap of $12,500.')]
    copies,todo=prepare_presentation(original,'es')
    ok,bad=apply_translations(json.dumps({'translations':[{'id':0,'text':text}]}),copies,todo,'es')
    assert not ok and bad and copies==original

def test_date_and_owner_remain_literal_fields():
    original=[item('action','Ana Ruiz will send the access draft by Friday.','Ana Ruiz','Friday')]
    copies,todo=prepare_presentation(original,'es')
    raw=json.dumps({'translations':[{'id':0,'text':'Ana Ruiz enviará el borrador de acceso para el viernes.'}]})
    assert apply_translations(raw,copies,todo,'es')==([0],[])
    assert copies[0]['due']=='Friday' and local_day(copies[0]['due'],'es')=='viernes'
    assert copies[0]['owner']=='Ana Ruiz'
    messages,schema=translation_request(original,todo,'es')
    assert json.loads(messages[1]['content'])['records'][0]['source']==original[0]['sources'][0]['quote']
    assert schema['properties']['translations']['maxItems']==1

def test_unknown_translation_id_rejected():
    original=[item('decision','The board approved the pilot.')]
    with pytest.raises(ValueError,match='IDs'):
        apply_translations('{"translations":[{"id":99,"text":"El comité aprobó el piloto."}]}',original,[0],'es')
