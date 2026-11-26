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
    assert "github.event_name == 'workflow_dispatch' && (inputs.package_for_qa || inputs.portable_for_qa)" in prep
    portable_marker = 'Compile Windows portable for QA'
    portable = workflow.split(portable_marker, 1)[1].split('      - name:', 1)[0]
    assert "github.event_name == 'workflow_dispatch' && inputs.portable_for_qa" in portable
    assert '--portable-only' in portable
    assert workflow.index(marker) < workflow.index(portable_marker)
    assert './scripts/prepare_lgpl_media.ps1' in prep
    assert workflow.index(marker) < workflow.index('Compile native Windows EXE')
    assert 'build/lgpl-wheel/lgpl-media-receipt.json' in workflow
    gate = json.loads((ROOT/'qa/release_gate.json').read_text(encoding='utf-8'))
    assert gate['release_allowed'] is False


def test_media_source_and_native_audit_are_pinned():
    setup = (ROOT/'scripts/prepare_lgpl_media.ps1').read_text(encoding='utf-8')
    assert 'autobuild-2026-11-24-12-41' in setup
    assert 'dbed3e64d68de76472bf2cd0b0f3250384fb96bac14b635a708e998f6e1d6996' in setup
    assert 'dd2ce779fa0b5f5889a6d9e00fbbbc39f58e247e52d31044272648fe16ff1dbf' in setup
    assert '--no-binary av' in setup
    assert 'delvewheel repair' in setup
    builder = (ROOT/'scripts/compilar_windows.bat').read_text(encoding='utf-8')
    assert '--add-binary "bin\\*.dll;bin"' in builder
    assert 'qa\\audit_package.py dist\\MeetingSplit' in builder
    audit = (ROOT/'qa/audit_package.py').read_text(encoding='utf-8')
    assert 'GPL codecs detected' in audit
    assert "('--enable-gpl','--enable-nonfree','--enable-libx264'" in audit
