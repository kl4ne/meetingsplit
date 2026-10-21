"""Grounded meeting prompts + optional entirely local Ollama summarization."""
from __future__ import annotations
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def instructions(mode: str='both', language: str='es') -> str:
    goal={
        'summary':'Produce un resumen ejecutivo fiel',
        'minutes':'Produce una minuta formal y detallada',
        'both':'Produce primero un resumen ejecutivo y luego una minuta formal',
    }[mode]
    lang={
        'es':'en español',
        'en':'in English',
        'both':'en dos secciones independientes: español e inglés',
    }[language]
    return f'''Actúa como secretario documental, sin inventar información.
{goal} {lang} a partir de la transcripción de la reunión.
La grabación puede alternar español e inglés; conserva nombres propios,
cifras, cargos, acuerdos y matices. No interpretes una propuesta como resolución.
Distingue acuerdos confirmados, ideas discutidas, desacuerdos y pendientes.
Para las tareas, registra descripción, responsable, fecha y estado solamente
cuando esté expresado; si falta algo indica «No especificado».
Incluye referencias a marcas de tiempo [HH:MM:SS] de la fuente cuando existan.
No inventes nombres de oradores: usa «Participante no identificado».
Marca [REVISAR AUDIO] ante palabras dudosas, cortes o fechas ambiguas.
Encabezados: fecha (si se conoce), título, participantes (si constan),
resumen, temas, acuerdos confirmados, tareas, pendientes y seguimiento.
No agregues hechos que no estén en el texto.''' 


def ollama_chat(messages: list[dict], model: str='qwen3:4b', timeout: int=600) -> str:
    """Talk ONLY to loopback Ollama, not the public Internet."""
    payload=json.dumps({
        'model':model,'messages':messages,'stream':False,
        'options':{'temperature':0.1, 'num_ctx':8192},
    }).encode('utf-8')
    req=Request('http://127.0.0.1:11434/api/chat',payload,
                {'Content-Type':'application/json'},method='POST')
    try:
        with urlopen(req,timeout=timeout) as response:
            result=json.load(response)
    except (URLError,HTTPError,TimeoutError) as exc:
        raise RuntimeError('Ollama local no responde o el modelo no está instalado. '
                           'Usa las plantillas de ChatGPT/Gemini o instala Ollama y el modelo.') from exc
    reply=result.get('message',{}).get('content','').strip()
    if not reply: raise RuntimeError('Ollama no devolvió texto')
    return reply


def summarize_local(transcript: str, mode: str, language: str, model: str,
                    progress=lambda msg:None) -> str:
    if not transcript.strip():
        raise ValueError('No hay transcripción para resumir')
    # Hierarchical approach to avoid dumping a three-hour transcript into one context.
    blocks=[]
    # split on line boundaries instead of cutting timestamps/sentences arbitrarily
    current=[];size=0
    for line in transcript.splitlines():
        if current and size+len(line)>10500:
            blocks.append('\n'.join(current));current=[];size=0
        current.append(line);size+=len(line)+1
    if current:blocks.append('\n'.join(current))
    notes=[]
    for i,block in enumerate(blocks,1):
        progress(f'Analizando transcripción, sección {i}/{len(blocks)}')
        note=ollama_chat([
            {'role':'system','content':'Extracción factual de reunión, en español. No inventes ni completes huecos.'},
            {'role':'user','content':f'''Extrae hechos, temas, resoluciones confirmadas, tareas y fechas
con su marca temporal. No resumas eliminando obligaciones. Esta es la parte {i}/{len(blocks)}.

{block}'''}],model)
        notes.append(f'SECCIÓN {i}\n{note}')
    # Recursively consolidate until size safely fits num_ctx.
    while sum(map(len,notes))>19000 and len(notes)>1:
        compact=[]
        for i in range(0,len(notes),2):
            part='\n\n'.join(notes[i:i+2])
            compact.append(ollama_chat([
                {'role':'system','content':'Consolida hechos de una reunión sin inventar.'},
                {'role':'user','content':'Fusiona estas notas fielmente; preserva referencias y discrepancias:\n'+part},
            ],model))
        notes=compact
    progress('Generando documento final local')
    return ollama_chat([
        {'role':'system','content':instructions(mode,language)},
        {'role':'user','content':'A continuación hay notas con marcas temporales extraídas de la grabación. Úsalas como única fuente.\n\n'+'\n\n'.join(notes)},
    ],model)
