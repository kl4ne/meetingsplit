from engine.minutes_theme_presentation import separate_structured_themes
from engine.minutes_evidence import source_blocks

PROPOSAL='Proposal only: extend the reception hours to Sunday. Not approved.'
PENDING='Who will order replacement supplies? No responsible person or deadline was assigned.'
TOPIC='Se explicó cómo orientar a visitantes.'
BLOCKS=list(source_blocks('\n'.join(f'[00:00:0{i}] {s}' for i,s in enumerate((PROPOSAL,PENDING,TOPIC),1))))
def ref(i,quote):
    return {'source_id':i,'timestamp':f'00:00:0{i}','quote':quote}
def theme(i,text):
    return {'title_es':'Tema','summary_es':text,'sources':[ref(i,text)]}
def item(category,refs,text):
    return {'category':category,'owner':None,'due':None,'sources':refs,'text_es':text}
def test_only_complete_structured_events_are_partitioned():
    themes=[theme(1,PROPOSAL),theme(2,PENDING),theme(3,TOPIC)]
    items=[item('proposal',[ref(1,'Proposal only: extend the reception hours to Sunday.'),ref(1,'Not approved.')],
                'Se propuso ampliar la recepción al domingo. No fue aprobada.'),
           item('pending',[ref(2,PENDING)],'Falta determinar quién pedirá los suministros.')]
    retained,moved=separate_structured_themes(BLOCKS,themes,items,('es',))
    assert retained==themes[2:] and len(moved)==2
    assert len(themes)==3
    assert moved[0]['source_ids']==[1]

def test_incomplete_or_mixed_or_rejected_events_remain():
    themes=[theme(1,PROPOSAL),theme(2,PENDING),theme(3,TOPIC)]
    items=[item('proposal',[ref(1,'Proposal only: extend the reception hours to Sunday.')],
                'Se propuso ampliar la recepción al domingo.'),
           item('pending',[ref(2,PENDING)],'Falta determinar quién pedirá los suministros.')]
    kept,moved=separate_structured_themes(BLOCKS,themes,items,('es',),
                  [{'language':'es','rejected':[{'id':1}]}])
    assert kept==themes and moved==[]
