"""Fresh fictitious map-conservation workshop, rubric frozen before inference."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_context_windows import plan_context,_size

ROWS=[
 (0,'En el taller ficticio de conservación de mapas, la instructora explicó'),
 (4,'que la restauradora reparó la cubierta del atlas, no la instructora.'),
 (9,'El guía recordó una orden de un archivo antiguo:'),
 (13,'«Muevan las cajas al depósito».'),
 (17,'Era un ejemplo histórico, no una orden de esta reunión.'),
 (35,'Una funda de papel neutro puede proteger las hojas'),
 (39,'pero no elimina el riesgo causado por el agua.'),
 (43,'Se distinguió una mancha superficial de una rotura del papel.'),
 (47,'Después de explicar las manchas, se habló de cómo sostener los mapas.'),
 (65,'El ejemplo de comprar una mesa nueva era hipotético.'),
 (69,'No hubo compra ni aprobación en ese ejemplo.'),
 (85,'Someone mentioned an unclear measurement'),
 (89,'and the recording stopped in the middle of'),
 (108,'La explicación siguiente trató de los inventarios.'),
 (112,'Se explicó que registrar un préstamo no equivale a transferir la propiedad.'),
 (116,'La ficha identifica el documento, sin afirmar quién es su dueño.'),
 (140,'Aviso: La demostración del martes será en la sala de lectura.'),
 (160,'Se aprobó conservar el orden actual del inventario.'),
 (180,'Elena Ruiz will send the checklist by Thursday.'),
 (204,'Se habló de distinguir una copia de consulta de un original.'),
 (208,'El original se conserva en su funda durante la consulta.'),
 (225,'Aviso: Las hojas de práctica están disponibles en recepción.'),
]
TRANSCRIPT='\n'.join(f'[{t//3600:02d}:{t//60%60:02d}:{t%60:02d}] {s}' for t,s in ROWS)
EXPECTED={17:'notice',18:'decision',19:'action',22:'notice'}
RUBRIC=[
 'The instructor explains; the restorer repairs the atlas cover, not the instructor.',
 'The guide quotes a historical order to move boxes to storage; it is not a present order.',
 'Neutral paper can protect pages, but does not remove water risk; retain the modal and contrast.',
 'Distinguish a surface stain from a tear; after explaining stains, discussion concerns supporting maps, not a deadline or obligation.',
 'Hypothetical table purchase is neither a real purchase nor approval.',
 'Rows 12–13 contain an interrupted unclear measurement; preserve both for review without guessing or joining the next topic.',
 'Distinguish recording a loan from transferring ownership; the record identifies the document without identifying its owner.',
 'Distinguish a consultation copy from an original; retain the original in its sleeve during consultation.',
 'All four actual outcomes: Tuesday demonstration in reading room; existing inventory order approved; Elena Ruiz sends checklist by Thursday inclusive; practice sheets at reception.',
 'No invented operational outcomes, actors, names, numbers, dates or claims; each claim individually supported by its own exact references.',
 'Readable Spanish combined report, no repeated full overview paragraphs, no hidden warnings; navigation digest is not independent synthesis.',
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
