"""Synthetic regressions; no local model, recording, or external API needed."""
import json
import pytest
from engine import summarize
from engine.minutes_brief import validate_editorial

TRANSCRIPT = '\n'.join([
    '[00:00:01] Se habló de la preparación del equipo.',
    '[00:01:01] Se revisó la orientación de los voluntarios.',
    '[00:02:01] Se explicó el registro de visitantes.',
    '[00:03:01] Se revisó el material de apoyo.',
])
DRAFT = 'La sesión abordó la preparación del equipo. [E1]\n\nSe trató la orientación de los voluntarios. [E2]'

@pytest.mark.parametrize('review_failure', ['bad_citation','timeout'])
def test_failed_review_retains_validated_draft_and_warning(monkeypatch, review_failure):
    def reply(messages, *args, json_output, **kwargs):
        if json_output:
            if 'items' in json_output['properties']:
                return '{"items":[]}'
            return json.dumps({'themes':[
                {'source_ids':[1], 'title_es':'Preparación', 'summary_es':'Se habló de la preparación del equipo.'},
                {'source_ids':[2], 'title_es':'Orientación', 'summary_es':'Se revisó la orientación de los voluntarios.'},
            ]})
        if len(messages)==2:
            return DRAFT
        if review_failure=='timeout':
            raise TimeoutError('Synthetic review timeout')
        return 'La sesión abordó la preparación. [E999]'
    monkeypatch.setattr(summarize,'ollama_chat',reply)
    evidence={};events=[]
    report=summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',
                                      evidence_sink=evidence.update,qa_trace=events.append)
    assert 'La sesión abordó la preparación del equipo.' in report
    assert 'Se trató la orientación de los voluntarios.' in report
    assert '[E999]' not in report
    assert evidence['narrative_fallbacks']==[{'language':'es','theme_ids':[1,2]}]
    fallback=next(event for event in events if event['event']=='fallback')
    assert fallback['retained']=='validated_draft'
    assert fallback['reason']
    assert fallback['stage']==('review' if review_failure=='timeout' else 'review_validation')
    assert any(e['stage']=='draft' and e['event']=='response' and e['raw']==DRAFT for e in events)
    assert any(e['stage']=='draft' and e['event']=='accepted' for e in events)

def test_editorial_rejection_reports_exact_reason_without_discarding_valid_theme():
    rows=[{'source_id':1,'timestamp':'00:00:01','quote':'Se habló de orientación.'},
          {'source_id':2,'timestamp':'00:00:02','quote':'Se revisó el registro.'}]
    bad={'source_ids':[2],'title_es':'Registro','summary_es':'Se revisó un gasto de USD 500.'}
    good={'source_ids':[1],'title_es':'Orientación','summary_es':'Se habló de orientación.'}
    gaps=[];failures=[]
    result=validate_editorial(json.dumps({'themes':[good,bad]}),rows,'es',rejected=gaps,
                              on_rejection=lambda theme,exc:failures.append((theme,str(exc))))
    assert len(result)==1 and result[0]['sources']==rows[:1]
    assert gaps==rows[1:]
    assert failures==[(bad,'Unsupported number in editorial theme')]
