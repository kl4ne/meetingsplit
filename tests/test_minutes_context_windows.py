import json
import pytest
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import (plan_context,request_spec,compose_context,
    validate_context,MAX_ROWS,MAX_UNIT_BYTES,MAX_WINDOW_BYTES,MAX_WINDOW_UNITS,_size)
from engine.control import JobCancelled

def row(i,t,quote):
    return {'id':i,'timestamp':f'00:{t//60:02d}:{t%60:02d}','text':quote}

def refs(plan):
    return [r for u in plan['units'] for r in u['sources']]+plan['structured_sources']+plan['overbudget_sources']

def test_fragments_cross_old_block_boundary_without_changes():
    rows=[row(1,0,'La muestra contiene'),row(2,5,'dos materiales distintos.'),row(3,10,'No se mezclan.')]
    plan=plan_context([rows[:1],rows[1:]])
    assert len(plan['units'])==1
    assert [r['quote'] for r in refs(plan)]==[r['text'] for r in rows]
    assert [r['source_id'] for r in refs(plan)]==[1,2,3]
    messages,_=request_spec(plan['windows'][0],'es')
    assert json.loads(messages[1]['content'])['context_units'][0]['fragments'][1]['text']==rows[1]['text']

def test_breaks_on_pause_backward_timestamp_and_separate_notice():
    rows=[row(1,0,'Primera idea'),row(2,5,'continúa.'),row(3,20,'Nueva explicación.'),
          row(4,25,'Aviso: La exposición comienza el lunes.'),row(5,26,'Otra idea.'),row(6,21,'Fragmento anterior.')]
    items=[{'category':'notice','sources':[{'source_id':4,'timestamp':rows[3]['timestamp'],'quote':rows[3]['text']}]}]
    p=plan_context([rows],items)
    assert [[r['source_id'] for r in u['sources']] for u in p['units']]==[[1,2],[3],[5],[6]]
    assert p['structured_sources'][0]['source_id']==4

def test_partial_quote_does_not_exclude_source():
    a=row(1,0,'Aviso: Se abre el lunes. La explicación continúa.')
    items=[{'category':'notice','sources':[{'source_id':1,'timestamp':a['timestamp'],'quote':'Aviso: Se abre el lunes.'}]}]
    p=plan_context([[a]],items)
    assert not p['structured_sources'] and refs(p)[0]['quote']==a['text']

def test_byte_and_row_limits_keep_every_source_once():
    rows=[row(i+1,i*4,'Texto de prueba '+('á漢字'*80)) for i in range(25)]
    rows.append(row(26,101,'漢'*1800))
    p=plan_context([rows])
    assert len(refs(p))==len(rows) and sorted(r['source_id'] for r in refs(p))==list(range(1,27))
    assert p['overbudget_sources'][0]['quote']==rows[-1]['text']
    assert all(len(u['sources'])<=MAX_ROWS and _size([u])<=MAX_UNIT_BYTES for u in p['units'])
    assert all(len(w)<=MAX_WINDOW_UNITS and _size(w)<=MAX_WINDOW_BYTES for w in p['windows'])

def test_duplicate_ids_rejected():
    with pytest.raises(ValueError):plan_context([[row(1,0,'uno'),row(1,2,'dos')]])

def small():
    return plan_context([[row(1,0,'Se explicó el uso de las muestras'),
                          row(2,4,'en el laboratorio.'),row(3,30,'Se habló de revisar las etiquetas.')]])

def theme(ids,text,title='Muestras'):
    return {'unit_ids':ids,'title_es':title,'summary_es':text}

def test_context_citations_expand_exact_original_rows():
    p=small();w=p['windows'][0]
    out=validate_context(json.dumps({'themes':[theme([1,2],'Se explicó el uso de las muestras en el laboratorio. Se habló de revisar las etiquetas.')]}),w,'es')
    assert not out['gaps'] and out['review_required']
    assert out['themes'][0]['sources']==refs(p)

def test_unrepresented_unit_and_empty_reply_stay_reviewable():
    p=small();w=p['windows'][0]
    out=validate_context(json.dumps({'themes':[theme([1],'Se explicó el uso de las muestras en el laboratorio.')]}),w,'es')
    assert [r['source_id'] for r in out['gaps']]==[3]
    assert validate_context('{"themes":[]}',w,'es')['gaps']==refs(p)

@pytest.mark.parametrize('bad',[
    theme([2],'Se propuso revisar las etiquetas.'),
    theme([2],'Se aprobó revisar las etiquetas.'),
    theme([2],'Se habló de revisar 25 etiquetas.'),
    theme([99],'Se habló de revisar las etiquetas.'),
    theme([True],'Se habló de revisar las etiquetas.'),
])
def test_rejected_units_preserve_sources(bad):
    p=small();w=p['windows'][0]
    out=validate_context(json.dumps({'themes':[theme([1],'Se explicó el uso de las muestras en el laboratorio.'),bad]}),w,'es')
    assert out['rejections'] and 3 in [r['source_id'] for r in out['gaps']]
    assert out['themes'][0]['sources']==w[0]['sources']

def test_rejected_claim_not_cleared_by_another_theme_on_same_unit():
    p=small();w=p['windows'][0]
    out=validate_context(json.dumps({'themes':[theme([1,2],'Se explicó el uso de las muestras y se habló de las etiquetas.'),theme([2],'Se propuso revisar las etiquetas.','Etiquetas')]}),w,'es')
    assert [r['source_id'] for r in out['gaps']]==[3]

def test_request_budget_transport_failure_no_retry():
    p=small();calls=[]
    def fail(*a):calls.append(1);raise RuntimeError('timeout')
    out=compose_context(p,'es',fail)
    assert out['requests']==len(calls)==len(p['windows'])
    assert out['gaps']==refs(p)
    def cancelled(*a):raise JobCancelled()
    with pytest.raises(JobCancelled):compose_context(p,'es',cancelled)
