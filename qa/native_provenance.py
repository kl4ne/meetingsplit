"""Match frozen native binaries to installed distributions and local build inputs.

No native binary is executed, no network access, no legal/security approval.
PE version resources are descriptive, not signed provenance. Exact byte
matches establish a local build-input match, not vendor authenticity.
"""
from __future__ import annotations
import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import sys
try:
    from .native_inventory import hash_file, inventory_package
except ImportError:
    from native_inventory import hash_file, inventory_package

GPU_VENDOR = re.compile(r'^(?:cudnn|cublas|cudart|cufft|curand|cusolver|cusparse|nvrtc|nvjitlink|nvcuda).*\.dll$',re.I)


def distribution_candidates(names, distributions=None):
    if distributions is None:
        distributions=metadata.distributions()
    for dist in distributions:
        for entry in dist.files or ():
            if entry.name.casefold() not in names or '..' in entry.parts:
                continue
            path=Path(dist.locate_file(entry))
            if not path.is_file(): continue
            yield path, {'kind':'python_distribution','name':dist.metadata.get('Name','unknown'),
                         'version':dist.version,'entry':entry.as_posix()}


def pe_version(path):
    """Best effort; a missing version is an explicit review gap."""
    try:
        import pefile
    except ImportError:
        return None
    pe=None
    try:
        pe=pefile.PE(str(path),fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        fixed=getattr(pe,'VS_FIXEDFILEINFO',None)
        if not fixed: return None
        info=fixed[0]
        version=lambda high,low: '.'.join(str(n) for n in (high>>16,high&65535,low>>16,low&65535))
        return {'file':version(info.FileVersionMS,info.FileVersionLS),
                'product':version(info.ProductVersionMS,info.ProductVersionLS)}
    except (OSError,ValueError,AttributeError,pefile.PEFormatError):
        return None
    finally:
        if pe is not None: pe.close()


def provenance(package, inventory, candidates):
    package=Path(package).resolve(strict=True)
    natives=[row for row in inventory['files'] if row['native']]
    wanted={(Path(row['path']).name.casefold(),row['sha256']) for row in natives}
    matches={}
    for path,origin in candidates:
        name=path.name.casefold()
        if not any(n==name for n,_ in wanted):
            continue
        key=(name,hash_file(path))
        if key in wanted: matches.setdefault(key,[]).append(origin)
    records=[]
    for row in natives:
        name=Path(row['path']).name.casefold()
        origins=matches.get((name,row['sha256']),[])
        records.append({'path':row['path'],'sha256':row['sha256'],'bytes':row['bytes'],
                        'pe_version':pe_version(package/row['path']),
                        'input_matches':origins,'optional_gpu_vendor_binary':bool(GPU_VENDOR.fullmatch(name))})
    gpu=[r['path'] for r in records if r['optional_gpu_vendor_binary']]
    unmatched=[r['path'] for r in records if not r['input_matches']]
    unversioned=[r['path'] for r in records if r['pe_version'] is None]
    notices=[r['path'] for r in inventory['files']
             if re.search(r'chromium|webengine',r['path'],re.I)
             and re.search(r'license|notice|credit|copyright',r['path'],re.I)]
    return {'schema':1,'scope':'actual frozen package; local build-input hash matches',
            'records':records,'unmatched_paths':unmatched,'unversioned_paths':unversioned,
            'gpu_vendor_paths':gpu,'candidate_webengine_notice_paths':notices,
            'release_allowed':False,'license_review_complete':False,'security_review_complete':False,
            'review_required':['Confirm exact upstream source and license for all native libraries',
                               'Review WebEngine/Chromium notices and corresponding sources',
                               'Confirm or remove all NVIDIA binaries from the base package',
                               'Map native component versions to current vulnerability advisories',
                               'Review unmatched and unversioned binaries; generated application may be unmatched']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path)
    parser.add_argument('--bin',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    inventory=inventory_package(args.package)
    names={Path(r['path']).name.casefold() for r in inventory['files'] if r['native']}
    candidates=list(distribution_candidates(names))
    # Match the interpreter and its DLL/extension inputs as well as wheels.
    for directory in (Path(sys.base_prefix),Path(sys.base_prefix)/'DLLs'):
        for file in directory.iterdir() if directory.is_dir() else ():
            if file.is_file() and file.name.casefold() in names:
                candidates.append((file,{'kind':'python_runtime_input','version':sys.version.split()[0],
                                        'entry':file.name}))
    for file in args.bin.glob('*'):
        if file.is_file() and file.name.casefold() in names:
            candidates.append((file,{'kind':'local_media_input','entry':file.name}))
    report=provenance(args.package,inventory,candidates)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Native review evidence: {len(report['records'])} binaries; {len(report['unmatched_paths'])} unmatched; {len(report['gpu_vendor_paths'])} GPU vendor binaries. Release blocked.")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
