import json
import pytest
from engine.minutes_context_claims import claim_request,validate_claims,operational_reason,recovery_targets
from engine.minutes_context_windows import plan_context
from engine.minutes_evidence import changes_operational_meaning

def row(i,t,text):
    return {'id':i,'timestamp':f'00:00:{t:02d}','text':text}

ROWS=[row(1,0,'La conservadora explicó que el fabricante reparó la caja.'),
      row(2,4,'El guía leyó una instrucción antigua:'),
      row(3,8,'«Trasladen el catálogo».'),
      row(4,12,'La instrucción era un ejemplo, no una orden de hoy.'),
      row(5,16,'Se habló de revisar las etiquetas.'),
      row(6,20,'Alguien mencionó un número y la lectura se cortó a mitad de'),
      row(7,40,'Se explicó cómo proteger los materiales.')]
BLOCKS=[ROWS];UNITS=plan_context(BLOCKS)['windows'][0]

def claim(ids,text,quotes=None):
    return {'sources':[{'id':i,'quote':ROWS[i-1]['text'] if quotes is None else quotes[n]}
                        for n,i in enumerate(ids)],'text_es':text}
def response(claims,review=(),title='Explicación'):
    return json.dumps({'themes':[{'title_es':title,'claims':claims}],'review_ids':list(review)})
def validate(claims,**kw):
    return validate_claims(response(claims),UNITS,'es',blocks=BLOCKS,**kw)

@pytest.mark.parametrize('value,source,expected',[
    ('Se habló antes de revisar.','Se habló de revisar.','unsupported_before'),
    ('Se habló después de revisar.','Se habló de revisar.','unsupported_after'),
    ('A más tardar el lunes.','El lunes.','unsupported_latest'),
    ('Se implementará el plan.','Se discutió el plan.','unsupported_implementation'),
    ('Se habló después de revisar.','They spoke after reviewing.',None),
    ('Se habló de revisar.','Se habló de revisar.',None),
])
def test_specific_reason_preserves_existing_guard(value,source,expected):
    assert operational_reason(value,source)==expected
    assert changes_operational_meaning(value,source)==bool(expected)

def test_schema_uses_claim_specific_quotes_and_original_context():
    m,s=claim_request(UNITS,'es')
    assert len(json.loads(m[1]['content'])['context_units'])==2
    fields=s['properties']['themes']['items']['properties']['claims']['items']['properties']
    assert fields['sources']['items']['properties']['id']['enum']==list(range(1,8))

def test_good_claim_retains_own_refs_not_neighboring_actor():
    a=claim([1],'La conservadora explicó que el fabricante reparó la caja.')
    b=claim([2,3,4],'El guía leyó una instrucción antigua de traslado como ejemplo, no como orden actual.')
    r=validate([a,b])
    assert len(r['themes'])==1 and len(r['themes'][0]['claims'])==2
    assert [x['source_id'] for x in r['themes'][0]['claims'][0]['sources']]==[1]
    assert [x['source_id'] for x in r['themes'][0]['claims'][1]['sources']]==[2,3,4]
    assert r['review_required']

def test_bad_claim_does_not_remove_good_claim_and_no_raw_draft_default():
    a=claim([1],'La conservadora explicó que el fabricante reparó la caja.')
    b=claim([5],'Se habló después de revisar las etiquetas.')
    r=validate([a,b])
    assert len(r['themes'][0]['claims'])==1
    assert r['rejections']==[{'code':'unsupported_after','source_ids':[5],'theme_index':0,'claim_index':1}]
    assert 5 in [x['source_id'] for x in r['gaps']]
    assert recovery_targets(UNITS,r)==[5]
    withdraft=validate([a,b],retain_rejected_drafts=True)
    assert withdraft['rejections'][0]['local_rejected_draft']==b

def test_cannot_borrow_another_claims_quantity():
    a=claim([1],'La conservadora explicó la reparación.')
    b=claim([5],'Se habló de revisar 3 etiquetas.')
    r=validate([a,b])
    assert r['rejections'][0]['code']=='unsupported_quantity'
    assert recovery_targets(UNITS,r)==[]

def test_nonliteral_and_unknown_ids_fail_closed():
    a=claim([1],'La conservadora explicó la reparación.',quotes=['El guía reparó la caja.'])
    r=validate([a]);assert r['rejections'][0]['code']=='nonliteral_quote'
    b={'sources':[{'id':99,'quote':'x'}],'text_es':'Se habló de una caja.'}
    r=validate([b]);assert r['rejections'][0]['code']=='invalid_source_id'
    assert len(r['gaps'])==7

def test_partial_quote_preserves_whole_source_for_review():
    r=validate([claim([1],'El fabricante reparó la caja.',quotes=['el fabricante reparó la caja.'])])
    assert r['themes'] and 1 in [x['source_id'] for x in r['gaps']]

def test_interruption_review_overrides_model_claim():
    r=validate([claim([6],'La lectura del catálogo se interrumpió.')])
    assert r['rejections'][0]['code']=='possible_interrupted_clause'
    assert 6 in r['review_ids'] and 6 in [x['source_id'] for x in r['gaps']]
    assert recovery_targets(UNITS,r)==[]

def test_review_and_rejected_overlap_not_cleared_by_accepted_claim():
    a=claim([5],'Se habló de revisar las etiquetas.')
    b=claim([5],'Se habló antes de revisar las etiquetas.')
    r=validate_claims(response([a,b],[5]),UNITS,'es',blocks=BLOCKS)
    assert r['themes'] and 5 in [x['source_id'] for x in r['gaps']]
    assert recovery_targets(UNITS,r)==[]

def test_literal_citations_are_not_semantic_certificate():
    # An actor inversion can still pass lexical checks. Keep this limitation
    # visible rather than pretending exact citations prove the model's claim.
    r=validate([claim([1],'El fabricante explicó que la conservadora reparó la caja.')])
    assert r['themes'] and r['review_required']
    assert r['verification']=='claim_local_literal_citations_not_semantic'

def test_bilingual_claim_schema_and_shared_evidence():
    t={'title_es':'Reparación','title_en':'Repair','claims':[{
        **claim([1],'La conservadora explicó que el fabricante reparó la caja.'),
        'text_en':'The conservator explained that the manufacturer repaired the box.'}]}
    r=validate_claims(json.dumps({'themes':[t],'review_ids':[]}),UNITS,'both',blocks=BLOCKS)
    assert r['themes'][0]['summary_en'].startswith('The conservator')


@pytest.mark.parametrize('proposed,source,expected',[
    ('"Trasladen el catálogo".','«Trasladen el catálogo».','«Trasladen el catálogo».'),
    ('"Trasladen el catálogo".','“Trasladen el catálogo”.','“Trasladen el catálogo”.'),
    ('«Trasladen el catálogo».','«Trasladen el catálogo».','«Trasladen el catálogo».'),
    ('"Trasladen el catalogo".','«Trasladen el catálogo».',None),
    ('"Trasladen el catálogo"!','«Trasladen el catálogo».',None),
    ('"Trasladen el catálogo".','«Trasladen el catálogo». Ahora.',None),
    ('"Trasladen el catálogo".','«Trasladen el catálogo".',None),
    ('"Trasladen 2 catálogos".','«Trasladen 3 catálogos».',None),
    ('"Trasladen el catálogo".','«Trasladen  el catálogo».',None),
    ('"A" y «B».','«A» y «B».',None),
    ("'Trasladen el catálogo'.",'«Trasladen el catálogo».',None),
    ('" ".','« ».',None),
])
def test_exact_original_quote_pair_only(proposed,source,expected):
    from engine.minutes_context_claims import restore_full_row_quote_pair
    assert restore_full_row_quote_pair(proposed,source)==expected

def test_repair_explicitly_enabled_and_retains_original():
    c=claim([2,3,4],'El guía leyó una instrucción antigua de traslado como ejemplo, no como orden actual.',
            quotes=[ROWS[1]['text'],'"Trasladen el catálogo".',ROWS[3]['text']])
    old=validate([c]);assert old['rejections'][0]['code']=='nonliteral_quote'
    new=validate([c],repair_quote_pairs=True)
    assert len(new['themes'])==1 and not new['rejections']
    assert new['themes'][0]['sources'][1]['quote']==ROWS[2]['text']
    assert new['quote_repairs']==[{'code':'restored_original_double_quote_pair','source_id':3,
                                   'theme_index':0,'claim_index':0,'ref_index':1}]
    assert 3 not in [x['source_id'] for x in new['gaps']]
    assert new['review_required']

def test_quote_pair_does_not_bypass_operational_guard():
    c=claim([3],'Se implementará el traslado.',quotes=['"Trasladen el catálogo".'])
    new=validate([c],repair_quote_pairs=True)
    assert not new['themes'] and new['rejections']
    assert new['quote_repairs']==[]
    assert 3 in [x['source_id'] for x in new['gaps']]

def test_quote_pair_does_not_remove_explicit_review():
    c=claim([2,3,4],'El guía leyó una instrucción antigua de traslado como ejemplo, no como orden actual.',
            quotes=[ROWS[1]['text'],'"Trasladen el catálogo".',ROWS[3]['text']])
    new=validate_claims(response([c],[3]),UNITS,'es',blocks=BLOCKS,repair_quote_pairs=True)
    assert 3 in new['review_ids'] and 3 in [x['source_id'] for x in new['gaps']]
