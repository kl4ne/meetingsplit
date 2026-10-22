"""Check that exact upstream third-party notice copies remain byte-hash pinned.

The hash confirms the Git repository copy matches its recorded receipt;
it does NOT independently certify third-party source licensing or legal review.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'third-party-licenses'


def test_pinned_vendor_notices_match_source_receipts():
    records = json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))
    assert isinstance(records, list) and len(records) >= 7
    names = set()
    for record in records:
        name = record['file']
        assert Path(name).name == name and name not in names
        names.add(name)
        assert record['source'].startswith('https://raw.githubusercontent.com/')
        text = (ROOT/name).read_bytes()
        assert text, f'Empty notice: {name}'
        assert hashlib.sha256(text).hexdigest() == record['sha256'], f'Notice changed: {name}'
    assert 'Chromium-140.0.7339.264-BSD-3-Clause.txt' in names
    assert 'Tokenizers-0.23.3-Apache-2.0.txt' in names
    assert 'Cython-3.3.0-Apache-2.0.txt' in names
    assert 'Cython-3.3.0-Pyrex-COPYING.txt' in names
