import pytest
from engine.minutes_evidence import repeated_topic_coverage,render_minutes
from engine.minutes_overview import build_overview

TEXT='Se revisó la estructura del archivo y el glosario.'
def row(i,text=TEXT):
    return {'id':i,'timestamp':'00:00:00','text':text}
def ref(r):
    return {'source_id':r['id'],'timestamp':r['timestamp'],'quote':r['text']}
def record(r,category='review',owner=None,due=None):
    return {'category':category,'owner':owner,'due':due,'sources':[ref(r)],'text_es':r['text']}

def test_exact_earlier_descriptive_repetitions_are_accounted_without_deletion():
    a,b,c=row(1),row(2),row(3)
    items=[record(a,'topic'),record(c)]
    themes=[{'title_es':'Archivo','summary_es':TEXT,'sources':[ref(a)]}]
    result=repeated_topic_coverage([[a],[b],[c]],items,themes,[2])
    assert result['covered_empty_blocks']==[{'block':2,'matches':[{'source_id':2,'earlier_source_id':1}]}]
    assert result['unresolved_empty_block_ids']==[]
    assert result['repeated_review_items'][0]['item_index']==1
    assert result['unresolved_review_indices']==[]
    assert len(items)==2 and items[1]['category']=='review'
    report=render_minutes(items,'both','es',[],editorial=themes,repetition_coverage=result,show_timestamps=False)
    assert 'advertencias de extracción' in report

@pytest.mark.parametrize('text',[
    'El comité aprobó el presupuesto.',
    'El presupuesto es de USD 2,400.',
    'Se propuso extender el horario.',
    'Si se confirma el proyecto.',
    'Ana Ruiz se comprometió a enviar el inventario el viernes.',
    'Queda pendiente el inventario.',
    'Se revisó la estructura del archivo y el glosario nuevo.',
])
def test_new_or_operational_passage_still_needs_review(text):
    a,b=row(1,text),row(2,text)
    if text.endswith('nuevo.'):
        a=row(1)
    items=[record(a,'topic'),record(b)]
    result=repeated_topic_coverage([[a],[b]],items,[],[2])
    assert result['unresolved_empty_block_ids']==[2]
    assert result['unresolved_review_indices']==[1]

def test_later_reference_and_partial_citation_do_not_count():
    a,b=row(1),row(2)
    partial=record(a,'topic')
    partial['sources'][0]['quote']='Se revisó la estructura del archivo'
    result=repeated_topic_coverage([[a],[b]],[partial,record(b,'topic'),record(a)],[],[1])
    assert result['unresolved_empty_block_ids']==[1]
    assert result['unresolved_review_indices']==[2]

def test_task_overview_preserves_fields():
    task=record(row(1),'action','Ana Ruiz','el viernes')
    task['text_es']='Enviar el inventario.'
    report=' '.join(build_overview([task],[],'es'))
    assert 'Ana Ruiz' in report and 'el viernes' in report
