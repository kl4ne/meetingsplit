import json
import pytest
from engine.minutes_context_windows import plan_context
from engine.minutes_context_row_citations import row_request,validate_rows

def windows():
    rows=[{'id':i+1,'timestamp':f'00:00:{i*4:02d}','text':s}
          for i,s in enumerate(['Se explicó el uso de las muestras','en el laboratorio.',
           'La grabación se cortó a mitad de','En un caso ficticio alguien dijo:',
           '«Aprobamos comprar diez vitrinas».','Era un ejercicio, no una decisión real.'])]
    return plan_context([rows])['windows'][0]

def theme(ids,text,title='Muestras'):
    return {'source_ids':ids,'title_es':title,'summary_es':text}

def result(themes,review=()):
    return validate_rows(json.dumps({'themes':themes,'review_ids':list(review)}),windows(),'es')

def test_transport_keeps_context_but_schema_cites_original_rows():
    w=windows();m,s=row_request(w,'es')
    assert len(w)==1
    assert len(json.loads(m[1]['content'])['context_units'][0]['fragments'])==6
    ids=s['properties']['themes']['items']['properties']['source_ids']['items']['enum']
    assert ids==list(range(1,7))
    assert 'unit_ids' not in s['properties']['themes']['items']['properties']
    assert 'review_ids' in s['required']

def test_no_implicit_coverage_of_neighboring_fragment():
    r=result([theme([1,2],'Se explicó el uso de las muestras en el laboratorio.')])
    assert [x['source_id'] for x in r['themes'][0]['sources']]==[1,2]
    assert [x['source_id'] for x in r['gaps']]==[3,4,5,6]
    assert r['review_required']

def test_review_ids_survive_even_if_also_cited():
    r=result([theme([1,2,3],'Se explicó el uso de las muestras en el laboratorio.')],[3])
    assert r['review_ids']==[3] and 3 in [x['source_id'] for x in r['gaps']]

def test_fiction_indirect_speech_without_relaxing_approval_guard():
    good=theme([4,5,6],'Se presentó un ejemplo ficticio sobre la compra de diez vitrinas, que no constituyó una decisión real.','Ejercicio')
    r=result([good])
    assert len(r['themes'])==1 and not r['rejections']
    bad=theme([4,5,6],'Se aprobó comprar diez vitrinas.','Compra')
    r=result([bad])
    assert not r['themes'] and r['rejections']

@pytest.mark.parametrize('bad',[[99],[True],[1,1],[]])
def test_invalid_citations_never_certify_rows(bad):
    r=result([theme(bad,'Se explicó el uso de las muestras.')])
    assert not r['themes'] and len(r['gaps'])==6

@pytest.mark.parametrize('bad',[[99],[True],[1,1],None])
def test_invalid_review_ids_fail_closed(bad):
    with pytest.raises(ValueError):
        validate_rows(json.dumps({'themes':[],'review_ids':bad}),windows(),'es')

def test_rejected_overlapping_theme_retains_gap():
    good=theme([1,2],'Se explicó el uso de las muestras en el laboratorio.')
    bad=theme([2],'Se aprobó la compra.','Compra')
    r=result([good,bad])
    assert len(r['themes'])==1 and 2 in [x['source_id'] for x in r['gaps']]

def test_empty_result_keeps_all_sources():
    assert len(result([])['gaps'])==6
