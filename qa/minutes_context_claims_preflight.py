"""Independent fictitious exhibit-preparation fixture. No private content."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import plan_context
from engine.minutes_context_claims import claim_request,validate_claims,recovery_targets

TRANSCRIPT="""[00:00:01] Durante la visita técnica, la conservadora explicó
[00:00:05] que el fabricante reparó el marco, no que ella lo reparara.
[00:00:09] El coordinador recordó una antigua instrucción de otro proyecto:
[00:00:13] «Trasladen las cajas al taller».
[00:00:17] Esa instrucción fue un ejemplo histórico, no una orden de hoy.
[00:00:21] Después de explicar la iluminación, se habló de revisar las etiquetas.
[00:00:25] Se explicó que la luz intensa puede alterar ciertos pigmentos.
[00:00:29] Alguien mencionó una medida poco clara
[00:00:33] y la lectura se interrumpió a mitad de
[00:00:51] La siguiente explicación distinguió limpiar un marco de sustituirlo.
[00:01:15] Aviso: La exposición del viernes será en el salón principal."""
RUBRIC=[
 'The conservator explains; the manufacturer repairs; never reverse the actors.',
 'The old instruction belongs to a different historical project and is not a current order.',
 'Temporal sequence is explanatory, not a deadline; do not invent a new before/after relation.',
 'Preserve possibility of pigment damage, not certainty.',
 'Do not complete the interrupted measurement or attach it to the next topic.',
 'Distinguish cleaning a frame from replacing it.',
 'Retain the actual Friday exhibition notice separately.',
 'Each claim cites its own exact supporting phrases; review gaps remain visible.',
 'Readable coherent themes, no invented facts; no certification from lexical checks alone.'
]
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    blocks=list(source_blocks(TRANSCRIPT));rows=[r for b in blocks for r in b]
    items=explicit_source_items(rows,'es')
    assert [(i['category'],[r['source_id'] for r in i['sources']]) for i in items]==[('notice',[11])]
    plan=plan_context(blocks,items)
    assert len(plan['windows'])==1 and len(plan['structured_sources'])==1
    units=plan['windows'][0];messages,schema=claim_request(units,'es')
    # Mock intentionally bad temporal claim; never label as generated model output.
    raw={'themes':[{'title_es':'Visita técnica','claims':[
        {'sources':[{'id':i,'quote':rows[i-1]['text']} for i in (1,2)],
         'text_es':'La conservadora explicó que el fabricante reparó el marco.'},
        {'sources':[{'id':7,'quote':rows[6]['text']}],
         'text_es':'Antes de revisar los pigmentos, se explicó que la luz puede alterarlos.'}
    ]}],'review_ids':[8,9]}
    result=validate_claims(json.dumps(raw,ensure_ascii=False),units,'es',blocks=blocks)
    assert result['rejections'][0]['code']=='unsupported_before'
    assert recovery_targets(units,result)==[7]
    assert [r['source_id'] for r in result['gaps']]==list(range(3,11))
    assert len(result['themes'])==1
    for name,value in [('rubric.json',RUBRIC),('plan.json',plan),('request.json',{'messages':messages,'schema':schema}),
                       ('mock-result.json',result),('result.json',{'rows':len(rows),'windows':len(plan['windows']),
                         'model_requests':0,'scope':'offline mock structural preflight','recovery_target_ids':[7]})]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'transcript.txt').write_text(TRANSCRIPT,encoding='utf-8')
    print('Claim-level offline fixture passed; zero inference.',flush=True)
if __name__=='__main__':main(Path(sys.argv[1]))
