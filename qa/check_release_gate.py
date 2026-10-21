"""Explicit fail-closed gate for any future release build, independent of CI success."""
import json
from pathlib import Path


def main():
    gate=json.loads((Path(__file__).parent/'release_gate.json').read_text(encoding='utf-8'))
    missing=[key for key,ok in gate['required'].items() if ok is not True]
    if gate.get('release_allowed') is not True or missing:
        print('RELEASE BLOCKED: '+', '.join(missing))
        return 2
    return 0


if __name__=='__main__': raise SystemExit(main())
