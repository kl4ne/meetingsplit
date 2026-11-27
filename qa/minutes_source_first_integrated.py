"""Fresh bilingual end-to-end evaluation of optional source-first architecture.

No old responses or fixture-specific translations are used. Exact outcome
checks and unique descriptive utterances are fixed independently of inference.
This is a source-level QA case, not real speech or a dense long benchmark.
"""
import json,sys,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import ollama,summarize
from engine.minutes_evidence import source_blocks
from qa.minutes_editorial_ab import VERSION,DIGEST
from qa.minutes_long_acceptance import timestamp,score

DESCRIPTIVE=[
    'El equipo repasó la orientación para familias que visitan por primera vez el centro comunitario.',
    'The entrance instructions distinguish the ramp from the stairs and describe where the accessible restrooms are located.',
    'Se examinó la diferencia entre un mapa público del edificio y los datos privados de una persona.',
    'The volunteer handbook explains how to refer a question to reception without disclosing private contact details.',
    'Se habló de preparar ejemplos de atención respetuosa para personas que no conocen los servicios disponibles.',
    'The participants discussed how a translated sign differs from an individual conversation with a visitor.',
    'Se explicó el uso de etiquetas para distinguir los materiales prestados de los materiales disponibles.',
    'The inventory discussion covered damaged containers, intact contents, and equipment kept separately for inspection.',
    'Se revisó cómo identificar los materiales devueltos sin modificar su descripción original.',
    'The group discussed preserving a working copy of a form while retaining the original in the archive.',
    'Se explicó que una instrucción técnica y una recomendación pedagógica tienen funciones distintas.',
    'The participants described a practice exercise that uses an example before introducing a more difficult scenario.',
    'Se habló de revisar la claridad de las instrucciones dirigidas a personas que leen en otro idioma.',
    'The safety discussion distinguished a general exit route from individual emergency assistance.',
    'Se examinó la ubicación de las señales junto a las puertas y los pasos de circulación.',
    'The group discussed how an incident record differs from an inspection report, without assigning responsibility for the incident.',
    'Se habló de conservar las versiones anteriores del manual en una carpeta distinta de la versión vigente.',
    'The final discussion distinguished individual feedback from a collective decision and covered unresolved questions as examples.',
]
EVENTS=[
    (35,'Se aprobó mantener el formato actual del formulario de visitantes.','decision',None,None,None),
    (95,'Lucía Vega se comprometió a enviar el mapa actualizado el miércoles.','action','Lucía Vega','miércoles',None),
    (165,'The budget is USD 1,350.','topic',None,None,'USD 1,350'),
    (235,'The committee approved the training pilot with a cap of $750.','decision',None,None,'$750'),
    (275,'Proposal only: extend support hours to Saturday. Not approved.','proposal',None,None,None),
    (335,'Se anunció que la sala de orientación está disponible en la biblioteca.','notice',None,None,None),
    (395,'Marco Silva promised to circulate the inventory checklist by Thursday.','action','Marco Silva','Thursday',None),
    (455,'Who will order replacement labels? No responsible person or deadline was assigned.','pending',None,None,None),
]
def fixture():
    descriptive=[(i*30,s) for i,s in enumerate(DESCRIPTIVE)]
    rows=descriptive+[(t,s) for t,s,*_ in EVENTS]
    assert len({t for t,_ in rows})==len(rows)
    transcript='\n'.join(f'[{timestamp(t)}] {s}' for t,s in sorted(rows))+'\n'
    checks=[(timestamp(t),c,o,d,a,None) for t,_,c,o,d,a in EVENTS]
    return transcript,checks,{timestamp(t) for t,_ in descriptive}

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main(output):
    output.mkdir(parents=True,exist_ok=False)
    transcript,expected,stamps=fixture()
    (output/'transcript.txt').write_text(transcript,encoding='utf-8')
    save(output/'expected.json',{'structured':expected,'descriptive_stamps':sorted(stamps)})
    state=ollama.existing_status()
    assert state['version']==VERSION and state['model']['digest']==DIGEST and ollama.reusable_existing()
    started=time.monotonic();evidence={};result={'passed':False};calls=[]
    def emit(e):
        if e['event']=='request':calls.append(e['stage'])
        with (output/'trace.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(e,ensure_ascii=False)+'\n')
    cache=output/'extraction-cache';cache.mkdir()
    try:
        report=summarize.summarize_local(transcript,'both','both',ollama.MODEL,narrative_strategy='source_first',
            evidence_sink=evidence.update,qa_trace=emit,progress=lambda msg:print(msg,flush=True),
            write_block=lambda key,raw:(cache/(key+'.json')).write_text(raw,encoding='utf-8'))
        (output/'minutes.md').write_text(report,encoding='utf-8')
        save(output/'evidence.json',evidence)
        structured=score(transcript,expected,evidence['items'])
        langchecks=[]
        for lang in evidence['source_first']:
            units=lang['units'];groups=[g for w in lang['windows'] for g in w['groups']]
            found={u['source']['timestamp'] for u in units}
            langchecks.append({'language':lang['language'],'units':len(units),'groups':len(groups),
                'descriptive_rows_preserved':stamps<=found,
                'missing_stamps':sorted(stamps-found),
                'every_unit_once':sorted(i for g in groups for i in g['unit_ids'])==[u['id'] for u in units],
                'no_translation_rejects':not lang['translation_rejected'],
                'no_grouping_fallbacks':not lang['grouping_failures']})
        checks={'structured_facts':structured['passed'],
            'two_independent_languages':[d['language'] for d in langchecks]==['es','en'],
            'all_descriptive_rows':all(d['descriptive_rows_preserved'] and d['every_unit_once'] for d in langchecks),
            'no_descriptive_translation_rejects':all(d['no_translation_rejects'] for d in langchecks),
            'no_grouping_fallbacks':all(d['no_grouping_fallbacks'] for d in langchecks),
            'no_structured_translation_rejects':all(not d['rejected'] for d in evidence['localization']),
            'no_structural_gaps':not evidence['coverage_gaps'],
            'no_unresolved_review':not evidence['repetition_coverage']['unresolved_review_indices'],
            'two_sections':'# Minuta de reunión' in report and '# Meeting minutes' in report and '## Temas tratados' in report and '## Topics discussed' in report,
            'no_visible_timecodes_or_tables':not re.search(r'\[\d{2}:\d{2}:\d{2}\]',report) and not any(l.startswith('|') for l in report.splitlines())}
        result.update(checks=checks,structured=structured,languages=langchecks,passed=all(checks.values()))
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(seconds=round(time.monotonic()-started,3),requests=calls,rows=len(transcript.splitlines()),
            blocks=len(list(source_blocks(transcript))),scope='fresh bilingual source-first optional engine path; not frozen executable or dense long case',
            quality='manual bilingual semantic and editorial review required')
        save(output/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='structured'},ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1])))
