import json
import pytest
from engine.minutes_evidence import source_blocks, validate_items, render_minutes
from engine import summarize
from engine.control import Cancellation, JobCancelled

SOURCE='[00:00:01] Ana will send the draft on Friday.\n[00:00:06] Luis agreed to review it on Monday.'

def record(**changes):
    item={'category':'action','sources':[{'id':1,'quote':'Ana will send the draft on Friday.'}],
          'owner':'Ana','due':'Friday','text_en':'Send the draft','text_es':'Enviar el borrador'}
    item.update(changes)
    return item

def payload(*items):
    return json.dumps({'items':list(items)})

@pytest.mark.parametrize('change',[
    {'owner':'Maria'}, {'due':'Tuesday'}, {'owner':'An'},
    {'sources':[{'id':2,'quote':'Ana will send the draft on Friday.'}]},
    {'sources':[{'id':1,'quote':'Ana will send the draft on Monday.'}]},
    {'sources':[{'id':True,'quote':'Ana will send the draft on Friday.'}]},
    {'category':'invented'}, {'extra':'unexpected'},
])
def test_reject_unsupported_evidence(change):
    with pytest.raises(ValueError):
        validate_items(payload(record(**change)),list(source_blocks(SOURCE))[0],'both')

def test_bilingual_report_preserves_literal_evidence_and_review_warning():
    items=validate_items(payload(record()),list(source_blocks(SOURCE))[0],'both')
    report=render_minutes(items,'both','both')
    assert '# Minuta de reunión' in report and '# Meeting minutes' in report
    assert 'Ana' in report and 'Friday' in report and '[00:00:01]' in report
    assert 'review required' in report and 'revisión' in report
    assert items[0]['sources'][0]['quote']=='Ana will send the draft on Friday.'

def test_retry_then_emit_verified_sidecar(monkeypatch):
    calls=[]; sidecar={}
    def fake(*args,**kwargs):
        calls.append(kwargs)
        return payload(record(owner='Invented')) if len(calls)==1 else payload(record())
    monkeypatch.setattr(summarize,'ollama_chat',fake)
    result=summarize.summarize_local(SOURCE,'minutes','both','qwen3:4b',evidence_sink=sidecar.update)
    assert len(calls)==2 and all(c['json_output'] for c in calls)
    assert sidecar['review_required'] is True
    assert sidecar['verification']=='literal_source_match_only'
    assert {item['owner'] for item in sidecar['items']}=={'Ana','Luis'} and 'Invented' not in result

def test_invalid_record_preserves_minutes_and_places_original_passage_under_review(monkeypatch):
    valid=record(owner='Luis',due='Monday',sources=[{'id':2,'quote':'Luis agreed to review it on Monday.'}])
    tentative='They talked about training.'
    invalid=record(owner=None,due='Wednesday',sources=[{'id':3,'quote':tentative}])
    monkeypatch.setattr(summarize,'ollama_chat',lambda *a,**k:payload(invalid,valid))
    sidecar={}
    report=summarize.summarize_local(SOURCE+'\n[00:00:09] '+tentative,'minutes','both','qwen3.8:27b',
                                     evidence_sink=sidecar.update)
    assert 'Wednesday' not in report
    assert 'Luis' in report and 'Monday' in report
    reviews=[item for item in sidecar['items'] if item['category']=='review']
    assert any(item['sources'][0]['quote']==tentative for item in reviews)
    assert '## Classification pending review' in report


def test_malformed_evidence_twice_still_does_not_emit_report(monkeypatch):
    monkeypatch.setattr(summarize,'ollama_chat',lambda *a,**k:'not JSON')
    sidecar={}
    with pytest.raises(RuntimeError,match='Invalid source evidence'):
        summarize.summarize_local(SOURCE,'minutes','both','qwen3.8:27b',evidence_sink=sidecar.update)
    assert sidecar=={}


def test_chunking_preserves_source_ids_and_timestamps():
    text='[00:00:01] '+'x'*9000+'\n[00:00:02] next'
    blocks=list(source_blocks(text))
    rows=[r for b in blocks for r in b]
    assert [r['id'] for r in rows]==list(range(1,len(rows)+1))
    assert ''.join(r['text'] for r in rows if r['timestamp']=='00:00:01')=='x'*9000
    assert rows[-1]['timestamp']=='00:00:02'

def test_cancel_before_call(monkeypatch):
    task=Cancellation()
    task.cancel()
    monkeypatch.setattr(summarize,'ollama_chat',lambda *a,**k:pytest.fail('Unexpected inference'))
    with pytest.raises(JobCancelled):
        summarize.summarize_local(SOURCE,'minutes','both','qwen3:4b',cancel=task)

def test_empty_extraction_warns_not_proof_of_no_discussion(monkeypatch):
    monkeypatch.setattr(summarize,'ollama_chat',lambda *a,**k:payload())
    report=summarize.summarize_local('[00:00:01] The discussion continued.','minutes','en','qwen3:4b')
    assert 'does not establish' in report


def test_two_distinct_tasks_using_same_quote_are_not_dropped(monkeypatch):
    source='[00:00:01] Ana will send the draft and the invoice on Friday.'
    quote='Ana will send the draft and the invoice on Friday.'
    first=record(sources=[{'id':1,'quote':quote}])
    second=record(sources=[{'id':1,'quote':quote}],text_en='Send the invoice',text_es='Enviar la factura')
    monkeypatch.setattr(summarize,'ollama_chat',lambda *a,**k:payload(first,second))
    sidecar={}
    report=summarize.summarize_local(source,'both','both','qwen3:4b',evidence_sink=sidecar.update)
    assert len(sidecar['items'])==2
    assert 'Send the draft' in report and 'Send the invoice' in report

def test_duplicate_json_keys_are_rejected():
    with pytest.raises(ValueError):
        validate_items('{"items":[],"items":[]}',list(source_blocks(SOURCE))[0],'both')

def test_empty_blocks_reported_in_sidecar_and_markdown(monkeypatch):
    monkeypatch.setattr(summarize,'ollama_chat',lambda *a,**k:payload())
    sidecar={}
    report=summarize.summarize_local(SOURCE,'minutes','en','qwen3:4b',evidence_sink=sidecar.update)
    assert sidecar['empty_block_ids']==[1]
    assert 'Sections with no extracted items' in report
