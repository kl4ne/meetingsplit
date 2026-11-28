"""Integration of experimental claims with existing minutes pipeline; mock only."""
import json
import pytest
from engine import summarize
from engine.control import JobCancelled
from engine.minutes_evidence import source_blocks

TEXT='\n'.join([
    '[00:00:01] El coordinador leyó un ejemplo:',
    '[00:00:05] «Protejan las muestras».',
    '[00:00:09] Se explicó cómo conservar las muestras.',
    '[00:00:13] Se habló de revisar las etiquetas.',
    '[00:00:40] Aviso: El material está disponible en recepción.'
])
ROWS=[r for b in source_blocks(TEXT) for r in b]
def stub(lang,behavior='ok'):
    calls=[]
    def answer(messages,*args,json_output,**kw):
        props=json_output['properties']
        if 'items' in props:
            calls.append('extraction');return '{"items":[]}'
        calls.append('claims')
        assert 'claims' in props['themes']['items']['properties']
        if behavior=='cancel':raise JobCancelled()
        if behavior=='timeout':raise RuntimeError('synthetic timeout')
        if behavior=='malformed':return '{invalid'
        langs=('es','en') if lang=='both' else (lang,)
        a={'sources':[{'id':1,'quote':ROWS[0]['text']},{'id':2,'quote':'"Protejan las muestras".'}]}
        b={'sources':[{'id':3,'quote':ROWS[2]['text']}]}
        c={'sources':[{'id':4,'quote':ROWS[3]['text']}]}
        for l in langs:
            a['text_'+l]='El coordinador leyó un ejemplo de protección de muestras.' if l=='es' else 'The coordinator read an example about protecting samples.'
            b['text_'+l]='Se explicó cómo conservar las muestras.' if l=='es' else 'The discussion explained how to preserve the samples.'
            c['text_'+l]='Se implementará la revisión de etiquetas.' if l=='es' else 'The label review will be implemented.'
        theme={'claims':[a,b,c],**{'title_'+l:'Implementación y conservación' if l=='es' else 'Implementation and preservation' for l in langs}}
        return json.dumps({'themes':[theme],'review_ids':[4]})
    return calls,answer

@pytest.mark.parametrize('mode',['summary','minutes','both'])
@pytest.mark.parametrize('lang',['es','en','both'])
def test_integrated_claims_preserve_sources(monkeypatch,mode,lang):
    calls,answer=stub(lang);e={};events=[]
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    report=summarize.summarize_local(TEXT,mode,lang,'qwen3.5:9b',narrative_strategy='contextual_claim_qa',
        evidence_sink=e.update,qa_trace=events.append)
    assert calls==['extraction','claims']
    assert e['narrative_strategy']=='contextual_claim_qa' and e['review_required']
    t=e['editorial_themes'][0]
    assert len(t['claims'])==2 and t['claims'][0]['sources'][1]['quote']==ROWS[1]['text']
    assert [r['source_id'] for r in t['claims'][1]['sources']]==[3]
    assert [r['source_id'] for r in e['editorial_gaps']]==[4]
    assert e['source_accounting']['uncited_passages']==[]
    w=e['context_diagnostics']['windows'][0]
    assert w['quote_repairs'][0]['source_id']==2 and w['neutralized_titles'][0]['theme_index']==0
    assert w['review_ids']==[4] and not w['recovery_target_ids']
    assert any(i['category']=='notice' for i in e['items'])
    assert ROWS[3]['text'] in report and ROWS[4]['text'] in report
    assert 'Implementación y conservación' not in report and 'Implementation and preservation' not in report
    assert [x['stage'] for x in events if x['event']=='request']==['extraction','contextual_claim_editorial']
    for l in ('es','en') if lang=='both' else (lang,):
        assert t['summary_'+l] in report
        if mode=='both':
            assert report.count(t['summary_'+l])==1
    assert not e['repeated_theme_presentation'] and not e['structured_theme_presentation']

@pytest.mark.parametrize('behavior',['timeout','malformed'])
def test_integrated_failure_preserves_original_rows(monkeypatch,behavior):
    calls,answer=stub('es',behavior);e={}
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    report=summarize.summarize_local(TEXT,'both','es','qwen3.5:9b',narrative_strategy='contextual_claim_qa',evidence_sink=e.update)
    assert calls==['extraction','claims'] and not e['editorial_themes']
    assert [r['source_id'] for r in e['editorial_gaps']]==[1,2,3,4]
    assert all(r['text'] in report for r in ROWS)

def test_integrated_cancel_propagates(monkeypatch):
    calls,answer=stub('es','cancel');e={}
    monkeypatch.setattr(summarize,'ollama_chat',answer)
    with pytest.raises(JobCancelled):
        summarize.summarize_local(TEXT,'both','es','qwen3.5:9b',narrative_strategy='contextual_claim_qa',evidence_sink=e.update)
    assert calls==['extraction','claims'] and not e
