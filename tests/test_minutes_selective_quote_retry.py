"""Synthetic regression for the extra-word quotation defect in run 45951175096."""
import json
import pytest
from engine import summarize
from engine.minutes_evidence import plan_quote_retry,source_blocks,validate_items

LINES=[
    'El equipo se reunió para revisar la capacitación de voluntarios y la atención a visitantes.',
    'Se explicó cómo orientar a los visitantes hacia recepción.',
    'Se revisó la guía de materiales públicos.',
    'Se habló de organizar el inventario.',
    'Se explicó el registro de visitantes.',
    'Se revisaron los ejemplos de capacitación.',
]
TRANSCRIPT='\n'.join(f'[00:00:0{i}] {line}' for i,line in enumerate(LINES,1))
ROWS=next(source_blocks(TRANSCRIPT))

def record(*ids, wrong=False, owner=None):
    refs=[{'id':i,'quote':LINES[i-1]} for i in ids]
    if wrong:
        refs[0]['quote']=refs[0]['quote'].replace('a visitantes','a los visitantes')
    return {'category':'topic','sources':refs,'owner':owner,'due':None,'text_es':'Se revisó el tema.'}

def payload(*items):
    return json.dumps({'items':list(items)})

def test_preserves_disjoint_records_and_retries_only_affected_and_linked_rows():
    raw=payload(record(1,2,wrong=True),record(3),record(4),record(5),record(6))
    with pytest.raises(ValueError,match='not verbatim'):
        validate_items(raw,ROWS,'es')
    kept,subset=plan_quote_retry(raw,ROWS,'es')
    assert [r['id'] for r in subset]==[1,2]
    assert [item['sources'][0]['source_id'] for item in kept]==[3,4,5,6]

def test_overlap_closure_and_uncited_rows_are_not_discarded():
    raw=payload(record(1,wrong=True),record(1,2),record(4),record(5),record(6))
    kept,subset=plan_quote_retry(raw,ROWS,'es')
    assert [r['id'] for r in subset]==[1,2,3]
    assert [item['sources'][0]['source_id'] for item in kept]==[4,5,6]

@pytest.mark.parametrize('raw',[
    'not JSON',
    payload(record(1,wrong=True),record(2,owner='Invented'),record(3),record(4),record(5),record(6)),
    payload(record(1,2,3,wrong=True),record(3,4),record(5),record(6)),
])
def test_does_not_change_full_retry_for_other_errors_or_large_subset(raw):
    assert plan_quote_retry(raw,ROWS,'es') is None

@pytest.mark.parametrize('missing',[False,True])
def test_pipeline_retries_only_two_rows_and_marks_missing_source(monkeypatch,missing):
    calls=[];events=[];evidence={}
    def reply(messages,*args,json_output,**kwargs):
        if 'items' in json_output['properties']:
            ids=[r['id'] for r in json.loads(messages[1]['content'])['source_rows']]
            calls.append(ids)
            if len(calls)==1:
                return payload(record(1,2,wrong=True),record(3),record(4),record(5),record(6))
            assert ids==[1,2]
            return payload(record(1)) if missing else payload(record(1,2))
        return '{"themes":[]}'
    monkeypatch.setattr(summarize,'ollama_chat',reply)
    summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',
                              evidence_sink=evidence.update,qa_trace=events.append)
    assert calls==[[1,2,3,4,5,6],[1,2]]
    assert {r['source_id'] for item in evidence['items'] for r in item['sources']}==set(range(1,7))
    assert any(i['category']=='review' and i['sources'][0]['source_id']==2
               for i in evidence['items'])==missing
    assert any(e['event']=='selective_retry' for e in events)
