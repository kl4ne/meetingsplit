"""Fresh invented community-garden workshop; fixed rubric before inference."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import plan_context,_size

ROWS=[
 (0,'Durante la demostración del huerto comunitario'),
 (4,'se explicó que una capa de hojas puede'),
 (8,'reducir la evaporación del suelo,'),
 (12,'pero no sustituye el riego cuando hace falta.'),
 (17,'El facilitador distinguió la humedad superficial'),
 (21,'de la humedad cerca de las raíces.'),
 (40,'A training example illustrated a hypothetical purchase'),
 (44,'of new watering cans. It was not a real purchase or approval.'),
 (61,'Se habló de registrar la fecha de siembra'),
 (65,'sin atribuir a cada voluntario una parcela.'),
 (69,'La etiqueta identifica la planta.'),
 (73,'La etiqueta identifica la planta.'),
 (90,'Someone mentioned an unclear measurement'),
 (94,'and the recording stopped in the middle of'),
 (113,'La explicación siguiente trató de las herramientas.'),
 (117,'Se habló de limpiarlas sin dañar los mangos.'),
 (140,'Aviso: El taller del sábado será en el patio.'),
 (160,'Se aprobó conservar el horario actual.'),
 (180,'Nora Vega will send the list by Friday.'),
 (200,'The discussion distinguished sharing seedlings'),
 (204,'from assigning ownership of the garden plots.'),
 (225,'Aviso: Las hojas de referencia están disponibles en recepción.'),
]
TRANSCRIPT='\n'.join(f'[{t//3600:02d}:{t//60%60:02d}:{t%60:02d}] {s}' for t,s in ROWS)
EXPECTED={17:'notice',18:'decision',19:'action',22:'notice'}
RUBRIC=[
 'Record the workshop as teaching/discussion, not a sequence of administrative decisions.',
 'Leaves can reduce evaporation, but do not replace watering when necessary; distinguish surface moisture from moisture near roots.',
 'Hypothetical watering-can purchase is not a real purchase or approval.',
 'Record planting date without assigning plots to volunteers; label identifies the plant, avoid duplicate theme.',
 'Preserve unclear interrupted measurement for review; never guess its value or link it to the next subject.',
 'Clean tools without damaging handles.',
 'Distinguish sharing seedlings from assigning ownership of plots.',
 'Saturday workshop in the patio; current schedule approved; Nora Vega sends list by Friday inclusive; reference sheets at reception.',
 'No invented names, facts, decisions, tasks, or dates; original refs and review gaps retained.',
 'Coherent Spanish paragraphs, useful executive overview, no tables/timecodes, fewer unnecessary themes; no claim of semantic verification.',
]
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    blocks=list(source_blocks(TRANSCRIPT));rows=[r for b in blocks for r in b]
    items=explicit_source_items(rows,'es')
    actual={(r['source_id'],i['category']) for i in items for r in i['sources']}
    assert actual==set(EXPECTED.items()),actual
    plan=plan_context(blocks,items)
    assert not plan['overbudget_sources']
    assert sorted(r['source_id'] for u in plan['units'] for r in u['sources'])==[r['id'] for r in rows if r['id'] not in EXPECTED]
    assert len(blocks)==1 and 1<=len(plan['windows'])<=2
    result={'scope':'independent synthetic structural preflight only',
        'rows':len(rows),'words':sum(len(r['text'].split()) for r in rows),
        'extraction_blocks':len(blocks),'context_windows':len(plan['windows']),
        'context_payload_bytes':[_size(w) for w in plan['windows']],
        'explicit_outcomes':len(actual),'model_requests':0,
        'future_real_call_cap':6,'quality':'not evaluated'}
    for n,v in [('result.json',result),('rubric.json',RUBRIC),('plan.json',plan),('expected.json',EXPECTED)]:
        (out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'transcript.txt').write_text(TRANSCRIPT,encoding='utf-8')
    print(json.dumps(result),flush=True)
if __name__=='__main__':main(Path(sys.argv[1]))
