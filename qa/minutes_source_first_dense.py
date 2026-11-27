"""Fresh denser single-language acceptance. Not a full 16k-word real benchmark."""
import json,sys,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama,summarize
from engine.minutes_evidence import source_blocks,_SENTENCE_BREAK
from qa.minutes_editorial_ab import VERSION,DIGEST
from qa.minutes_long_acceptance import timestamp,score

DESCRIPTIVE=[
  {
    "name": "Recepción y accesibilidad",
    "text": "El equipo repasó la llegada de familias que visitan el edificio por primera vez. La bienvenida comienza con una explicación breve del lugar, no con una solicitud de datos personales. La conversación distinguió las preguntas sobre horarios y ubicación de las consultas que requieren hablar con una persona en un espacio privado. Se examinó cómo una señal visible facilita la orientación."
  },
  {
    "name": "Recepción y accesibilidad",
    "text": "Se describió el acceso desde el estacionamiento hasta la entrada principal, incluyendo la rampa y el pasillo que conduce al mostrador. Las indicaciones para una persona con movilidad reducida deben diferenciar la ruta accesible de las escaleras. El grupo examinó el ejemplo de una familia que solicita la ubicación de los baños accesibles sin necesidad de revelar información sobre su salud."
  },
  {
    "name": "Recepción y accesibilidad",
    "text": "The reception handbook separates building directions from confidential individual inquiries. A visitor asking for the location of a meeting room can receive a general map, whereas a personal question belongs in a private conversation. The discussion covered respectful listening before referring the person to another service. It also described how visible signs near the entrance reduce confusion."
  },
  {
    "name": "Recepción y accesibilidad",
    "text": "Se habló de preparar ejemplos de atención para personas que no conocen los servicios disponibles. La explicación distinguió un saludo cordial de una entrevista administrativa. Se examinó la utilidad de tener materiales impresos con información general en el mostrador y de indicar claramente qué datos se necesitan únicamente para un trámite específico, sin presentar este ejemplo como una decisión de la reunión."
  },
  {
    "name": "Recepción y accesibilidad",
    "text": "El grupo revisó la función de los puntos de orientación dentro del edificio. La conversación abordó la diferencia entre indicar un camino y acompañar físicamente a una persona que solicita ayuda. Se describió un escenario de formación donde un visitante encuentra una puerta cerrada y pregunta por otra ruta; el ejemplo no establece un nuevo procedimiento de seguridad."
  },
  {
    "name": "Recepción y accesibilidad",
    "text": "The participants reviewed an example of a translated sign and discussed why a brief sign cannot answer every question. A map identifies rooms and accessible routes, while a conversation allows someone to clarify the visitor's specific request. The guide describes keeping contact details out of publicly displayed directions and maintaining a respectful tone when explaining unfamiliar terminology."
  },
  {
    "name": "Biblioteca e inventario",
    "text": "Se examinó la distribución de los estantes de lectura y la diferencia entre materiales de consulta, ejemplares prestados y libros disponibles. La organización por público facilita encontrar recursos infantiles sin mezclar las publicaciones de referencia para adultos. Se describió cómo las etiquetas indican el contenido de una caja y su ubicación, sin atribuirle un valor monetario ni asignar responsabilidad por las existencias."
  },
  {
    "name": "Biblioteca e inventario",
    "text": "El equipo explicó cómo se registra un libro devuelto antes de colocarlo nuevamente en su estante. Se distinguió el desgaste normal de un daño que requiere examinar el ejemplar. Un embalaje deteriorado no implica necesariamente que el contenido esté dañado. Se revisaron ejemplos de materiales apartados para inspección, sin afirmar que se hayan descartado o comprado reemplazos."
  },
  {
    "name": "Biblioteca e inventario",
    "text": "The inventory discussion distinguished disposable supplies used during activities from reusable equipment. Participants described organizing containers by their contents rather than the name of the person who last used them. A working inventory label can include a clear description of the item and its storage location. The examples were instructional, not an allocation of new funds."
  },
  {
    "name": "Biblioteca e inventario",
    "text": "Se habló de mejorar la legibilidad de las etiquetas para que las personas identifiquen los materiales sin abrir cada caja. La conversación abordó el uso de nombres comunes y descripciones breves en lugar de abreviaturas desconocidas. Se examinó la diferencia entre una etiqueta temporal de revisión y la identificación habitual de un recurso que ya está disponible."
  },
  {
    "name": "Biblioteca e inventario",
    "text": "Se repasó una actividad de lectura en la que los participantes leen un pasaje corto y comentan su significado. Se distinguió la comprensión del texto de la velocidad de lectura. La conversación incluyó ejemplos de preguntas abiertas que permiten comprobar si se entendió una idea, así como la selección de materiales adecuados para diferentes edades y experiencias de lectura."
  },
  {
    "name": "Biblioteca e inventario",
    "text": "The group discussed a fictional example of a returned item whose label no longer matches its contents. The example illustrates why staff examine the contents before updating the inventory description. The discussion also separated the location of a reference book from its availability for lending, and distinguished items awaiting inspection from resources ready to use."
  },
  {
    "name": "Privacidad y archivo",
    "text": "La guía de privacidad distingue información destinada al público de datos de contacto individuales. Se explicó por qué un cartel de actividades generales no debe incluir el nombre de una persona que planteó una consulta privada. La conversación examinó cómo describir el contenido de una nota sin revelar detalles innecesarios y cómo conservar el documento original cuando se prepara una copia de trabajo."
  },
  {
    "name": "Privacidad y archivo",
    "text": "Se revisó la diferencia entre un registro interno y un anuncio público. Un registro puede contener información necesaria para comprender el contexto de una consulta, mientras que un anuncio explica una actividad a cualquier persona interesada. Se habló de utilizar ejemplos ficticios durante la formación, evitando que los materiales de enseñanza reproduzcan información personal de situaciones reales."
  },
  {
    "name": "Privacidad y archivo",
    "text": "The archive discussion covered original records and working copies. A working copy can be used to prepare a revision without altering the original. Participants discussed how descriptive file names and a short indication of the document's subject help locate a record without opening unrelated files. The discussion distinguished current reference materials from older versions retained for context."
  },
  {
    "name": "Privacidad y archivo",
    "text": "Se habló de organizar carpetas por contenido, separando borradores, documentos finales y versiones anteriores. Se examinó la conveniencia de indicar de forma clara cuál versión está vigente, sin eliminar automáticamente los antecedentes. La conversación abordó el valor de registrar el contexto de un documento sin alterar sus palabras y de mantener un nombre de archivo que pueda comprender otra persona."
  },
  {
    "name": "Privacidad y archivo",
    "text": "El equipo examinó la diferencia entre un informe de incidente y un comentario informal sobre una experiencia. Un informe debe distinguir lo observado de las interpretaciones posteriores; el ejemplo presentado no identificó a ninguna persona responsable. Se explicó cómo describir una dificultad general sin divulgar información privada y por qué los documentos destinados a formación deben conservar su contexto."
  },
  {
    "name": "Privacidad y archivo",
    "text": "The group discussed limiting sensitive information to the people who need it for the relevant process. A public summary can describe a general concern without including the contact details of the person involved. The conversation distinguished the purpose of retaining a record from the purpose of publishing information, and considered how earlier versions can explain changes to a document."
  },
  {
    "name": "Formación y comunicación",
    "text": "Se habló de preparar ejemplos que permitan distinguir preguntas frecuentes de solicitudes excepcionales. La conversación examinó la demostración de un procedimiento antes de que una persona lo practique por sí misma. Se explicó que una instrucción técnica y una recomendación pedagógica tienen funciones diferentes. El ejemplo no asignó una tarea a una persona ni estableció un plazo."
  },
  {
    "name": "Formación y comunicación",
    "text": "Se revisó la claridad de las instrucciones destinadas a quienes leen en un segundo idioma. La explicación abordó el uso de frases breves, vocabulario consistente y ejemplos que muestran cómo se aplica un procedimiento. Se examinó la diferencia entre comprender una instrucción y completar correctamente una actividad práctica, sin atribuir una evaluación personal a los participantes."
  },
  {
    "name": "Formación y comunicación",
    "text": "The training discussion examined a fictional learner who needs more time to understand the reference material. A demonstration can clarify the order of a procedure before the learner begins practicing. The participants discussed how feedback on an individual exercise differs from an assessment of someone's overall abilities. The example is descriptive and does not introduce a new performance requirement."
  },
  {
    "name": "Formación y comunicación",
    "text": "Se distinguieron los avisos generales de las comunicaciones dirigidas a una persona concreta. La conversación abordó cómo un mensaje breve puede indicar la ubicación de una actividad sin agregar antecedentes innecesarios. Se revisó un ejemplo de cambio de sala que conserva la hora anunciada y se explicó la diferencia entre una fecha confirmada y una fecha que todavía se discute."
  },
  {
    "name": "Formación y comunicación",
    "text": "El grupo examinó la coherencia terminológica de los mensajes en español e inglés. Se explicó que una traducción debe conservar la información sobre el lugar, el propósito y la fecha, incluso cuando cambia la estructura de una frase. Se habló de presentar información pública de manera clara, sin incorporar detalles privados que no ayudan a comprender el aviso."
  },
  {
    "name": "Formación y comunicación",
    "text": "The participants discussed how to separate a general announcement from an individual reminder. A change in location does not by itself imply a change in the scheduled time. The examples included a short notice identifying the library and an explanation of why consistent terminology helps visitors recognize the same activity in different languages. No additional event was announced in those examples."
  },
  {
    "name": "Seguridad y seguimiento",
    "text": "Se revisaron las salidas del edificio, los pasos de circulación y la ubicación de señales junto a las puertas. La explicación distinguió la orientación general de la asistencia individual ante una emergencia. Se examinó un ejemplo en el que una persona pregunta por una salida sin solicitar asistencia; el caso sirve para enseñar la diferencia entre información general y ayuda individual."
  },
  {
    "name": "Seguridad y seguimiento",
    "text": "El equipo explicó la importancia de mantener visibles las señales y diferenciar una zona de circulación de una zona destinada a guardar materiales. Se describió un ejemplo de un pasillo con cajas que dificultan el paso. La conversación no identificó un incidente real ni una persona responsable, sino que examinó el propósito de las indicaciones de seguridad."
  },
  {
    "name": "Seguridad y seguimiento",
    "text": "The safety discussion distinguished a routine inspection of equipment from an incident report. An inspection describes the condition of the equipment at the time it is examined; an incident report describes what occurred. The participants discussed recording an equipment fault without prematurely attributing responsibility and distinguishing observed conditions from explanations that still need to be checked."
  },
  {
    "name": "Seguridad y seguimiento",
    "text": "Se habló de revisar la claridad de las observaciones recibidas durante las actividades. Se distinguió la retroalimentación que describe una experiencia de la que solicita un cambio. La explicación abordó cómo agrupar preguntas similares sin presentar opiniones individuales como decisiones del equipo. Se examinó el valor de conservar las preguntas aún no aclaradas en el registro correspondiente."
  },
  {
    "name": "Seguridad y seguimiento",
    "text": "The group reviewed a fictional follow-up conversation in which the original question remained unresolved. The example showed how a later conversation can clarify the issue without assuming a decision has already been made. The discussion distinguished feedback on a service from a proposal to change the service and considered the usefulness of preserving the original context of a question."
  },
  {
    "name": "Seguridad y seguimiento",
    "text": "Al final se habló de preparar ejemplos prácticos de orientación para la próxima formación. Se examinó la diferencia entre asuntos resueltos, preguntas que todavía necesitan aclaración y comentarios que simplemente describen una experiencia. La conversación distinguió un acuerdo explícito de una explicación de procedimiento y recordó la utilidad de conservar la redacción original de los compromisos cuando se elabora una minuta."
  }
]
EVENTS=[
  [
    40,
    "Se aprobó mantener el horario actual de recepción.",
    "decision",
    None,
    None,
    None
  ],
  [
    100,
    "Elena Cruz se comprometió a entregar el plano actualizado el martes.",
    "action",
    "Elena Cruz",
    "martes",
    None
  ],
  [
    300,
    "The budget is USD 3,650.",
    "topic",
    None,
    None,
    "USD 3,650"
  ],
  [
    400,
    "The committee approved the reading pilot with a cap of $900.",
    "decision",
    None,
    None,
    "$900"
  ],
  [
    580,
    "Proposal only: extend support hours to Saturday. Not approved.",
    "proposal",
    None,
    None,
    None
  ],
  [
    700,
    "Se anunció que la sala de orientación está disponible en la biblioteca.",
    "notice",
    None,
    None,
    None
  ],
  [
    850,
    "Rafael Mora promised to circulate the archive checklist by Friday.",
    "action",
    "Rafael Mora",
    "Friday",
    None
  ],
  [
    1000,
    "Se aprobó un fondo de 650 pesos para los materiales de formación.",
    "decision",
    None,
    None,
    "650 pesos"
  ],
  [
    1160,
    "Ya empezaremos el mes de abril con talleres de lectura.",
    "notice",
    None,
    None,
    None
  ],
  [
    1325,
    "Who will order replacement signs? No responsible person or deadline was assigned.",
    "pending",
    None,
    None,
    None
  ]
]

def fixture():
    entries=[(i*55,x['text']) for i,x in enumerate(DESCRIPTIVE)]
    entries.extend((t,s) for t,s,*_ in EVENTS)
    assert len({t for t,_ in entries})==len(entries)
    transcript='\n'.join(f'[{timestamp(t)}] {s}' for t,s in sorted(entries))+'\n'
    checks=[(timestamp(t),c,o,d,a,None) for t,_,c,o,d,a in EVENTS]
    topics=[{'stamp':timestamp(i*55),'section':x['name']} for i,x in enumerate(DESCRIPTIVE)]
    return transcript,checks,topics

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main(output):
    output.mkdir(parents=True,exist_ok=False)
    transcript,expected,topics=fixture()
    blocks=list(source_blocks(transcript));rows=[r for b in blocks for r in b]
    (output/'transcript.txt').write_text(transcript,encoding='utf-8')
    save(output/'expected.json',{'structured':expected,'topics':topics})
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    started=time.monotonic();evidence={};result={'passed':False};calls=[]
    def emit(e):
        if e['event']=='request':calls.append(e['stage'])
        with (output/'trace.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(e,ensure_ascii=False)+'\n')
    cache=output/'extraction-cache';cache.mkdir()
    try:
        report=summarize.summarize_local(transcript,'both','es',ollama.MODEL,narrative_strategy='source_first',
            evidence_sink=evidence.update,qa_trace=emit,progress=lambda msg:print(msg,flush=True),
            write_block=lambda key,raw:(cache/(key+'.json')).write_text(raw,encoding='utf-8'))
        (output/'minutes.md').write_text(report,encoding='utf-8')
        save(output/'evidence.json',evidence)
        facts=score(transcript,expected,evidence['items'])
        lang=evidence['source_first'][0]
        units=lang['units'];account=lang['source_accounting']
        expected_sentences=[(r['id'],q.strip()) for r in rows for q in _SENTENCE_BREAK.split(r['text']) if q.strip()]
        actual=[(a['source']['source_id'],a['source']['quote']) for a in account]
        by_id={u['id']:u for u in units}
        def accounted(a):
            ref=a['source'];status=a['status']
            if status=='detail':return by_id[a['unit_id']]['source']==ref
            if status=='exact_repeat':return by_id[a['unit_id']]['source']['quote']==ref['quote'] and by_id[a['unit_id']]['source']['source_id']<ref['source_id']
            if status=='structured':
                return bool(a['item_indices']) and all(any(s['source_id']==ref['source_id'] and ref['quote'] in s['quote'] for s in evidence['items'][i]['sources']) for i in a['item_indices'])
            return False
        checks={
            'structured_facts':facts['passed'],
            'all_source_sentences_accounted':actual==expected_sentences and all(accounted(a) for a in account),
            'all_descriptive_rows_preserved':{t['stamp'] for t in topics}<={u['source']['timestamp'] for u in units},
            'every_detail_unit_once':sorted(i for w in lang['windows'] for g in w['groups'] for i in g['unit_ids'])==[u['id'] for u in units],
            'no_extraction_failures':not evidence['source_first_extraction_failures'],
            'no_translation_rejects':not lang['translation_rejected'] and all(not d['rejected'] for d in evidence['localization']),
            'no_grouping_fallbacks':not lang['grouping_failures'],
            'no_structural_gaps':not evidence['coverage_gaps'],
            'no_unresolved_review':not evidence['repetition_coverage']['unresolved_review_indices'],
            'summary_and_detail':'## Resumen ejecutivo' in report and '## Temas tratados' in report,
            'no_visible_timecodes_or_tables':not re.search(r'\[\d{2}:\d{2}:\d{2}\]',report) and not any(l.startswith('|') for l in report.splitlines())}
        result.update(checks=checks,facts=facts,passed=all(checks.values()),units=len(units),sentences=len(account),
            windows=len(lang['windows']),group_count=sum(len(w['groups']) for w in lang['windows']))
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(seconds=round(time.monotonic()-started,3),requests=calls,rows=len(rows),words=len(transcript.split()),
            blocks=len(blocks),scope='fresh denser bilingual source, Spanish output, CPU; not historical full-length or frozen app',
            quality='manual semantic comparison required; exact sentence accounting is not semantic proof')
        save(output/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='facts'},ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1])))
