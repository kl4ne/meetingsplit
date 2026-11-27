"""Independent varied bilingual synthetic fixture (not the historical 29-block recording).

The timeline spans 2h15m. Speech is synthetic text, not audio or a measure of
natural meeting accuracy. All assertions are fixed before model execution.
"""
import json,sys,time,re
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama,summarize
from engine.minutes_evidence import source_blocks
from qa.minutes_editorial_ab import VERSION,DIGEST
from qa.minutes_long_acceptance import timestamp,score

SECTIONS = [
  {
    "name": "recepción",
    "lines": [
      "El equipo explicó que una persona nueva necesita una orientación breve, sin exigirle que conozca previamente el edificio.",
      "La información sobre accesibilidad debe estar disponible en el mostrador; la conversación distinguió la bienvenida del registro administrativo.",
      "Visitors who need assistance can use the entrance ramp. The discussion covered how to describe accessible routes without disclosing private contact information.",
      "Se examinó el ejemplo de una familia que llega por primera vez y pregunta dónde encontrar materiales de consulta.",
      "The reception guide describes the difference between general directions and questions requiring a private conversation.",
      "La explicación abordó cómo escuchar una consulta completa antes de remitirla al servicio adecuado."
    ]
  },
  {
    "name": "biblioteca",
    "lines": [
      "Se analizó la distribución de las estanterías para que los libros infantiles sean fáciles de localizar.",
      "The reading group discussed the difference between a reference book and an item available for lending.",
      "Se explicó la utilidad de separar los ejemplares dañados sin confundirlos con materiales descartados.",
      "La conversación abordó la identificación de libros devueltos y la revisión de su estado físico.",
      "Participants described a reading activity that uses short passages followed by questions about the text.",
      "Se revisó la organización de los materiales de lectura en función de su público y su contenido."
    ]
  },
  {
    "name": "privacidad",
    "lines": [
      "The privacy guide distinguishes personal contact details from information intended for public display.",
      "Se explicó por qué una consulta individual no debe aparecer en el cartel de actividades generales.",
      "La conversación abordó el uso de ejemplos ficticios al enseñar a manejar notas confidenciales.",
      "Participants discussed limiting access to sensitive files to the appropriate people, without naming individuals.",
      "Se examinó la diferencia entre conservar un registro interno y publicar información de una actividad.",
      "The group discussed how to describe an incident in general terms without including unnecessary personal details."
    ]
  },
  {
    "name": "inventario",
    "lines": [
      "Se explicó la diferencia entre existencias disponibles, materiales prestados y artículos apartados para revisión.",
      "The inventory discussion covered damaged packaging and the need to distinguish it from damaged contents.",
      "Se revisó un ejemplo de etiquetas que describen el contenido de una caja sin atribuirle un valor monetario.",
      "Participants discussed grouping supplies by type rather than by the name of the person who received them.",
      "Se habló de mejorar la legibilidad de las etiquetas utilizadas en los estantes.",
      "The discussion distinguished supplies consumed during activities from reusable equipment."
    ]
  },
  {
    "name": "formación",
    "lines": [
      "Se habló de preparar ejemplos que ayuden a los voluntarios a distinguir preguntas frecuentes de solicitudes excepcionales.",
      "The training discussion covered how to explain a procedure using a demonstration before asking someone to practice.",
      "Se explicó que una instrucción técnica y una recomendación pedagógica tienen funciones distintas.",
      "Participants examined a fictional example of a trainee who needs additional time to understand the reference materials.",
      "Se habló de revisar la claridad de las instrucciones para personas que leen en un segundo idioma.",
      "The discussion examined how feedback on a practice exercise differs from an assessment of a person's overall performance."
    ]
  },
  {
    "name": "comunicación",
    "lines": [
      "La conversación abordó la diferencia entre un aviso general y una comunicación dirigida a una persona concreta.",
      "The communications discussion examined how a short announcement can convey a location without unnecessary background.",
      "Se revisó el ejemplo de un mensaje que explica un cambio de sala sin modificar la hora de una actividad.",
      "Participants described why consistent terminology helps people recognize announcements in different languages.",
      "Se explicó la importancia de distinguir una fecha anunciada de una fecha que todavía se discute.",
      "The group discussed how to present public information in clear language without adding private details."
    ]
  },
  {
    "name": "seguridad",
    "lines": [
      "Se examinó la ubicación de las salidas y los pasos de circulación alrededor de los espacios de reunión.",
      "The safety discussion distinguished general orientation information from individual emergency assistance.",
      "Se explicó la utilidad de mantener visibles las señales de acceso durante una actividad.",
      "Participants discussed the difference between a routine equipment inspection and an incident report.",
      "Se revisó el ejemplo de una zona de paso que debe mantenerse libre de materiales.",
      "The discussion covered the purpose of documenting an equipment fault without attributing responsibility prematurely."
    ]
  },
  {
    "name": "archivo",
    "lines": [
      "Se habló de organizar las carpetas por contenido y de mantener separados los borradores de los documentos finales.",
      "The archive discussion covered the difference between an original record and a working copy.",
      "Se explicó cómo una descripción del contenido facilita localizar documentos sin abrirlos todos.",
      "Participants discussed the use of consistent names for files produced during different activities.",
      "Se analizó la distinción entre materiales de consulta vigentes y versiones anteriores conservadas por referencia.",
      "The discussion covered the purpose of recording a document's context without changing its original wording."
    ]
  },
  {
    "name": "seguimiento",
    "lines": [
      "Se habló de revisar la claridad de las observaciones recibidas durante las actividades.",
      "The group discussed the distinction between feedback that describes an experience and feedback that requests a change.",
      "Se explicó el valor de reunir preguntas similares sin presentar las opiniones individuales como acuerdos del equipo.",
      "Participants reviewed a fictional example of a follow-up conversation in which the original question was still unresolved.",
      "Se habló de preparar ejemplos prácticos de orientación para la siguiente sesión de formación.",
      "The final discussion distinguished matters already resolved from questions that still require clarification."
    ]
  }
]

# Explicit outcomes are spread across the start, middle and end.
EVENTS=[
    (195,"Se aprobó mantener el horario actual de recepción.","decision",None,None,None),
    (450,"Ana Ruiz will send the visitor guide by Friday.","action","Ana Ruiz","Friday",None),
    (750,"Proposal only: extend reception hours to Sunday. Not approved.","proposal",None,None,None),
    (1200,"Ya empezaremos el mes de abril con talleres de lectura.","notice",None,None,None),
    (1500,"Este mes reservamos los sábados para realizar las prácticas en la biblioteca.","notice",None,None,None),
    (2100,"The committee approved the privacy checklist for the internal review.","decision",None,None,None),
    (2700,"El presupuesto operativo asciende a 4,200 pesos.","topic",None,None,"4,200 pesos"),
    (3250,"Who will order replacement supplies? No responsible person or deadline was assigned.","pending",None,None,None),
    (3750,"Inés Ramos se comprometió a enviar el inventario el viernes.","action","Inés Ramos","viernes",None),
    (4050,"Se aprobó un fondo de 800 pesos para el archivo norte.","decision",None,None,"800 pesos"),
    (4680,"The steering group proposed extending support hours.","proposal",None,None,None),
    (5250,"Reminder: the orientation room is the library.","notice",None,None,None),
    (5950,"The board approved the retention pilot with a cap of USD 2,400.","decision",None,None,"USD 2,400"),
    (6550,"Alex Park committed to documenting the handoff by Thursday.","action","Alex Park","Thursday",None),
    (7270,"Se anunció que el material de consulta está disponible en recepción.","notice",None,None,None),
    (7800,"David Lin promised to circulate the vendor checklist by Tuesday.","action","David Lin","Tuesday",None),
    (8100,"Se aprobó conservar el formato actual del registro de consultas.","decision",None,None,None),
]

def fixture():
    lines=[];expected=[];topic_rows=[]
    for i,section in enumerate(SECTIONS):
        # Different utterances in each section. No copied filler or padding.
        for j,text in enumerate(section['lines']):
            stamp=timestamp(i*900+45+j*120)
            lines.append((stamp,text))
            topic_rows.append({'stamp':stamp,'section':section['name'],'text':text})
    for second,text,category,owner,due,amount in EVENTS:
        stamp=timestamp(second)
        lines.append((stamp,text))
        expected.append((stamp,category,owner,due,amount,None))
    lines.sort()
    assert len({stamp for stamp,_ in lines})==len(lines)
    assert len({text for _,text in lines})==len(lines)
    return '\n'.join(f'[{stamp}] {text}' for stamp,text in lines)+'\n',expected,topic_rows

def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main(output):
    output.mkdir(parents=True,exist_ok=False)
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    transcript,checks,topics=fixture()
    blocks=list(source_blocks(transcript))
    (output/'transcript.txt').write_text(transcript,encoding='utf-8')
    save(output/'expected.json',{'structured':checks,'topics':topics})
    save(output/'environment.json',{'model':ollama.MODEL,'version':VERSION,'digest':DIGEST,
        'scope':'independent varied synthetic text; 2h15 timestamp span, not 2h15 of recorded speech',
        'rows':len(transcript.splitlines()),'characters':len(transcript),'words':len(transcript.split()),'blocks':len(blocks)})
    trace=output/'trace.jsonl'
    def emit(event):
        with trace.open('a',encoding='utf-8') as f:
            f.write(json.dumps(event,ensure_ascii=False)+'\n')
    cache=output/'extraction-cache';cache.mkdir()
    def read_block(key):
        p=cache/(key+'.json')
        return p.read_text(encoding='utf-8') if p.exists() else None
    def write_block(key,raw):
        (cache/(key+'.json')).write_text(raw,encoding='utf-8')
    # Reference is independent of the model: fixed required source topics and outcomes.
    evidence={};started=time.monotonic()
    result={'passed':False}
    try:
        report=summarize.summarize_local(transcript,'both','es',ollama.MODEL,
            evidence_sink=evidence.update,qa_trace=emit,read_block=read_block,write_block=write_block,
            narrative_strategy='localized_editorial',progress=lambda msg:print(msg,flush=True))
        (output/'minutes.md').write_text(report,encoding='utf-8')
        save(output/'evidence.json',evidence)
        facts=score(transcript,checks,evidence['items'])
        cited={ref['timestamp'] for theme in evidence['editorial_themes'] for ref in theme['sources']}
        section_results=[{'section':section['name'],'cited_rows':sum(t['stamp'] in cited for t in topics if t['section']==section['name']),
            'total_rows':len(section['lines'])} for section in SECTIONS]
        criteria={'structured_facts':facts['passed'],
          'every_thematic_section_represented':all(x['cited_rows']>0 for x in section_results),
          'no_detected_structural_gaps':not evidence['coverage_gaps'],
          'no_detected_editorial_gaps':not evidence['editorial_gaps'],
          'no_unresolved_empty_blocks':not evidence['repetition_coverage']['unresolved_empty_block_ids'],
          'no_unresolved_review_records':not evidence['repetition_coverage']['unresolved_review_indices'],
          'no_failed_localization':all(not x['rejected'] for x in evidence['localization']),
          'overview_and_detail':'## Resumen ejecutivo' in report and '## Temas tratados' in report,
          'no_visible_timecodes_or_tables':not re.search(r'\[\d{2}:\d{2}:\d{2}\]',report) and not any(l.startswith('|') for l in report.splitlines())}
        result.update(facts=facts,sections=section_results,criteria=criteria,passed=all(criteria.values()),
                      quality='manual semantic comparison required; source-ID coverage alone is not semantic proof')
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result['seconds']=round(time.monotonic()-started,3)
        result['requests']=sum(json.loads(l).get('event')=='request' for l in trace.read_text(encoding='utf-8').splitlines()) if trace.exists() else 0
        save(output/'result.json',result)
        print(json.dumps({k:v for k,v in result.items() if k!='facts'},ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':
    raise SystemExit(main(Path(sys.argv[1])))
