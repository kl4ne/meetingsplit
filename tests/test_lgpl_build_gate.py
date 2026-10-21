"""Prevent accidental GPL media reintroduction in main's QA packaging."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_packaging_requires_pinned_lgpl_media_and_remains_manual():
    workflow = (ROOT/'.github/workflows/windows-build.yml').read_text(encoding='utf-8')
    marker = 'Prepare verified LGPL FFmpeg and source-built PyAV (QA packaging only)'
    assert 'branches: [main]' in workflow
    assert 'qa/consolidated-20261021' not in workflow
    assert marker in workflow
    prep = workflow.split(marker, 1)[1].split('      - name:', 1)[0]
    assert "github.event_name == 'workflow_dispatch' && inputs.package_for_qa" in prep
    assert './scripts/prepare_lgpl_media.ps1' in prep
    assert workflow.index(marker) < workflow.index('Compile native Windows EXE')
    assert 'build/lgpl-wheel/lgpl-media-receipt.json' in workflow
    gate = json.loads((ROOT/'qa/release_gate.json').read_text(encoding='utf-8'))
    assert gate['release_allowed'] is False


def test_media_source_and_native_audit_are_pinned():
    setup = (ROOT/'scripts/prepare_lgpl_media.ps1').read_text(encoding='utf-8')
    assert 'autobuild-2026-10-20-13-08' in setup
    assert '453a30a5019676e805a85d4845e3aad31234dfed4ae0ea2b1d4e97254dc44b0a' in setup
    assert 'dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf' in setup
    assert '--no-binary av' in setup
    assert 'delvewheel repair' in setup
    builder = (ROOT/'scripts/compilar_windows.bat').read_text(encoding='utf-8')
    assert '--add-binary "bin\\*.dll;bin"' in builder
    assert 'qa\\audit_package.py dist\\MeetingSplit' in builder
    audit = (ROOT/'qa/audit_package.py').read_text(encoding='utf-8')
    assert 'GPL codecs detected' in audit
    assert "('--enable-gpl','--enable-nonfree','--enable-libx264'" in audit
