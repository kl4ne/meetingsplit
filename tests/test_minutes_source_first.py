import json
import pytest
from qa.minutes_source_first import source_units,validate_grouping,compose_groups,translate_units
from engine.minutes_evidence import source_blocks

def test_units_preserve_compound_sentence_and_multiple_sentences():
    blocks=list(source_blocks('[00:00:01] La información debe estar en el mostrador; se distinguió el registro.\n[00:00:02] Visitors can use the entrance ramp. The guide describes accessible routes.'))
    u=source_units(blocks,[],[],'es')
    assert len(u)==3 and [x['source']['source_id'] for x in u]==[1,2,2]
    assert ';' in u[0]['text'] and 'entrance ramp' in u[1]['text']

def test_group_plan_exactly_once_preserves_text_and_sorting():
    units=[{'id':i,'source':{'source_id':i,'quote':f'Source {i}'},'text':f'Texto {i}.','status':'literal'} for i in range(1,5)]
    raw=json.dumps({'groups':[{'title':'Archivo','unit_ids':[4,3],'overview_id':4},
                              {'title':'Recepción','unit_ids':[2,1],'overview_id':1}]})
    groups=validate_grouping(raw,units,'es')
    themes,brief=compose_groups(groups,units,'es')
    assert themes[0]['summary_es']=='Texto 1. Texto 2.'
    assert themes[1]['summary_es']=='Texto 3. Texto 4.'
    assert brief==['Texto 1.','Texto 4.']

@pytest.mark.parametrize('groups',[
    [{'title':'Archivo','unit_ids':[1],'overview_id':1}],
    [{'title':'Archivo','unit_ids':[1,2,2],'overview_id':1}],
    [{'title':'Archivo','unit_ids':[1,3],'overview_id':1}],
    [{'title':'Archivo','unit_ids':[1],'overview_id':2},{'title':'Recepción','unit_ids':[2],'overview_id':2}],
    [{'title':'Se aprobó','unit_ids':[1,2],'overview_id':1}],
])
def test_invalid_plan_rejected(groups):
    with pytest.raises(ValueError):
        validate_grouping(json.dumps({'groups':groups}),[{'id':1},{'id':2}],'es')

def test_translation_failure_preserves_original_unit():
    u=[{'id':1,'source':{'source_id':1,'quote':'Visitors can use the entrance ramp.'},'text':'Visitors can use the entrance ramp.','status':'needs_translation'}]
    def fail(*args,**kwargs):return '{"translations":[{"id":0,"text":"Se aprobó eliminar la rampa."}]}'
    copies,bad,calls=translate_units(u,'es',fail)
    assert calls==1 and bad and copies[0]['status']=='source_only' and copies[0]['text']==u[0]['text']
    assert u[0]['status']=='needs_translation'
