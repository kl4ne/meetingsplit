"""Bounded synthetic retry; never relax editorial validation."""
import json
import pytest
from engine import summarize
from engine.minutes_brief import editorial_retry_sources,merge_editorial_retry

def ref(i):
    return {'source_id':i,'timestamp':f'00:00:{i:02d}','quote':f'Se revisó el material {i}.'}

def theme(title, *refs):
    return {'title_es':title,'summary_es':'Se revisó el material.','sources':list(refs)}

def test_retry_is_bounded_and_deduplicated():
    refs=[ref(i) for i in range(1,9)]
    assert editorial_retry_sources([refs[0],*refs])==refs[:5]

def test_only_repaired_passages_clear_gaps():
    original=theme('Material',ref(1))
    repaired=theme('Orientación',ref(2))
    result,gaps=merge_editorial_retry([original],[ref(1),ref(2),ref(3)],
                                     [repaired],[],'es')
    assert result==[original,repaired]
    assert gaps==[ref(1),ref(3)]

def test_duplicate_theme_or_repeated_rejection_does_not_clear_gap():
    original=theme('Material',ref(1))
    repaired=[theme('Material',ref(2)),theme('Orientación',ref(3))]
    result,gaps=merge_editorial_retry([original],[ref(2),ref(3)],repaired,[ref(3)],'es')
    assert result==[original,repaired[1]]
    assert gaps==[ref(2),ref(3)]

@pytest.mark.parametrize('repair_fails',[False,True])
def test_pipeline_retries_only_rejected_source_once(monkeypatch,repair_fails):
    lines=['Se revisó la preparación del equipo.',
           'Se explicó la atención a visitantes.',
           'Se revisó el registro.',
           'Se revisó la guía de orientación.']
    transcript='\n'.join(f'[00:00:0{i}] {line}' for i,line in enumerate(lines,1))
    calls=[]
    def reply(messages,*args,json_output,**kwargs):
        if json_output and 'items' in json_output['properties']:
            return '{"items":[]}'
        if json_output:
            ids=[r['id'] for r in json.loads(messages[1]['content'])['sources']]
            calls.append(ids)
            if len(calls)==1:
                return json.dumps({'themes':[
                    {'source_ids':[1],'title_es':'Preparación','summary_es':lines[0]},
                    {'source_ids':[2],'title_es':'Atención','summary_es':'Se aprobó la atención a visitantes.'},
                ]})
            assert ids==[2]
            if repair_fails:
                raise TimeoutError('Synthetic timeout')
            return json.dumps({'themes':[{'source_ids':[2],'title_es':'Atención','summary_es':lines[1]}]})
        data=json.loads(messages[1]['content'])
        return '\n\n'.join(f"{record['summary']} [{key}]" for key,record in data.items())
    monkeypatch.setattr(summarize,'ollama_chat',reply)
    evidence={}
    report=summarize.summarize_local(transcript,'both','es','qwen3.5:9b',evidence_sink=evidence.update)
    assert calls==[[1,2,3,4],[2]]
    assert lines[0] in report and 'Se aprobó la atención' not in report
    assert bool(evidence['editorial_gaps'])==repair_fails
    if not repair_fails:
        assert lines[1] in report
