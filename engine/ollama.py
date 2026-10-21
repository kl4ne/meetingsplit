"""Fixed local endpoints; no proxies, redirects, remote models or implicit downloads."""
from __future__ import annotations
import json
from contextlib import contextmanager
import http.client
import os
from pathlib import Path
import subprocess
import select
import time
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler, Request
from desktop.storage import validate_local_folder
from engine.control import Cancellation

MODEL = 'qwen3:4b'
DEFAULT_ENDPOINT = 'http://127.0.0.1:11434'
MANAGED_ENDPOINT = 'http://127.0.0.1:11435'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Ollama redirects are not permitted')


def _open(endpoint, route, payload=None, timeout=20):
    if endpoint not in (DEFAULT_ENDPOINT,MANAGED_ENDPOINT):
        raise ValueError('Only the fixed loopback Ollama endpoints are allowed')
    if route not in ('/api/version','/api/tags','/api/show','/api/pull','/api/chat'):
        raise ValueError('Unsupported Ollama operation')
    body=None if payload is None else json.dumps(payload).encode('utf-8')
    request=Request(endpoint+route,body,{'Content-Type':'application/json'})
    return build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=timeout)


def request_json(endpoint, route, payload=None, timeout=3):
    with _open(endpoint,route,payload,timeout) as response:
        data=response.read(4*1024**2+1)
    if len(data)>4*1024**2: raise ValueError('Ollama response is too large')
    result=json.loads(data)
    if not isinstance(result,dict) or result.get('error'):
        raise RuntimeError('Ollama returned an error: '+str(result.get('error','invalid response'))[:200])
    return result


def existing_status(endpoint=DEFAULT_ENDPOINT) -> dict:
    try:
        version=request_json(endpoint,'/api/version').get('version')
        models=request_json(endpoint,'/api/tags').get('models',[])
        installed=next((m for m in models if (m.get('name')==MODEL or m.get('model')==MODEL)
                        and not m.get('remote_host') and not m.get('remote_model')),None)
        return {'available':bool(version),'version':version,'model':installed}
    except (OSError,ValueError,RuntimeError):
        return {'available':False,'version':None,'model':None}


@contextmanager
def _stream_open(endpoint, route, payload, cancel):
    """Cold model load can take minutes before headers; keep this wait cancellable."""
    if endpoint not in (DEFAULT_ENDPOINT,MANAGED_ENDPOINT) or route not in ('/api/chat','/api/generate','/api/pull'):
        raise ValueError('Only fixed local Ollama streaming routes are allowed')
    port=11434 if endpoint==DEFAULT_ENDPOINT else 11435
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
    try:
        connection.request('POST',route,json.dumps(payload).encode('utf-8'),{'Content-Type':'application/json'})
        connection.sock.settimeout(20)
        deadline=time.monotonic()+180
        while not select.select([connection.sock],[],[],.25)[0]:
            cancel.check()
            if time.monotonic()>deadline: raise TimeoutError('Ollama model did not begin responding in 180 seconds')
        cancel.check()
        response=connection.getresponse()
        if response.status!=200: raise RuntimeError('Ollama HTTP error '+str(response.status))
        with response: yield response
    finally: connection.close()


def stream_json(endpoint, route, payload, cancel, progress, deadline_seconds=900):
    deadline=time.monotonic()+deadline_seconds
    with _stream_open(endpoint,route,payload,cancel) as response:
        while True:
            cancel.check()
            if time.monotonic()>deadline: raise TimeoutError('Ollama operation exceeded its time limit')
            # One bounded line/read; a stalled peer times out in <=20 seconds.
            line=response.readline(1024*1024+1)
            if not line: break
            if len(line)>1024*1024: raise ValueError('Ollama stream record too large')
            data=json.loads(line)
            if not isinstance(data,dict): raise ValueError('Invalid Ollama stream record')
            if data.get('error'): raise RuntimeError(str(data['error'])[:300])
            progress(data)
            yield data


def chat(messages, endpoint=DEFAULT_ENDPOINT, model=MODEL, cancel=None, progress=lambda _:None, timeout=900):
    if model!=MODEL: raise ValueError('Only the local qwen3:4b model is supported')
    control=cancel or Cancellation()
    chunks=[]; total=0; done=False; last_update=0; thinking_chars=0
    # The current official qwen3:4b reports thinking.values=[true]. Requesting
    # false is then coerced to its default and leaks reasoning into content on
    # some runtimes. Enable the separate thinking channel and discard that field.
    # Reserve enough generation/context budget for both reasoning and final text.
    payload={'model':MODEL,'messages':[dict(m) for m in messages],'stream':True,'think':True,
             'keep_alive':0,'truncate':False,'options':{'temperature':0.6,'num_ctx':16384,
                'num_predict':8192,'repeat_penalty':1.1}}
    for record in stream_json(endpoint,'/api/chat',payload,control,lambda _:None,timeout):
        text=record.get('message',{}).get('content','')
        thinking_chars+=len(record.get('message',{}).get('thinking',''))
        if thinking_chars>512*1024: raise ValueError('Ollama reasoning exceeded its limit')
        total += len(text)
        if total>1024*1024: raise ValueError('Ollama generated too much text')
        chunks.append(text)
        if time.monotonic()-last_update>.5:
            progress('Ollama: '+str(total)+' characters' if total else 'Ollama: preparing the report…');last_update=time.monotonic()
        if record.get('done'):
            if record.get('done_reason')=='length':
                raise RuntimeError('Ollama reached its output limit; the incomplete report was not saved')
            done=True; break
    result=''.join(chunks).strip()
    if not done or not result: raise RuntimeError('Ollama generation incomplete or empty')
    if '<think>' in result or '</think>' in result:
        if '</think>' not in result: raise RuntimeError('Ollama returned incomplete thinking instead of a report')
        result=result.rsplit('</think>',1)[-1].strip()
        if not result: raise RuntimeError('Ollama returned thinking without a final report')
    return result


class LocalService:
    """Reuse a ready existing model, otherwise own a separate scoped subprocess.

    Never pull into an existing service: its actual model directory is unknowable
    from the API. Only the managed process writes models to a validated disk.
    """
    def __init__(self, root: Path, cancel=None, progress=lambda _:None, reuse=True):
        self.root=validate_local_folder(root)
        self.cancel=cancel or Cancellation(); self.progress=progress
        self.reuse=reuse; self.process=None; self.log=None
        self.endpoint=DEFAULT_ENDPOINT

    def __enter__(self):
        if self.reuse and existing_status().get('model'):
            return self
        from desktop.components import OLLAMA_PACKAGE
        folder=self.root/'Componentes'/OLLAMA_PACKAGE.name
        exe=folder/'ollama.exe'
        if not exe.is_file():
            raise RuntimeError('Configure optional Ollama components in Settings first.')
        validate_local_folder(folder)
        # Do not trust another process on the reserved managed port.
        import socket
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1',11435))==0:
                raise RuntimeError('Ollama setup port 11435 is busy. Close the other MeetingSplit local AI operation.')
        model_dir=self.root/'Modelos'/'Ollama'
        model_dir.mkdir(parents=True,exist_ok=True)
        validate_local_folder(model_dir)
        env=os.environ.copy()
        env.update(OLLAMA_HOST='127.0.0.1:11435',OLLAMA_MODELS=str(model_dir),
                   OLLAMA_NO_CLOUD='1',OLLAMA_MAX_LOADED_MODELS='1',OLLAMA_NUM_PARALLEL='1',
                   OLLAMA_CONTEXT_LENGTH='8192')
        self.endpoint=MANAGED_ENDPOINT
        self.log=(self.root/'Componentes'/'ollama-server.log').open('ab')
        try:
            self.process=subprocess.Popen([str(exe),'serve'],cwd=str(folder),env=env,
                stdin=subprocess.DEVNULL,stdout=self.log,stderr=self.log,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+45
            while time.monotonic()<deadline:
                self.cancel.check()
                if self.process.poll() is not None: raise RuntimeError('Managed Ollama could not start; see local component log.')
                if existing_status(self.endpoint)['available']: return self
                self.cancel.event.wait(.25)
            raise TimeoutError('Managed Ollama did not start in 45 seconds')
        except BaseException:
            self.__exit__(None,None,None); raise

    def ensure_model(self, allow_download=False):
        status=existing_status(self.endpoint)
        if status['model']:
            details=request_json(self.endpoint,'/api/show',{'model':MODEL})
            if details.get('remote_host') or details.get('remote_model'):
                raise RuntimeError('Remote Ollama model aliases are not allowed')
            return status['model']
        if not allow_download or not self.process:
            raise RuntimeError('qwen3:4b is missing. Use optional component setup to download it.')
        import shutil
        if shutil.disk_usage(self.root).free<6*1024**3: raise OSError('At least 6 GiB free is required for the model download')
        success=False
        for row in stream_json(self.endpoint,'/api/pull',{'model':MODEL,'stream':True},self.cancel,
                               lambda r:self.progress(f"qwen3:4b: {r.get('status','')} {r.get('completed',0)//1048576}/{r.get('total',0)//1048576} MiB"),3600):
            if row.get('status')=='success': success=True
        model=existing_status(self.endpoint)['model']
        if not success or not model: raise RuntimeError('Model download was not confirmed by Ollama')
        return model

    def __exit__(self, *_):
        if self.process and self.process.poll() is None:
            if os.name=='nt':
                # Terminate only the owned server's tree, including model runners.
                taskkill=Path(os.environ.get('WINDIR',r'C:\Windows'))/'System32'/'taskkill.exe'
                try:
                    subprocess.run([str(taskkill),'/PID',str(self.process.pid),'/T','/F'],
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=8,
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                except (OSError,subprocess.TimeoutExpired): self.process.terminate()
            else: self.process.terminate()
            try: self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.wait(timeout=3)
        if self.log: self.log.close()


def setup_ollama(root, progress, cancel):
    from desktop.components import install_package, OLLAMA_PACKAGE
    component_root=validate_local_folder(root)/'Componentes'
    component_root.mkdir(exist_ok=True)
    receipt=component_root/'ollama-validation.json'
    receipt.write_text(json.dumps({'ok':False,'status':'testing'}),encoding='utf-8')
    (component_root/'ollama-smoke-minutes.md').unlink(missing_ok=True)
    # An existing service with the exact local model requires no installation.
    if not existing_status().get('model'):
        install_package(OLLAMA_PACKAGE,root,progress,cancel)
    with LocalService(root,cancel,progress) as service:
        model=service.ensure_model(allow_download=True)
        details=request_json(service.endpoint,'/api/show',{'model':MODEL})
        # Preserve the actual downloaded model's license, not a guessed label.
        license_text=details.get('license','')
        if not license_text.strip(): raise RuntimeError('Ollama did not supply the model license')
        (component_root/'QWEN3_LICENSE.txt').write_text(license_text,encoding='utf-8')
        from engine.summarize import summarize_local
        transcript='[00:00:01] Ana will send the draft on Friday.\n[00:00:06] Luis agreed to review it on Monday.'
        report=summarize_local(transcript,'minutes','en',MODEL,progress=progress,
                               endpoint=service.endpoint,cancel=cancel)
        (component_root/'ollama-smoke-minutes.md').write_text(report,encoding='utf-8')
        (component_root/'ollama-validation.json').write_text(json.dumps({
            'ok':True,'model':MODEL,'digest':model.get('digest'),'endpoint':service.endpoint,
            'test':'synthetic meeting, generation completed; factual review required',
            'characters':len(report)},indent=2),encoding='utf-8')
