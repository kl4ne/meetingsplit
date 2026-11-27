import json
import pytest
from engine.minutes_bounded_synthesis import atoms
from engine.minutes_bounded_bilingual import compose_bilingual,render_candidate,bridge,bounded_windows,size,languages
ES='Se explicó el uso de etiquetas para distinguir los materiales prestados de los materiales disponibles.'
EN='The entrance instructions distinguish the ramp from the stairs and describe where the accessible restrooms are located.'
ES_EN='The use of labels to distinguish borrowed materials from available materials was explained.'
EN_ES='Las instrucciones de entrada distinguen la rampa de las escaleras y describen dónde están los baños accesibles.'
def ref(i,text):return {'source_id':i,'timestamp':'00:00:01','quote':text}
def units():return atoms([ref(1,ES),ref(2,EN)])[0]
def theme(lang,i,summary,translation=None):
    return {'language':lang,'ids':[i],'title':'Orientación' if lang=='es' else 'Orientation','summary':summary,
        'translations':[] if translation is None else [{'id':i,'text':translation}]}
def raw(*themes):return json.dumps({'themes':themes})
def test_both_one_request_all_pairs_originals_retained():
    out=compose_bilingual(units(),'both',lambda *a,**k:raw(theme('es',1,ES),theme('en',2,EN),
        theme('es',2,EN_ES,EN_ES),theme('en',1,ES_EN,ES_EN)))
    assert len(out['calls'])==1
    assert all(not r['source_only'] and len(r['themes'])==2 for r in out['reports'].values())
    assert out['review_required']
    for lang,r in out['reports'].items():
        assert any(t['verification']=='translation_candidate_semantic_review' for t in r['themes'])
    both=render_candidate(out,'both')
    assert EN in both['es'] and ES in both['en']
    assert '# Minuta de reunión' not in render_candidate(out,'summary')['es']
    assert '# Executive summary' not in render_candidate(out,'minutes')['en']
    assert '# Executive summary' in both['en'] and '# Meeting minutes' in both['en']

def test_bad_language_keeps_good_pairs_and_retries_only_remaining():
    scopes=[]
    def request(*a,**kw):
        scopes.append(kw['scope']['pairs'])
        if len(scopes)==1:
            return raw(theme('es',1,ES),theme('en',2,EN),theme('es',2,EN_ES),theme('en',1,ES_EN,ES_EN))
        return raw()
    out=compose_bilingual(units(),'both',request)
    assert scopes[1]==[[2,'es']]
    assert len(out['reports']['en']['themes'])==2
    assert out['reports']['es']['source_only'][0]['unit']['source']['quote']==EN

@pytest.mark.parametrize('source,target',[
    ('The guide explains the ramp; the accessible restroom is near the entrance.',
     'La guía explica la rampa.'),
    ('The guide does not disclose the private contact information.',
     'La guía divulga la información privada de contacto.'),
    ('The guide describes 3 exits in the building.',
     'La guía describe 2 salidas en el edificio.'),
    ('The form is available on Friday.',
     'El formulario está disponible a más tardar el viernes.'),
    ('The group discussed preparing examples for the next training.',
     'Se propuso preparar ejemplos para la próxima capacitación.'),
])
def test_translation_negative_guards(source,target):
    with pytest.raises(ValueError):bridge(ref(1,source),target,'es')

def test_summary_cannot_omit_clause_present_in_translation():
    u=atoms([ref(1,EN)])[0]
    out=compose_bilingual(u,'es',lambda *a,**k:raw(theme('es',1,
        'Las instrucciones de entrada distinguen la rampa de las escaleras.',EN_ES)))
    assert len(out['calls'])==2 and not out['reports']['es']['themes']
    assert out['reports']['es']['source_only'][0]['unit']==u[0]

def test_duplicate_pair_rejected_and_other_language_retained():
    out=compose_bilingual(units()[:1],'both',lambda *a,**k:raw(theme('es',1,ES),
        theme('es',1,ES),theme('en',1,ES_EN,ES_EN)))
    # Whole response can exceed cardinality; no invented acceptance.
    assert len(out['calls'])==2
    assert all(r['source_only'] for r in out['reports'].values())

def test_request_budget_includes_language_metadata():
    u=atoms([ref(i,ES) for i in range(270)]+[ref(271,'La '+('información '*600)+'.')])[0]
    w=list(bounded_windows(u,languages('both')))
    out=compose_bilingual(u,'both',lambda *a,**k:raw())
    assert len(out['calls'])==2*sum(not large for _,large in w)
    assert all(c['input_bytes']<=4500 for c in out['calls'])
    assert all(len(r['source_only'])==len(u) for r in out['reports'].values())
