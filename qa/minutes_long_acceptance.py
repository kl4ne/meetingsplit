"""Windows/Ollama acceptance using a reproducible bilingual synthetic transcript."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.minutes_evidence import source_blocks
from engine import ollama, summarize

CONTEXT = (
    "The discussion continued with background on file naming, the archive layout, and examples in the reference guide.",
    "Entre los asistentes se comentó la diferencia entre el material de consulta y los ejemplos del manual interno.",
    "Participants described how the reference folder is organized and which vocabulary appears in the training notes.",
    "La conversación repasó el glosario y la estructura habitual de los anexos y las carpetas compartidas.",
    "The notes covered the history of the template, the terminology in the appendix and the existing records.",
    "Se describieron los materiales existentes y las diferencias entre las plantillas descriptivas y los formularios.",
)
EVENTS = {
    180: ("The committee approved the access pilot with a cap of $12,500.", "decision", None, None, "$12,500"),
    220: ("Ana Ruiz will send the access draft by Friday.", "action", "Ana Ruiz", "Friday", None),
    270: ("The steering group proposed extending support hours.", "proposal", None, None, None),
    3600: ("The board approved the privacy checklist for the internal review.", "decision", None, None, None),
    4050: ("Se aprobó un fondo de 800 pesos para el archivo norte.", "decision", None, None, "800 pesos"),
    4080: ("Inés Ramos se comprometió a enviar el inventario el viernes.", "action", "Inés Ramos", "viernes", None),
    7950: ("The board approved the retention pilot with a cap of USD 2,400.", "decision", None, None, "USD 2,400"),
    7980: ("Alex Park committed to documenting the handoff by Thursday.", "action", "Alex Park", "Thursday", None),
    8010: ("El presupuesto operativo asciende a 4,200 pesos.", "topic", None, None, "4,200 pesos"),
}
CROSSINGS = (
    (4250, "El comité propuso abrir una sala de formación.", "Se aprobó esta propuesta.", "decision", None, None),
    (4330, "David Lin promised to circulate the vendor checklist.", "The deadline for this task is Tuesday.", "action", "David Lin", "Tuesday"),
)


def timestamp(seconds):
    return f"{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d}"


def fixture():
    crossing={entry[0]:entry[1:] for entry in CROSSINGS}
    excluded={second+offset for second in crossing for offset in range(-20,4)}
    filler={second:CONTEXT[index%len(CONTEXT)] for index,second in enumerate(range(0,8101,30))
            if second not in excluded}
    lines=[]
    checks=[]
    for second in sorted(filler.keys() | EVENTS.keys() | crossing.keys()):
        if second in crossing:
            first,second_line,category,owner,due=crossing[second]
            # Place the first utterance in the remaining space, so the next one
            # falls just over the production source window without separating time.
            for size in range(1,4301):
                padding=(CONTEXT[0]+' ')*40
                candidate=lines+[f"[{timestamp(second-1)}] {padding[:size].rstrip()}",
                                 f"[{timestamp(second)}] {first}",f"[{timestamp(second+2)}] {second_line}"]
                blocks=list(source_blocks('\n'.join(candidate)))
                if len(blocks)>1 and blocks[-2][-1]['timestamp']==timestamp(second) and blocks[-1][0]['timestamp']==timestamp(second+2):
                    lines=candidate
                    break
            else:
                raise AssertionError("Could not position a window crossing")
            checks.append((timestamp(second),category,owner,due,None,timestamp(second+2)))
        elif second in EVENTS:
            line,category,owner,due,amount=EVENTS[second]
            lines.append(f"[{timestamp(second)}] {line}")
            checks.append((timestamp(second),category,owner,due,amount,None))
        else:
            lines.append(f"[{timestamp(second)}] {filler[second]}")
    return '\n'.join(lines)+'\n',checks


def score(transcript, checks, items):
    source={row['id']:row for block in source_blocks(transcript) for row in block}
    expected={row[0]:row[1] for row in checks}
    result=[]
    for stamp,category,owner,due,amount,second in checks:
        hits=[item for item in items if item['category']==category and any(ref['timestamp']==stamp for ref in item['sources'])]
        passed=len(hits)==1
        if passed:
            hit=hits[0]
            passed=(not owner or owner==hit['owner']) and (not due or due in (hit['due'] or ''))
            passed=passed and (not amount or any(amount in ref['quote'] for ref in hit['sources']))
            passed=passed and (not second or any(second==ref['timestamp'] for ref in hit['sources']))
        result.append({'stamp':stamp,'category':category,'matches':len(hits),'passed':passed})
    unexpected=[item for item in items if item['category'] in ('decision','action','proposal')
                and not any(expected.get(ref['timestamp'])==item['category'] for ref in item['sources'])]
    ungrounded=[ref for item in items for ref in item['sources']
                if ref['source_id'] not in source or ref['quote'] not in source[ref['source_id']]['text']
                or ref['timestamp']!=source[ref['source_id']]['timestamp']]
    return {'checks':result,'unexpected':unexpected,'ungrounded':ungrounded,
            'passed':all(c['passed'] for c in result) and not unexpected and not ungrounded}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    assert ollama.reusable_existing(), 'Audited model not available through the normal server'
    state=ollama.existing_status()
    assert state['version']=='0.40.18'
    assert state['model']['digest']=='359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7'
    transcript,checks=fixture()
    (args.output/'transcript.txt').write_text(transcript,encoding='utf-8')
    started=time.monotonic()
    evidence={}
    report=summarize.summarize_local(transcript,'both','both',ollama.MODEL,evidence_sink=evidence.update,
                                    progress=lambda message:print(message,flush=True))
    (args.output/'minutes.md').write_text(report,encoding='utf-8')
    (args.output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    result=score(transcript,checks,evidence['items'])
    result.update(seconds=round(time.monotonic()-started,2), rows=len(transcript.splitlines()),
                  characters=len(transcript), blocks=evidence['source_blocks'], coverage_gaps=evidence['coverage_gaps'])
    (args.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['passed'] else 2


if __name__=='__main__':
    raise SystemExit(main())

