from engine.minutes_evidence import source_blocks,render_minutes
from engine.minutes_context_gap_presentation import compact_context_gaps

def setup(a='La etiqueta identifica la planta.',b=None,*,delta=4):
    b=a if b is None else b
    blocks=list(source_blocks(f'[00:00:01] {a}\n[00:00:{1+delta:02d}] {b}'))
    rows=[r for block in blocks for r in block]
    refs=[{'source_id':r['id'],'timestamp':r['timestamp'],'quote':r['text']} for r in rows]
    themes=[{'sources':[refs[0]],'title_es':'Etiqueta','summary_es':a}]
    diag={'overbudget_source_ids':[],'windows':[{'source_ids':[1,2],
        'review_ids':[],'interruption_review_ids':[],'rejections':[],'quarantined_themes':[]}]}
    return blocks,refs,themes,diag

def test_adjacent_identical_cited_sentence_is_presentation_only():
    blocks,refs,themes,diag=setup()
    gaps=[refs[1]]
    visible,compacted=compact_context_gaps(blocks,[],themes,gaps,diag)
    assert visible==[] and gaps==[refs[1]]
    assert compacted==[{'source':refs[1],'reason':'adjacent_exact_repeat_of_cited_row','earlier_source_id':1}]

def test_unique_or_distant_source_remains_visible():
    for args,kwargs in [(('La etiqueta identifica la planta.','La etiqueta identifica la parcela.'),{}),((),{'delta':20})]:
        blocks,refs,themes,diag=setup(*args,**kwargs)
        assert compact_context_gaps(blocks,[],themes,[refs[1]],diag)==([refs[1]],[])

def test_operational_or_uncertain_repeated_source_remains_visible():
    for q in ('Se aprobó conservar el horario.','Quizá cambie el horario.','El presupuesto es de $25.'):
        blocks,refs,themes,diag=setup(q)
        assert compact_context_gaps(blocks,[],themes,[refs[1]],diag)==([refs[1]],[])

def test_explicit_review_interruption_and_rejection_not_cleared_by_repeat():
    for key,value in [('review_ids',[2]),('interruption_review_ids',[2]),
        ('rejections',[{'source_ids':[2],'reason':'invalid'}]),
        ('rejections',[{'reason':'timeout'}]),
        ('quarantined_themes',[{'theme':{'sources':[{'source_id':2}]}}])]:
        blocks,refs,themes,diag=setup()
        diag['windows'][0][key]=value
        assert compact_context_gaps(blocks,[],themes,[refs[1]],diag)==([refs[1]],[])

def test_already_visible_review_is_not_printed_twice_but_original_gap_remains():
    blocks,refs,themes,diag=setup(b='Someone mentioned an unclear measurement')
    item={'category':'review','sources':[refs[1]],'owner':None,'due':None,
          'text_es':'Consulta las palabras originales en la cita.'}
    gaps=[refs[1]]
    visible,compacted=compact_context_gaps(blocks,[item],themes,gaps,diag)
    assert not visible and gaps==[refs[1]]
    assert compacted[0]['reason']=='already_displayed_in_review'
    result=render_minutes([item],'both','es',editorial=themes,editorial_gaps=visible,
        respect_mode=True,show_timestamps=False,compacted_review_count=len(compacted))
    assert result.count(refs[1]['quote'])==1 and 'JSON de evidencias' in result
    visible,compacted=compact_context_gaps(blocks,[item],themes,gaps,diag,
        {'repeated_review_items':[{'item_index':0}]})
    assert visible==gaps and not compacted

def test_prior_gap_never_certifies_repeat():
    blocks,refs,themes,diag=setup()
    assert compact_context_gaps(blocks,[],themes,refs,diag)==(refs,[])
