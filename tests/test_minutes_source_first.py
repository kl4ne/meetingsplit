import json
import pytest
from engine.minutes_source_first import source_units,validate_grouping,compose_groups,translate_units
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


from engine.minutes_source_first import plan_grouping_repair,grouping_repair_request,apply_grouping_repair

def test_bounded_repair_preserves_fixed_partition():
    units=[{'id':i,'text':f'Texto {i}.'} for i in range(1,9)]
    raw=json.dumps({'groups':[{'title':'Archivo','unit_ids':[1,2,3,4],'overview_id':3},
                              {'title':'Recepción','unit_ids':[3,5,6,7],'overview_id':5}]})
    plan=plan_grouping_repair(raw,units,'es')
    assert plan['disputed']==[3,8] and plan['duplicates']==[3] and plan['missing']==[8]
    assert plan['fixed'][0]['overview_id']==1
    messages,schema=grouping_repair_request(plan,units,'es')
    assert [u['id'] for u in json.loads(messages[1]['content'])['disputed_units']]==[3,8]
    groups=apply_grouping_repair(json.dumps({'assignments':[{'unit_id':3,'group_id':2},{'unit_id':8,'group_id':1}]}),plan,units,'es')
    assert groups[0]['unit_ids']==[1,2,4,8] and groups[1]['unit_ids']==[3,5,6,7]
    assert plan['fixed'][0]['unit_ids']==[1,2,4]
    for bad in ([{'unit_id':3,'group_id':1},{'unit_id':3,'group_id':2}],
                [{'unit_id':1,'group_id':1},{'unit_id':8,'group_id':2}],
                [{'unit_id':3,'group_id':99},{'unit_id':8,'group_id':1}]):
        with pytest.raises(ValueError):
            apply_grouping_repair(json.dumps({'assignments':bad}),plan,units,'es')

def test_unbounded_or_unanchored_group_repair_rejected():
    units=[{'id':i} for i in range(1,9)]
    for groups in ([{'title':'Archivo','unit_ids':[1,2],'overview_id':1}],
                   [{'title':'Archivo','unit_ids':[1,2,3,4,5,6,7],'overview_id':1},
                    {'title':'Recepción','unit_ids':[1],'overview_id':1}],
                   [{'title':'Se aprobó','unit_ids':[1,2,3,4,5,6,7],'overview_id':1}]):
        with pytest.raises(ValueError):
            plan_grouping_repair(json.dumps({'groups':groups}),units,'es')


def test_grouping_fallback_retains_every_unit_and_warns():
    from engine.minutes_source_first import compose_source_first
    blocks=list(source_blocks('[00:00:01] Se explicó el uso de materiales de consulta.\n[00:00:02] Se habló de revisar los documentos de trabajo.'))
    def fail(*args,**kwargs):
        return '{"groups":[]}'
    out=compose_source_first(blocks,[],[],'es',fail)
    assert out['grouping_failures'] and len(out['units'])==2
    assert all(u['text'] in out['themes'][0]['summary_es'] for u in out['units'])

def test_long_grouping_windows_bounded_and_complete():
    from engine.minutes_source_first import compose_source_first
    text='\n'.join(f'[00:{i//60:02d}:{i%60:02d}] Se habló de revisar el documento de trabajo {i}.' for i in range(123))
    blocks=list(source_blocks(text));calls=[]
    def plan(messages,schema,**kw):
        ids=kw['scope']['unit_ids'];calls.append(ids)
        groups=[{'title':'Documentos de trabajo '+('local' if j==0 else 'general'),
                 'unit_ids':ids[j:j+20],'overview_id':ids[j]} for j in range(0,len(ids),20)]
        return json.dumps({'groups':groups})
    out=compose_source_first(blocks,[],[],'es',plan)
    assert all(len(ids)<=40 for ids in calls) and len(calls)>=4
    assert len(out['units'])==123
    assert sorted(i for w in out['windows'] for g in w['groups'] for i in g['unit_ids'])==list(range(1,124))

def test_optional_real_engine_path_preserves_bilingual_units_and_fallbacks(monkeypatch):
    from engine import summarize
    transcript='[00:00:01] Se explicó el uso de materiales de consulta.\n[00:00:02] The guide describes the accessible routes in the building.'
    calls=[];evidence={}
    def fake(messages,*args,json_output,**kwargs):
        p=json.loads(messages[1]['content']);calls.append(p)
        if 'source_rows' in p:return '{"items":[]}'
        if 'records' in p:
            result=[]
            spanish='into Spanish.' in messages[0]['content']
            for r in p['records']:
                result.append({'id':r['id'],'text':'La guía describe las rutas accesibles.' if spanish else 'The use of reference materials was explained.'})
            return json.dumps({'translations':result})
        if 'units' in p:
            ids=[u['id'] for u in p['units']]
            return json.dumps({'groups':[{'title':'Orientación' if 'Spanish.' in messages[0]['content'] else 'Guidance','unit_ids':ids,'overview_id':ids[0]}]})
        pytest.fail('Unexpected request')
    monkeypatch.setattr(summarize,'ollama_chat',fake)
    report=summarize.summarize_local(transcript,'both','both','qwen3.5:9b',
        evidence_sink=evidence.update,narrative_strategy='source_first')
    assert len(evidence['source_first'])==2
    assert all(len(d['units'])==2 and not d['translation_rejected'] and not d['grouping_failures'] for d in evidence['source_first'])
    assert '## Temas tratados' in report and '## Topics discussed' in report
    assert 'La guía describe las rutas accesibles.' in report and 'The use of reference materials was explained.' in report
    assert evidence['narrative_strategy']=='source_first'
