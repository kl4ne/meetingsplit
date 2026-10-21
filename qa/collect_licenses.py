"""Collect distribution metadata and original notices into the development package.

This inventory aids review; it does not certify GPL/LGPL redistribution compliance.
"""
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    target=ROOT/'build'/'legal';target.mkdir(parents=True,exist_ok=True)
    inventory=[]
    for dist in sorted(metadata.distributions(),key=lambda d:d.metadata.get('Name','').lower()):
        name=dist.metadata.get('Name','unknown')
        row={'name':name,'version':dist.version,'license':dist.metadata.get('License-Expression') or dist.metadata.get('License'),
             'home':dist.metadata.get('Home-page'),'notices':[]}
        for entry in dist.files or []:
            lower=str(entry).lower()
            if any(word in lower for word in ('license','copying','copyright','notice')) and entry.suffix.lower() in ('','.txt','.md','.rst'):
                source=Path(dist.locate_file(entry))
                if not source.is_file() or source.stat().st_size>2*1024**2: continue
                # Preserve path components; reject parent escapes in wheel metadata.
                if '..' in entry.parts: continue
                dest=target/name/Path(str(entry))
                dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
                row['notices'].append(str(dest.relative_to(target)))
        inventory.append(row)
    for app in ('ffmpeg','ffprobe'):
        binary=ROOT/'bin'/(app+'.exe')
        if binary.is_file():
            result=subprocess.run([str(binary),'-version'],capture_output=True,text=True,timeout=15)
            (target/(app+'-build.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
    (target/'DEPENDENCY_INVENTORY.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    shutil.copyfile(ROOT/'docs'/'THIRD_PARTY_REVIEW.md',target/'THIRD_PARTY_REVIEW.md')
    # Preserve exact media provenance and verified archive hashes alongside
    # the distributed binaries. A receipt is evidence, not license approval.
    media_receipt=ROOT/'build'/'lgpl-wheel'/'lgpl-media-receipt.json'
    if media_receipt.is_file():
        shutil.copyfile(media_receipt,target/'LGPL_MEDIA_BUILD_RECEIPT.json')



if __name__=='__main__': main()
