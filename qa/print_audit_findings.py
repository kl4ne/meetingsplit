"""Print package/version and advisory IDs from a CycloneDX report, without weakening the audit."""
import json
import sys
from pathlib import Path


def findings(document):
    components={c['bom-ref']:c for c in document.get('components',[]) if 'bom-ref' in c}
    for vuln in document.get('vulnerabilities',[]):
        for affected in vuln.get('affects',[]):
            component=components.get(affected.get('ref'),{})
            yield (component.get('name','unknown'),component.get('version','unknown'),
                   vuln.get('id','unknown'))


def main(path):
    rows=sorted(set(findings(json.loads(Path(path).read_text(encoding='utf-8')))))
    for package,version,advisory in rows:
        print(f'{package} {version}: {advisory}')
    print(f'{len(rows)} distinct package/version/advisory rows')


if __name__=='__main__':
    main(sys.argv[1])
