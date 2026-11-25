from qa.minutes_acceptance import evaluate

def item(category,stamp,owner=None,due=None):
    return {'category':category,'sources':[{'timestamp':stamp}],'owner':owner,'due':due}

def test_acceptance_detects_proposal_promoted_to_decision():
    evidence={'review_required':True,'items':[
        item('action','00:00:01','Ana','Friday'),
        item('action','00:00:06','Luis','lunes'),
        item('proposal','00:00:12'),
        item('decision','00:00:18'),
    ]}
    assert all(evaluate(evidence).values())
    evidence['items'].append(item('decision','00:00:12'))
    assert not evaluate(evidence)['proposal_not_decision']
