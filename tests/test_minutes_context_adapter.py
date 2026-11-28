"""Mocked end-to-end QA adapter; no calls to a running model."""
import json
import pytest
from engine import summarize
from engine.control import JobCancelled
from engine.minutes_evidence import source_blocks
from engine.minutes_context_windows import plan_context
from engine.minutes_context_adapter import contextual_editorial

TEXT='\n'.join([
    '[00:00:01] Se explicó cómo conservar',
    '[00:00:05] las muestras lejos de la luz.',
    '[00:00:09] La humedad también afecta los materiales.',
    '[00:00:31] Se habló de revisar las etiquetas.',
])
ES='Se explicó cómo conservar las muestras lejos de la luz y el efecto de la humedad.'
EN='The discussion explained how to keep the samples away from light and the effects of humidity.'

def stub(language,behavior='ok'):
    calls=[]
    def answer(messages,*args,json_output,**kw):
        props=json_output['properties']
        if 'items' in props:
            calls.append('extraction')
            return '{"items":[]}'
        assert 'review_ids' in props
        calls.append('context')
        if behavior=='cancel':raise JobCancelled()
        if behavior=='timeout':raise RuntimeError('synthetic model timeout')
        if behavior=='malformed':return '{invalid'
        themes=[]
        if behavior!='empty':
            t={'source_ids':[1,2,3]}
            if language in ('es','both'):t.update(title_es='Conservación',summary_es=ES)
            if language in ('en','both'):t.update(title_en='Preservation',summary_en=EN)
            themes.append(t)
        return json.dumps({'themes':themes,'review_ids':[4]})
    return calls,answer

@pytest.mark.parametrize('mode',['summary','minutes','both'])
@pytest.mark.parametrize('lang',['es','en','both'])
def test_complete_context_contract(monkeypatch,mode,lang):
    calls,answer=stub(lang);e={};events=[]
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    report=summarize.summarize_local(TEXT,mode,lang,'qwen3.5:9b',
        narrative_strategy='contextual_qa',evidence_sink=e.update,qa_trace=events.append)
    assert calls==['extraction','context']
    assert e['narrative_strategy']=='contextual_qa' and e['review_required']
    assert e['context_diagnostics']['window_count']==1
    assert [r['source_id'] for r in e['editorial_themes'][0]['sources']]==[1,2,3]
    assert [r['source_id'] for r in e['editorial_gaps']]==[4]
    assert e['source_accounting']['uncited_passages']==[]
    assert 'Se habló de revisar las etiquetas.' in report
    assert '[00:00:' not in report
    assert not any(line.startswith('|') for line in report.splitlines())
    docs=report.split('\n\n---\n\n')
    assert len(docs)==(2 if lang=='both' else 1)
    for doc,l in zip(docs,('es','en') if lang=='both' else (lang,)):
        assert (ES if l=='es' else EN) in doc
        detail='Temas tratados' if l=='es' else 'Topics discussed'
        assert (('## '+detail) in doc)==(mode!='summary')
    assert [x['stage'] for x in events if x['event']=='request']==['extraction','contextual_editorial']

@pytest.mark.parametrize('behavior',['timeout','malformed','empty'])
def test_failed_or_empty_window_keeps_all_sources(monkeypatch,behavior):
    calls,answer=stub('es',behavior);e={}
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    report=summarize.summarize_local(TEXT,'both','es','qwen3.5:9b',
        narrative_strategy='contextual_qa',evidence_sink=e.update)
    assert calls==['extraction','context']
    assert not e['editorial_themes']
    assert [r['source_id'] for r in e['editorial_gaps']]==[1,2,3,4]
    assert all(row['text'] in report for b in source_blocks(TEXT) for row in b)

def test_cancel_not_swallowed(monkeypatch):
    calls,answer=stub('es','cancel');e={}
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    with pytest.raises(JobCancelled):
        summarize.summarize_local(TEXT,'both','es','qwen3.5:9b',
            narrative_strategy='contextual_qa',evidence_sink=e.update)
    assert calls==['extraction','context'] and not e

def test_structured_notice_preserved_and_excluded_from_context(monkeypatch):
    text=TEXT+'\n[00:00:45] Aviso: El material está disponible en recepción.'
    calls=[];e={}
    def answer(messages,*args,json_output,**kw):
        if 'items' in json_output['properties']:
            calls.append('extraction');return '{"items":[]}'
        calls.append('context')
        ids=[r['id'] for u in json.loads(messages[1]['content'])['context_units'] for r in u['fragments']]
        assert ids==[1,2,3,4]
        return json.dumps({'themes':[{'source_ids':[1,2,3],'title_es':'Conservación','summary_es':ES}],
                           'review_ids':[4]})
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    report=summarize.summarize_local(text,'both','es','qwen3.5:9b',
        narrative_strategy='contextual_qa',evidence_sink=e.update)
    assert calls==['extraction','context']
    assert e['context_diagnostics']['structured_source_ids']==[5]
    assert any(i['category']=='notice' and i['sources'][0]['source_id']==5 for i in e['items'])
    assert 'El material está disponible en recepción.' in report

def test_one_failed_window_does_not_erase_other_window():
    blocks=list(source_blocks('\n'.join(f'[00:{i:02d}:00] Texto de prueba número {i}.' for i in range(7))))
    plan=plan_context(blocks);assert len(plan['windows'])==2
    calls=[]
    def answer(messages,schema,*,stage,scope):
        calls.append(scope['window'])
        if scope['window']==1:raise RuntimeError('timeout')
        return json.dumps({'themes':[{'source_ids':scope['source_ids'],'title_es':'Registro',
            'summary_es':'Se leyó el texto de prueba.'}],'review_ids':[]})
    out=contextual_editorial(blocks,[],'es',answer)
    assert calls==[1,2]
    assert len(out['themes'])==1 and len(out['gaps'])==5

def test_legacy_path_does_not_get_context_schema(monkeypatch):
    e={};calls=[]
    def answer(messages,*args,json_output,**kw):
        props=json_output['properties']
        assert 'review_ids' not in props
        calls.append('old')
        if 'items' in props:return '{"items":[]}'
        return json.dumps({'themes':[{'source_ids':[1,2,3,4],
            'title_es':'Conservación','summary_es':ES}]})
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    summarize.summarize_local(TEXT,'both','es','qwen3.5:9b',
        narrative_strategy='localized_editorial',evidence_sink=e.update)
    assert len(calls)==2 and 'context_diagnostics' not in e
