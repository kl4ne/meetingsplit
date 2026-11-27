import json
from engine.minutes_source_accounting import audit_source_passages
from engine.minutes_evidence import source_blocks,render_minutes
from engine import summarize

def blocks(*rows):
    return list(source_blocks('\n'.join(f'[00:00:{i:02d}] {s}' for i,s in enumerate(rows,1))))
def ref(i,q):
    return {'source_id':i,'timestamp':f'00:00:{i:02d}','quote':q}
def item(i,q,category='decision'):
    return {'category':category,'sources':[ref(i,q)],'owner':None,'due':None,
            'text_es':q,'text_en':q}
def theme(i,q):
    return {'sources':[ref(i,q)],'title_es':'Orientación','summary_es':q}

def test_partial_structured_citation_keeps_uncited_sentence():
    a='Se aprobó conservar el horario.'
    b='Se explicó dónde están los baños accesibles.'
    audit=audit_source_passages(blocks(a+' '+b),[item(1,a)],[])
    assert [e['status'] for e in audit['entries']]==['structured_or_review','uncited_passage']
    assert audit['uncited_passages']==[ref(1,b)]

def test_existing_gap_not_counted_twice_and_partial_quote_not_full():
    a='El equipo explicó el acceso desde la rampa.'
    b='Se examinó el registro de visitantes.'
    audit=audit_source_passages(blocks(a,b),[],[theme(1,'el acceso desde la rampa.')],[ref(2,b)])
    assert [e['status'] for e in audit['entries']]==['uncited_passage','existing_gap']

def test_exact_repetition_only_from_accounted_source():
    a='Se explicó la orientación de las familias.'
    b='Se explicó la orientación de los visitantes.'
    c='Quizá se podría cambiar el horario.'
    audit=audit_source_passages(blocks(a,a,b,c,c),[],[theme(1,a),theme(4,c)])
    assert [e['status'] for e in audit['entries']]==['editorial_citation','exact_repeat','uncited_passage','editorial_citation','uncited_passage']

def test_ordinary_topic_not_assumed_visible_and_review_source_accounted():
    a='Se explicó dónde se ubica la biblioteca.'
    b='Quizá se cambie el horario.'
    audit=audit_source_passages(blocks(a,b),[item(1,a,'topic'),item(2,b,'review')],[])
    assert [e['status'] for e in audit['entries']]==['uncited_passage','structured_or_review']

def test_original_quote_visible_all_modes_without_timecodes():
    q='The entrance ramp is next to the reception desk.'
    for mode in ('summary','minutes','both'):
        result=render_minutes([],mode,'both',show_timestamps=False,respect_mode=True,uncited_passages=[ref(1,q)])
        es,en=result.split('\n\n---\n\n')
        assert q in es and q in en and 'Pasajes sin cita' in es and 'Passages not cited' in en
        assert '[00:00:' not in result

def test_integrated_pipeline_retains_unique_filtered_aside_no_new_calls(monkeypatch):
    transcript='[00:00:01] Se aprobó conservar el horario.\n[00:00:02] Quizá yo podría revisar el archivo.'
    calls=[];evidence={}
    def reply(*a,**kw):
        calls.append(1)
        return json.dumps({'items':[{'category':'decision','sources':[{'id':1,'quote':'Se aprobó conservar el horario.'}],
                'owner':None,'due':None,'text_es':'Se aprobó conservar el horario.'}]})
    monkeypatch.setattr(summarize,'ollama_chat',reply)
    report=summarize.summarize_local(transcript,'both','es','qwen3.5:9b',
                narrative_strategy='localized_editorial',evidence_sink=evidence.update)
    assert len(calls)==1
    assert 'Quizá yo podría revisar el archivo.' in report
    assert evidence['source_accounting']['uncited_passages']==[{'source_id':2,'timestamp':'00:00:02','quote':'Quizá yo podría revisar el archivo.'}]
