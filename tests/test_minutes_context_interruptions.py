import json
from engine.minutes_context_windows import plan_context
from engine.minutes_context_row_citations import validate_rows
from engine.minutes_context_interruptions import interrupted_tails,quarantine_interrupted

def row(i,t,s):
    return {'id':i,'timestamp':f'00:{t//60:02d}:{t%60:02d}','text':s}

def test_dangling_clause_after_complete_sentence_and_real_pause():
    blocks=[[row(1,0,'Se explicó el proceso.'),row(2,4,'Alguien mencionó un documento')],
        [row(3,8,'y se interrumpió la lectura de'),row(4,30,'Otro tema comenzó.')]]
    assert interrupted_tails(blocks)==[{'source_ids':[2,3],
        'reason':'possible_interrupted_clause_at_source_boundary'}]

def test_no_false_boundary_at_transport_or_extraction_split():
    rows=[row(i,i*2,'la explicación sigue') for i in range(1,8)]
    rows.extend([row(8,16,'se habló de'),row(9,18,'los materiales.')])
    assert len(plan_context([rows])['units'])==2
    assert interrupted_tails([rows[:8],rows[8:]])==[]

def test_end_of_transcript_can_remain_incomplete():
    assert interrupted_tails([[row(1,0,'The group discussed the')]])[0]['source_ids']==[1]
    assert interrupted_tails([[row(1,0,'El texto termina correctamente.')]])==[]

def test_unpunctuated_complete_statement_not_assumed_interrupted():
    assert interrupted_tails([[row(1,0,'El código identifica la pieza')]])==[]

def test_quarantine_rejected_prose_preserves_originals_and_other_theme():
    blocks=[[row(1,0,'Se explicó el proceso.'),row(2,4,'Alguien mencionó un documento'),
             row(3,8,'y se interrumpió la lectura de'),row(4,30,'Se habló de los materiales.')]]
    units=plan_context(blocks)['windows'][0]
    raw={'themes':[{'source_ids':[1],'title_es':'Proceso','summary_es':'Se explicó el proceso.'},
        {'source_ids':[2,3],'title_es':'Lectura','summary_es':'Se interrumpió la lectura del manual de seguridad.'}],
        'review_ids':[4]}
    initial=validate_rows(json.dumps(raw),units,'es')
    out=quarantine_interrupted(initial,units,blocks)
    assert [t['title_es'] for t in out['themes']]==['Proceso']
    assert out['interruption_review_ids']==[2,3]
    assert [r['source_id'] for r in out['gaps']]==[2,3,4]
    assert out['review_ids']==[4] and out['quarantined_themes'][0]['theme']==initial['themes'][1]
    assert initial['themes'][1]['summary_es'].endswith('manual de seguridad.')

def test_flagged_uncited_source_is_already_a_gap_not_duplicate():
    blocks=[[row(1,0,'Se habló de'),row(2,30,'Otro asunto.')]]
    units=plan_context(blocks)['windows'][0]
    initial=validate_rows('{"themes":[],"review_ids":[1]}',units,'es')
    out=quarantine_interrupted(initial,units,blocks)
    assert [r['source_id'] for r in out['gaps']]==[1,2]
    assert out['interruption_review_ids']==[1]
