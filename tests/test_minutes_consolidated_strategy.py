"""The experimental strategy avoids rewrite calls but keeps evidence and warnings."""
import json
import pytest
from engine import summarize
from engine.minutes_overview import build_overview
from engine.minutes_evidence import render_minutes

TRANSCRIPT='\n'.join([
    '[00:00:01] Se habló de la preparación del equipo.',
    '[00:00:02] Se revisó la guía de orientación.',
    '[00:00:03] Se aprobó mantener el horario actual.',
    '[00:00:04] Ana Ruiz se comprometió a enviar el inventario el viernes.',
])

def test_consolidation_reuses_editorial_themes_without_rewriting(monkeypatch):
    calls=[]; evidence={}
    def reply(messages,*args,json_output,**kwargs):
        calls.append(json_output)
        assert json_output
        if 'items' in json_output['properties']:
            return '{"items":[]}'
        return json.dumps({'themes':[
            {'source_ids':[1],'title_es':'Preparación','summary_es':'Se habló de la preparación del equipo.'},
            {'source_ids':[2],'title_es':'Orientación','summary_es':'Se revisó la guía de orientación.'},
        ]})
    monkeypatch.setattr(summarize,'ollama_chat',reply)
    report=summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',evidence_sink=evidence.update,
                                      narrative_strategy='validated_editorial')
    assert len(calls)==2
    assert evidence['narrative_strategy']=='validated_editorial'
    assert evidence['review_required'] is True
    assert evidence['empty_block_ids']==[1]
    brief,detail=report.split('## Temas tratados',1)
    assert '## Resumen ejecutivo' in brief
    assert 'mantener el horario actual' in brief and 'Ana Ruiz' in brief
    assert 'Preparación' in detail and 'Orientación' in detail
    assert 'Secciones sin elementos extraídos' in report

def test_long_overview_samples_end_and_keeps_all_details():
    themes=[{'title_es':f'Tema {i}','summary_es':f'Contenido del tema {i}.',
             'sources':[{'source_id':i,'timestamp':'00:00:00','quote':f'Contenido del tema {i}.'}]}
            for i in range(1,21)]
    overview=build_overview([],themes,'es')
    assert 'Contenido del tema 1.' in overview[0] and 'Contenido del tema 20.' in overview[0]
    assert 'Los demás temas' in overview[0]
    report=render_minutes([],'both','es',editorial=themes,executive_overview={'es':overview},show_timestamps=False)
    assert all(f'Contenido del tema {i}.' in report for i in range(1,21))
    assert '## Temas tratados' in report

def test_unknown_strategy_rejected():
    with pytest.raises(ValueError,match='strategy'):
        summarize.summarize_local(TRANSCRIPT,'both','es','qwen3.5:9b',narrative_strategy='unknown')
