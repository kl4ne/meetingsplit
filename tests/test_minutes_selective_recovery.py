"""Selective recovery is not relaxed full-section approval."""
import json
import pytest
from engine import summarize
from engine.minutes_narrative import narrative_sections, recover_narrative, validate_narrative

def make_section():
    texts=['Se habló de la preparación del equipo.',
           'Se revisó la orientación de los voluntarios.',
           'Se explicó el registro de visitantes.']
    titles=['Preparación','Orientación','Registro']
    themes=[{'title_es':titles[i-1], 'summary_es':text,
             'sources':[{'source_id':i,'timestamp':f'00:00:0{i}','quote':text}]}
            for i,text in enumerate(texts,1)]
    return next(narrative_sections(themes,'es'))

def test_partial_recovery_retains_good_paragraphs_and_only_missing_theme():
    section=make_section()
    draft='Se explicó la preparación del equipo. [E1]\n\nSe habló de la orientación de los voluntarios. [E2]'
    review='La sesión abordó la preparación del equipo. [E1]\n\nSe aprobó un gasto de USD 500. [E3]'
    with pytest.raises(ValueError):
        validate_narrative(review,section,'es')
    with pytest.raises(ValueError,match='omitted evidence'):
        validate_narrative(draft,section,'es')
    recovered,selection=recover_narrative(section,'es',draft=draft,revised=review)
    assert selection=={'review':[1],'draft':[2],'themes':[3]}
    assert [p['text'] for p in recovered]==[
        'La sesión abordó la preparación del equipo.',
        'Se habló de la orientación de los voluntarios.',
        'Se explicó el registro de visitantes.']
    assert all('500' not in p['text'] for p in recovered)

def test_invalid_clause_invalidates_entire_paragraph():
    section=make_section()
    raw='Se explicó la preparación del equipo. [E1] Se aprobó el registro de visitantes. [E3]'
    recovered,selection=recover_narrative(section,'es',revised=raw)
    assert selection=={'review':[],'draft':[],'themes':[1,2,3]}
    assert all(p.get('title') for p in recovered)

def test_overlap_cannot_duplicate_covered_themes():
    section=make_section()
    review='Se trató la preparación y orientación de los voluntarios. [E1] [E2]'
    draft='Se habló de la orientación y el registro de visitantes. [E2] [E3]'
    recovered,selection=recover_narrative(section,'es',revised=review,draft=draft)
    assert selection=={'review':[1,2],'draft':[],'themes':[3]}
    assert len(recovered)==2

def test_unknown_citations_and_oversized_output_do_not_enter_recovery():
    section=make_section()
    recovered,selection=recover_narrative(section,'es',revised='Se habló de preparación. [E999]',
                                          draft='Se habló de preparación. [E1]\n\n'+'a'*4001)
    assert selection=={'review':[],'draft':[],'themes':[1,2,3]}

def test_pipeline_partial_recovery_preserves_review_warning(monkeypatch):
    section=make_section()
    rows=[value[0] for value in section.values()]
    transcript='\n'.join(f"[00:00:0{i}] {theme['summary_es']}" for i,theme in enumerate(rows,1))
    transcript+='\n[00:00:04] Se revisó el material de apoyo.'
    def reply(messages,*args,json_output,**kwargs):
        if json_output:
            if 'items' in json_output['properties']:
                return '{"items":[]}'
            return json.dumps({'themes':[{'source_ids':[i],
                    'title_es':theme['title_es'],'summary_es':theme['summary_es']}
                    for i,theme in enumerate(rows,1)]})
        if len(messages)==2:
            return 'Se habló de la orientación de los voluntarios. [E2]'
        return 'La sesión abordó la preparación del equipo. [E1]\n\nSe aprobó un gasto de USD 500. [E3]'
    monkeypatch.setattr(summarize,'ollama_chat',reply)
    evidence={};events=[]
    report=summarize.summarize_local(transcript,'both','es','qwen3.5:9b',
                                      evidence_sink=evidence.update,qa_trace=events.append)
    assert 'La sesión abordó la preparación del equipo.' in report
    assert 'Se habló de la orientación de los voluntarios.' in report
    assert 'Se explicó el registro de visitantes.' in report
    assert '500' not in report
    assert evidence['narrative_fallbacks']==[{'language':'es','theme_ids':[1,2,3]}]
    assert next(e for e in events if e['event']=='fallback')['selection']=={
        'review':[1],'draft':[2],'themes':[3]}
