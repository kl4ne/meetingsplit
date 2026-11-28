"""Independent fabricated ASR-style fixture, no user meeting data.

Preflight checks exact source mapping and request budget, not generated quality.
The rubric is fixed before any inference. Future inference must compare both
arms against it and retain originals, not treat grouped IDs as semantic proof.
"""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.minutes_evidence import source_blocks,explicit_source_items
from engine.minutes_brief import editorial_input,editorial_request
from engine.minutes_context_windows import plan_context,request_spec,_size,compose_context

FRAGMENTS=[
 (0,'En el taller de conservación de textiles'),(4,'se explicó que la luz directa'),
 (8,'puede deteriorar el pigmento aunque'),(12,'el tejido parezca limpio.'),
 (16,'El instructor mostró dos tipos de protección.'),(21,'Una evita el polvo,'),
 (25,'pero no sustituye una barrera contra la luz.'),
 (30,'La explicación insistió en esa diferencia.'),(35,'No son el mismo tipo de protección.'),
 (50,'En un ejemplo ficticio, alguien dijo:'),(54,'«Aprobamos comprar diez vitrinas».'),
 (59,'Era una frase de práctica, no una decisión del taller.'),
 (75,'The facilitator explained the difference'),(80,'between identifying a stain'),
 (84,'and removing it. The first step does not'),(89,'authorize treatment.'),
 (95,'Se discutió cómo describir una mancha'),(100,'sin atribuirle una causa que no se conoce.'),
 (105,'Alguien mencionó un nombre poco claro'),(110,'y la grabación se cortó a mitad de'),
 (125,'La siguiente explicación trató de las etiquetas.'),
 (130,'Se explicó que el código de muestra'),(135,'identifica la pieza y no su propietario.'),
 (140,'El código identifica la pieza.'),(145,'El código identifica la pieza.'),
 (165,'Aviso: La demostración del lunes será en el salón de muestras.'),
 (185,'Se aprobó conservar el formulario actual.'),
 (205,'Lena Ortiz se comprometió a enviar el catálogo el viernes.'),
 (225,'Se explicó la diferencia entre una ficha de observación'),
 (230,'y una instrucción de tratamiento.'),(235,'Una describe lo observado.'),
 (240,'La otra explica cómo actuar, sin convertir el ejemplo en una orden real.'),
 (260,'The discussion returned to safe storage.'),(265,'It emphasized ventilation,'),
 (270,'without exposing samples to direct sunlight.'),
 (290,'Aviso: El material de referencia estará disponible en la recepción.'),
]
def stamp(seconds):
    return f'{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d}'
TRANSCRIPT='\n'.join(f'[{stamp(t)}] {s}' for t,s in FRAGMENTS)
RUBRIC=[
 'Describe the conservation workshop as teaching/discussion, not a meeting of invented decision makers.',
 'Direct sunlight can damage pigment even when fabric appears clean; dust protection does not replace light protection.',
 'The purchase of ten display cases is explicitly fictional, not an actual approval or budget.',
 'Identifying a stain does not authorize treatment; describe without inventing cause.',
 'Do not reconstruct unclear name or missing words from interrupted speech.',
 'Sample code identifies the piece, not its owner; repeated statement need not become duplicate themes.',
 'Observation sheet describes observation; treatment instruction explains action, not a real order from the example.',
 'Ventilation and avoiding direct sunlight remain distinct storage considerations.',
 'Keep actual Monday demonstration notice, current form approval, named Friday commitment and reference-material notice separately.',
 'Fluent Spanish, fewer meaningful themes rather than micro-themes, no invented actors/events, no hidden gaps.',
]

def main(output):
    output.mkdir(parents=True,exist_ok=False)
    blocks=list(source_blocks(TRANSCRIPT));rows=[r for b in blocks for r in b]
    # Explicit records are shared by both arms; exclude only known full structured sources
    # from contextual transport. Preflight separately checks that the four actual records
    # are preserved; fictional split quote is not assumed safe by extraction.
    explicit=explicit_source_items(rows,'es')
    expected={26:'notice',27:'decision',28:'action',36:'notice'}
    actual={(r['source_id'],item['category']) for item in explicit for r in item['sources']}
    assert all((i,cat) in actual for i,cat in expected.items())
    # Existing per-row extractor may misread the quoted practice line as an agreement.
    # Keep diagnostic explicit; do not use a false record to remove it from context.
    structured=[item for item in explicit if all(r['source_id'] in expected and expected[r['source_id']]==item['category'] for r in item['sources'])]
    plan=plan_context(blocks,structured)
    accounted=[r for u in plan['units'] for r in u['sources']]+plan['structured_sources']+plan['overbudget_sources']
    assert len(accounted)==len(rows)
    assert {r['source_id']:(r['timestamp'],r['quote']) for r in accounted}=={
        r['id']:(r['timestamp'],r['text']) for r in rows}
    old=list(editorial_input(blocks,structured,explicit_items=structured))
    old_requests=[editorial_request(s,'es')[0][1]['content'] for s in old]
    new_requests=[request_spec(w,'es')[0][1]['content'] for w in plan['windows']]
    # Mock failure, not a fake generated minute.
    def empty(*args):return '{"themes":[]}'
    fallback=compose_context(plan,'es',empty)
    expected_gaps={r['source_id'] for u in plan['units'] for r in u['sources']}
    assert {r['source_id'] for r in fallback['gaps']}==expected_gaps
    checks={'exact_partition':True,'all_four_structured_sources':True,
        'fictional_quote_retained_in_context':11 in expected_gaps,
        'empty_response_keeps_all_context_sources':True,
        'bounded_windows':all(_size(w)<=4500 for w in plan['windows']),
        'no_model_calls':True}
    report={'scope':'synthetic structural preflight, no inference or editorial acceptance',
        'checks':checks,'rows':len(rows),'words':sum(len(r['text'].split()) for r in rows),
        'old_excerpt_count':sum(map(len,old)),'old_initial_windows':len(old),
        'old_payload_bytes':[len(s.encode('utf-8')) for s in old_requests],
        'context_units':len(plan['units']),'context_initial_windows':len(plan['windows']),
        'context_payload_bytes':[len(s.encode('utf-8')) for s in new_requests],
        'structured_source_ids':[r['source_id'] for r in plan['structured_sources']],
        'overbudget_source_ids':[r['source_id'] for r in plan['overbudget_sources']],
        'unexpected_explicit_extraction':sorted([list(x) for x in actual if expected.get(x[0])!=x[1]]),
        'empty_response_gaps':len(fallback['gaps']),'model_requests':0}
    for name,value in [('result.json',report),('plan.json',plan),('rubric.json',RUBRIC),
        ('structured.json',structured),('original-explicit-extraction.json',explicit)]:
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'transcript.txt').write_text(TRANSCRIPT,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    return 0 if all(checks.values()) else 2

if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1])))
