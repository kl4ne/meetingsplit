"""Portable Windows packaging contracts tested even when a Windows runner isn't available."""
from pathlib import Path
import json
import subprocess
import sys
from desktop.self_check import run_checks

ROOT=Path(__file__).resolve().parents[1]

def test_self_check_never_requires_online_services():
    report,code=run_checks()
    assert report['offline'] is True
    assert report['version']=='0.8.4'
    assert {'qt_webengine','ffmpeg','ffprobe','whisper','cuda'} <= set(report['checks'])
    assert all(isinstance(row['ok'],bool) for row in report['checks'].values())
    assert all(not row['required'] for key,row in report['checks'].items() if key in ('cuda','platform'))
    assert code in (0,2)

def test_self_check_can_export_diagnostic_without_touching_audio(tmp_path):
    dest=tmp_path/'ready.json'
    outcome=subprocess.run([sys.executable,str(ROOT/'run.py'),'--self-check',str(dest)],
                           cwd=str(ROOT),capture_output=True,text=True,timeout=25)
    assert outcome.returncode in (0,2)
    data=json.loads(dest.read_text(encoding='utf-8'))
    assert data['product']=='MeetingSplit' and data['offline']
    assert set(data['checks'])>= {'qt_webengine','ffmpeg','ffprobe','whisper','cuda'}

def test_build_script_has_required_release_gates_and_version():
    build=(ROOT/'scripts/compilar_windows.bat').read_text(encoding='utf-8')
    setup=(ROOT/'scripts/MeetingSplit.iss').read_text(encoding='utf-8')
    assert 'set "RELEASE=0.8.4"' in build
    assert 'start /wait "" "dist\\MeetingSplit\\MeetingSplit.exe" --self-check' in build
    assert 'QtWebEngineWidgets' in build
    assert '--add-binary "bin\\ffmpeg.exe;bin"' in build
    assert 'if not "%PROBE_EXIT%"=="0"' in build
    assert 'MeetingSplit_Setup_v0.8.4' in setup
    assert 'AppVersion={#MyAppVersion}' in setup
    assert (ROOT/'assets/meetingsplit.ico').is_file()
    assert (ROOT/'assets/meetingsplit.ico').stat().st_size > 1000
