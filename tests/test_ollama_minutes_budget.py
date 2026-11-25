import io
import json

import pytest

from engine import ollama, summarize


def test_evidence_reserves_tokens_and_rejects_a_truncated_json_object(monkeypatch):
    captured=[]
    def open_stream(endpoint, route, payload, cancel):
        captured.append(payload)
        return io.BytesIO(b'{"message":{"content":"{\\"items\\":[]}"},"done":true,"done_reason":"length"}\n')

    monkeypatch.setattr(ollama, '_stream_open', open_stream)
    schema={'type':'object'}
    with pytest.raises(ollama.OutputLimitError, match='output limit'):
        ollama.chat([{'role':'user','content':'source'}], json_output=schema)
    assert captured[0]['think'] is False
    assert captured[0]['format']==schema


def test_over_budget_section_splits_but_a_failed_section_never_yields_a_report(monkeypatch):
    calls=[]
    checkpoints={}
    sinks=[]
    fail_second=True

    def fake_chat(messages, *_args, json_output, **_kwargs):
        rows=json.loads(messages[1]['content'])['source_rows']
        ids=[row['id'] for row in rows]
        assert json_output['properties']['items']['items']['properties']['sources']['items']['properties']['id']['enum']==ids
        calls.append(ids)
        if len(rows)>1 or (fail_second and ids==[2]):
            raise ollama.OutputLimitError('output limit')
        row=rows[0]
        return json.dumps({'items':[{
            'category':'decision','sources':[{'id':row['id'],'quote':row['text']}],
            'owner':None,'due':None,'text_en':row['text'],
        }]})

    monkeypatch.setattr(summarize, 'ollama_chat', fake_chat)
    transcript='[00:00:01] The pilot was approved.\n[00:00:05] The committee approved $500.'
    settings=dict(read_block=checkpoints.get,write_block=checkpoints.__setitem__,evidence_sink=sinks.append)
    with pytest.raises(ollama.OutputLimitError):
        summarize.summarize_local(transcript,'minutes','en',ollama.MODEL,**settings)
    assert calls==[[1,2],[1],[2]]
    assert len(checkpoints)==1 and not sinks

    fail_second=False
    calls.clear()
    report=summarize.summarize_local(transcript,'minutes','en',ollama.MODEL,**settings)
    assert calls==[[1,2],[2]]
    assert '$500' in report
    assert len(sinks[0]['items'])==2 and not sinks[0]['coverage_gaps']


def test_explicit_confirmed_agreement_cannot_be_rendered_as_a_proposal():
    from engine.minutes_evidence import source_blocks, validate_items

    source='Acuerdo confirmado: el piloto se lanza el lunes.'
    rows=next(source_blocks('[00:00:15] '+source))
    item={'category':'proposal','sources':[{'id':1,'quote':source}],
          'owner':None,'due':None,'text_es':'El piloto se lanza el lunes.'}
    with pytest.raises(ValueError,match='confirmed agreement'):
        validate_items(json.dumps({'items':[item]}),rows,'es')
    item['category']='decision'
    assert validate_items(json.dumps({'items':[item]}),rows,'es')[0]['category']=='decision'



def test_invalid_amount_uses_source_only_after_retry_and_caches_safe_result(monkeypatch):
    sent=[]
    checkpoints={}

    def fake_chat(messages, *_args, **_kwargs):
        row=json.loads(messages[1]['content'])['source_rows'][0]
        sent.append(row['id'])
        return json.dumps({'items':[{
            'category':'decision','sources':[{'id':row['id'],'quote':row['text']}],
            'owner':None,'due':None,'text_es':'Fondo aprobado de 800 pesos.',
            'text_en':'A $800 fund was approved.',
        }]})

    monkeypatch.setattr(summarize,'ollama_chat',fake_chat)
    source='[00:00:30] Se aprobó un fondo de 800 pesos.'
    options=dict(read_block=checkpoints.get,write_block=checkpoints.__setitem__)
    report=summarize.summarize_local(source,'minutes','both',ollama.MODEL,**options)
    assert sent==[1,1] and report.count('800 pesos')>=2
    assert '$800' not in report and 'See the original wording' in report
    sent.clear()
    assert summarize.summarize_local(source,'minutes','both',ollama.MODEL,**options)==report
    assert sent==[]
