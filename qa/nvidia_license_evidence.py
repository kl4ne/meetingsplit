"""Compare exact vendor archive member with the historical QA package.
No SDK execution, no binary distribution, no assertion of legal clearance.
"""
import hashlib,json,os,sys,zipfile
from pathlib import Path
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='kl4ne/meetingsplit':
    raise SystemExit('CI only')
root=Path(sys.argv[1])
archive=root/'cudnn.zip'
out=root/'evidence';out.mkdir(exist_ok=True)
expected='3083b5bf20b0b2b29305de088e0b2cdbb78b5190655a27e8a7c596e47042eedf'
candidate='c07cc47f2fa4a566593c7af4aa7e57edf09a985a0fddd14cb8d6f456e252af05'
def digest(stream):
    h=hashlib.sha256()
    for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
report={'vendor_version':'9.1.0.70','archive_sha256_expected':expected,
        'archive_size_expected':669629858,'old_package_dll_sha256':candidate,
        'source_manifest':'https://developer.download.nvidia.com/compute/cudnn/redist/redistrib_9.1.0.json',
        'license_url':'https://docs.nvidia.com/deeplearning/cudnn/backend/v9.1.0/reference/eula.html',
        'release_allowed':False,'legal_review_complete':False}
try:
    with archive.open('rb') as f:report['archive_sha256']=digest(f)
    report['archive_size']=archive.stat().st_size
    if report['archive_sha256']!=expected or report['archive_size']!=669629858:raise ValueError('Vendor archive integrity failure')
    with zipfile.ZipFile(archive) as z:
        dlls=[i for i in z.infolist() if not i.is_dir() and i.filename.replace('\\','/').split('/')[-1].lower()=='cudnn64_9.dll']
        if len(dlls)!=1:raise ValueError('Unexpected vendor DLL inventory')
        with z.open(dlls[0]) as f:report['vendor_dll_sha256']=digest(f)
        report['matches_old_package']=report['vendor_dll_sha256']==candidate
        report['notice_files']=[]
        for i in z.infolist():
            name=i.filename.replace('\\','/').split('/')[-1]
            if i.is_dir() or i.file_size>2*1024*1024 or not name.lower().endswith(('.txt','.md')) or not any(w in name.lower() for w in ('license','notice','copyright','acknowledg')):
                continue
            payload=z.read(i);target=out/f"notice-{len(report['notice_files']):03}.txt"
            target.write_bytes(payload)
            report['notice_files'].append({'vendor_path':i.filename,'file':target.name,'sha256':hashlib.sha256(payload).hexdigest()})
except Exception as exc:
    report['error']=str(exc)[:700];raise
finally:
    (out/'nvidia-evidence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
