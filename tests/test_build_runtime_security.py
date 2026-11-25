from pathlib import Path
from qa.check_build_runtime import blockers

ROOT=Path(__file__).resolve().parents[1]

def test_old_runtime_is_rejected():
    assert blockers((3,11,9),(3,0,13),(3,45,1),64)
    assert blockers((3,14,10),(3,0,13),(3,50,4),64)
    assert blockers((3,14,10),(3,5,9),(3,45,1),64)
    assert blockers((3,14,10),(3,5,9),(3,50,4),32)
    assert not blockers((3,14,10),(3,5,9),(3,50,4),64)

def test_ci_and_build_require_approved_runtime():
    workflow=(ROOT/'.github/workflows/windows-build.yml').read_text(encoding='utf-8')
    assert workflow.count("python-version: '3.14.10'")==2
    script=(ROOT/'scripts/compilar_windows.bat').read_text(encoding='utf-8')
    assert script.index('qa\\check_build_runtime.py')<script.index('-m PyInstaller')
