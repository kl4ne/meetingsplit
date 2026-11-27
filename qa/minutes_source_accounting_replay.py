"""Offline citation accounting over archived synthetic Actions ZIPs.

No Ollama, downloads, production settings or model responses changed.
Usage: python qa/minutes_source_accounting_replay.py <varied-initial.zip>
       <varied-targeted.zip> <dense-original.zip> <dense-reclassified.zip>
"""
import collections
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.minutes_evidence import source_blocks
from engine.minutes_source_accounting import audit_source_passages


def read(path,name,as_json=True):
    with zipfile.ZipFile(path) as archive:
        value=archive.read(name).decode('utf-8')
    return json.loads(value) if as_json else value


def replay(varied_initial,varied_targeted,dense_original,dense_reclassified):
    varied=read(varied_initial,'transcript.txt',False)
    dense=read(dense_original,'transcript.txt',False)
    dense_evidence=read(dense_original,'evidence.json')
    cases=[
        ('varied_initial',varied,read(varied_initial,'evidence.json')),
        ('varied_targeted',varied,read(varied_targeted,'varied-targeted/evidence.json')),
        ('dense_original',dense,dense_evidence),
        ('dense_reclassified',dense,{**dense_evidence,'items':read(dense_reclassified,'items.json')}),
    ]
    results={}
    for name,transcript,evidence in cases:
        blocks=list(source_blocks(transcript))
        audit=audit_source_passages(blocks,evidence['items'],evidence['editorial_themes'],
                                    evidence['editorial_gaps'])
        counts=collections.Counter(entry['status'] for entry in audit['entries'])
        results[name]={'rows':sum(map(len,blocks)),'counts':dict(counts),
                       'uncited_passages':audit['uncited_passages']}
    return results


if __name__=='__main__':
    if len(sys.argv)!=5:
        raise SystemExit(__doc__)
    print(json.dumps(replay(*sys.argv[1:]),ensure_ascii=False,indent=2))
