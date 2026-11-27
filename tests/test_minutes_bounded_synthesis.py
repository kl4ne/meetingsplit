import json
import pytest
from engine.minutes_bounded_synthesis import (atoms,anchor_audit,audit_themes,compose,
    windows,byte_size,MAX_BYTES,MAX_UNITS)

def ref(i,quote):
    return {'source_id':i,'timestamp':'00:00:01','quote':quote}
SOURCE='La información sobre accesibilidad debe estar disponible en el mostrador; la conversación distinguió la bienvenida del registro administrativo.'
OTHER='Se examinó el acceso desde la rampa hasta la entrada principal.'
def response(ids,summary=SOURCE):
    return json.dumps({'themes':[{'ids':ids,'title_es':'Información y orientación','summary_es':summary}]})

def test_cited_row_with_missing_clause_is_not_coverage():
    units,_=atoms([ref(2,SOURCE)])
    report=audit_themes(units,[{'sources':[ref(2,SOURCE)],
        'summary_es':'La conversación distinguió la bienvenida del registro administrativo en el mostrador.'}],'es')
    assert report[0]['status']=='anchor_gap'
    assert 'accesibilidad' in report[0]['missing']
    assert anchor_audit(SOURCE,SOURCE,'es')['status']=='literal_anchors_only'

def test_multi_sentence_partial_structured_quote_keeps_other_sentences():
    source=ref(1,SOURCE+' '+OTHER)
    units,account=atoms([source],[{'category':'notice','sources':[ref(1,SOURCE)]}])
    assert [u['source']['quote'] for u in units]==[OTHER]
    assert [a['status'] for a in account]==['structured','detail']

def test_single_retry_only_unresolved_units_and_preserve_exact_source():
    units,_=atoms([ref(1,SOURCE),ref(2,OTHER)])
    scopes=[]
    def request(messages,schema,**kw):
        scopes.append(kw['scope']['ids'])
        return response([1]) if len(scopes)==1 else '{"themes":[]}'
    out=compose(units,'es',request)
    assert scopes==[[1,2],[2]]
    assert [t['ids'] for t in out['themes']]==[[1]]
    assert out['source_only'][0]['unit']['source']['quote']==OTHER
    assert out['review_required']

def test_cross_language_fallback_no_extra_translation_calls():
    units,_=atoms([ref(1,'The group discussed access to the entrance ramp.')])
    def never(*a,**k):raise AssertionError('unexpected model request')
    out=compose(units,'es',never)
    assert out['source_only'][0]['reason']=='cross_language_or_uncertain'
    assert anchor_audit(units[0]['source']['quote'],SOURCE,'es')['status']=='cross_language_unverified'
    # BOTH remains explicitly unsupported rather than pretending a single
    # target-language result proves coverage of the second report.
    units,_=atoms([ref(2,SOURCE)])
    assert compose(units,'both',never)['source_only']

def test_unsupported_proposal_rejected_even_if_source_words_present():
    quote='Se habló de preparar ejemplos para la próxima capacitación.'
    units,_=atoms([ref(1,quote)])
    out=compose(units,'es',lambda *a,**k:response([1],quote+' Se propuso preparar ejemplos.'))
    assert not out['themes'] and len(out['calls'])==2
    assert out['source_only'][0]['unit']['source']['quote']==quote

def test_invalid_duplicate_ids_not_accepted():
    units,_=atoms([ref(1,SOURCE)])
    out=compose(units,'es',lambda *a,**k:response([1,1]))
    assert len(out['calls'])==2 and not out['themes'] and len(out['source_only'])==1

def test_bound_and_oversize_16k_simulated_words():
    text=' '.join(['material de consulta disponible para la orientación y el registro']*8)+'.'
    units,_=atoms([ref(i,text) for i in range(270)]+[ref(271,'La '+('información '*600)+'.')])
    assert sum(len(u['source']['quote'].split()) for u in units)>16000
    w=list(windows(units))
    assert sum(len(b) for b,_ in w)==len(units)
    assert all(len(b)<=MAX_UNITS and byte_size(b)<=MAX_BYTES for b,large in w if not large)
    assert sum(large for _,large in w)==1
    out=compose(units,'es',lambda *a,**k:'{"themes":[]}')
    assert len(out['calls'])<=2*sum(not large for _,large in w)
    assert len(out['source_only'])==len(units)

def test_no_silent_removal_of_asides_or_repetitions():
    units,account=atoms([ref(1,SOURCE),ref(2,SOURCE),ref(3,'Yo quizá podría revisar el archivo.')])
    assert len(units)==len(account)==3

def test_transport_failure_bounded_and_literal_fallback():
    units,_=atoms([ref(1,SOURCE)])
    def fail(*a,**k):raise RuntimeError('timeout')
    out=compose(units,'es',fail)
    assert len(out['calls'])==len(out['errors'])==2 and out['source_only'][0]['unit']==units[0]
