import json
from zipfile import ZipFile
import pytest
from qa import minutes_private_compare as q

def fixture(tmp_path,*,alter=False,duplicate=False,wrong_version=False):
    p=tmp_path/'RESULTADOS_COMPLETOS.zip'
    transcript='[00:00:01] Se explicó el proceso.\n[00:00:04] Los materiales están en recepción.'
    ref={'source_id':1,'timestamp':'00:00:01','quote':'Se explicó el proceso.'}
    e={'narrative_strategy':'localized_editorial','items':[],
        'editorial_themes':[{'title_es':'Proceso','summary_es':'Se explicó el proceso.',
            'sources':[dict(ref,quote='No aparece en la fuente.') if alter else ref]}],
        'editorial_gaps':[],'source_accounting':{'uncited_passages':[]}}
    m={'version':'0.8.18' if wrong_version else '0.8.19','status':'complete',
        'summary_status':'needs_review','resume_signature':{'settings':{'report':'both',
            'language':'es','ollama_model':q.ollama.MODEL}}}
    with ZipFile(p,'w') as z:
        for key,value in [('transcript',transcript),('baseline','# Minuta\nSe explicó el proceso.'),
            ('evidence',json.dumps(e)),('manifest',json.dumps(m))]:
            z.writestr(q.MEMBERS[key],value)
        z.writestr('RESULTADOS_COMPLETOS/Audio/parte_01.mp3',b'not real audio')
        if duplicate:z.writestr(q.MEMBERS['transcript'].upper(),transcript)
    return p

def test_inspect_no_network_no_write_no_audio_access(tmp_path,monkeypatch):
    p=fixture(tmp_path);before=q.hash_file(p)
    def fail(*a,**k):raise AssertionError('Unexpected network or inference')
    monkeypatch.setattr(q.ollama,'existing_status',fail)
    monkeypatch.setattr(q.summarize,'summarize_local',fail)
    original=ZipFile.open
    def guard(self,name,*a,**k):
        assert '/Audio/' not in getattr(name,'filename',str(name))
        return original(self,name,*a,**k)
    monkeypatch.setattr(ZipFile,'open',guard)
    r=q.inspect(p)
    assert r['model_requests']==0 and r['rows']==2 and r['context_windows']==1
    assert list(tmp_path.iterdir())==[p] and q.hash_file(p)==before

@pytest.mark.parametrize('options',[{'alter':True},{'duplicate':True},{'wrong_version':True}])
def test_unsafe_or_incompatible_baseline_blocked(tmp_path,options):
    with pytest.raises(ValueError):q.inspect(fixture(tmp_path,**options))

def test_no_consent_no_connection_or_output(tmp_path,monkeypatch):
    p=fixture(tmp_path)
    monkeypatch.setattr(q,'verify_model',lambda:pytest.fail('Called service without consent'))
    with pytest.raises(ValueError):q.run_comparison(p,tmp_path,'no')
    assert list(tmp_path.iterdir())==[p]

@pytest.mark.parametrize('version,digest,local',[('0.40.6','wrong',True),('0.40.7',q.MODEL_DIGEST,True),
    ('0.40.18',q.MODEL_DIGEST,False)])
def test_model_and_runtime_mismatch_blocked(monkeypatch,version,digest,local):
    monkeypatch.setattr(q.ollama,'existing_status',lambda *a:{'available':True,'version':version,'model':{'digest':digest}})
    monkeypatch.setattr(q.ollama,'reusable_existing',lambda *a:local)
    with pytest.raises(RuntimeError):q.verify_model()

@pytest.mark.parametrize('version',['0.40.6','0.40.18'])
def test_explicit_allowed_runtime_recorded(monkeypatch,version):
    monkeypatch.setattr(q.ollama,'existing_status',lambda *a:{'available':True,'version':version,'model':{'digest':q.MODEL_DIGEST}})
    monkeypatch.setattr(q.ollama,'reusable_existing',lambda *a:True)
    assert q.verify_model()['runtime_matches_linux_qa']==(version=='0.40.18')

def test_live_mock_preserves_input_and_uses_new_output(tmp_path,monkeypatch):
    p=fixture(tmp_path);before=q.hash_file(p)
    monkeypatch.setattr(q,'verify_model',lambda:{'runtime':'0.40.18'})
    calls=[]
    def reply(messages,model,*,json_output,**kwargs):
        calls.append(kwargs)
        if 'items' in json_output['properties']:return '{"items":[]}'
        return '{"themes":[{"source_ids":[1,2],"title_es":"Proceso","summary_es":"Se explicó el proceso. Los materiales están en recepción."}],"review_ids":[]}'
    monkeypatch.setattr(q.summarize,'ollama_chat',reply)
    out,r=q.run_comparison(p,tmp_path,q.CONSENT)
    assert r['completed'] and r['original_zip_unchanged'] and r['requests']==2
    assert len(calls)==2 and all(c['endpoint']==q.ollama.DEFAULT_ENDPOINT for c in calls)
    assert set(x.name for x in out.iterdir())=={'CANDIDATO_CONTEXTUAL.md','CANDIDATO_EVIDENCIAS.json','COMPARACION_TECNICA.json'}
    assert q.hash_file(p)==before and not r['semantic_acceptance']

def test_call_budget_counts_attempts_and_does_not_publish_incomplete_report(tmp_path,monkeypatch):
    p=fixture(tmp_path)
    monkeypatch.setattr(q,'verify_model',lambda:{'runtime':'0.40.18'})
    monkeypatch.setattr(q,'CALL_CAP',1)
    monkeypatch.setattr(q.summarize,'ollama_chat',lambda *a,**k:'{"items":[]}')
    out,r=q.run_comparison(p,tmp_path,q.CONSENT)
    assert not r['completed'] and r['requests']==1 and r['error_type']=='BudgetExceeded'
    assert set(x.name for x in out.iterdir())=={'COMPARACION_TECNICA.json'}
