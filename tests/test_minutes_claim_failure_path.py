import copy,json
import pytest
from engine.minutes_evidence import explicit_source_items,source_blocks,render_minutes
from engine.minutes_claim_structured_refs import restore_structured_periods
from engine.minutes_context_adapter import contextual_editorial

TEXT='[00:00:01] Se aprobó conservar el orden actual del inventario.\n[00:00:20] Elena Ruiz will send the checklist by Thursday.'
BLOCKS=list(source_blocks(TEXT))
ROWS=[r for b in BLOCKS for r in b]
EXPLICIT=explicit_source_items(ROWS,'es')

def test_restore_only_original_terminal_period():
    items=copy.deepcopy(EXPLICIT)
    for i in items:i['sources'][0]['quote']=i['sources'][0]['quote'].rstrip('.')
    saved=copy.deepcopy(items)
    result,diag=restore_structured_periods(items,EXPLICIT,BLOCKS)
    assert items==saved
    assert result==EXPLICIT
    assert [d['source_id'] for d in diag]==[1,2]

@pytest.mark.parametrize('change',['words','owner','due','category','timestamp','multiple','duplicate'])
def test_no_restoration_when_independent_evidence_does_not_match(change):
    items=copy.deepcopy(EXPLICIT)
    item=items[1];item['sources'][0]['quote']=item['sources'][0]['quote'].rstrip('.')
    explicit=copy.deepcopy(EXPLICIT)
    if change=='words':item['sources'][0]['quote']=item['sources'][0]['quote'].replace('checklist','list')
    if change=='owner':item['owner']='Other Person'
    if change=='due':item['due']='Friday'
    if change=='category':item['category']='topic'
    if change=='timestamp':item['sources'][0]['timestamp']='00:00:21'
    if change=='multiple':item['sources'].append(copy.deepcopy(item['sources'][0]))
    if change=='duplicate':explicit.append(copy.deepcopy(explicit[1]))
    result,diag=restore_structured_periods(items,explicit,BLOCKS)
    assert result==items and not diag

def test_interruption_diagnostics_survive_timeout():
    blocks=list(source_blocks('[00:00:01] Someone mentioned an unclear measurement\n[00:00:05] and the recording stopped in the middle of\n[00:00:30] Se explicó el tema siguiente.'))
    def timeout(*a,**k):raise TimeoutError('synthetic limit')
    r=contextual_editorial(blocks,[],'es',timeout,claim_mode=True)
    assert [x['source_id'] for x in r['gaps']]==[1,2,3]
    assert r['diagnostics']['windows'][0]['interruption_review_ids']==[1,2]
    assert r['diagnostics']['windows'][0]['review_ids']==[1,2]
    assert not r['themes']

@pytest.mark.parametrize('lang',['es','en'])
def test_failed_combined_no_duplicate_outcome_summary(lang):
    items=copy.deepcopy(EXPLICIT)
    for i in items:i['text_en']='An existing outcome was recorded.'
    gaps=[{'source_id':3,'timestamp':'00:00:30','quote':'Un tema sin síntesis.'}]
    title='Resumen ejecutivo' if lang=='es' else 'Executive summary'
    report=render_minutes(items,'both',lang,editorial_gaps=gaps,executive_overview={lang:['Overview.']},
        respect_mode=True,show_timestamps=False,claim_qa=True)
    assert report.count('## '+title)==1
    assert 'Un tema sin síntesis.' in report
    assert ('No se completó la síntesis temática.' if lang=='es' else 'The thematic synthesis was not completed.') in report
