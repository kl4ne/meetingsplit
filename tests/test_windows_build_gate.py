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
    assert report['version']=='0.8.11'
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
    resource=(ROOT/'scripts/windows_version.txt').read_text(encoding='utf-8')
    assert 'set "RELEASE=0.8.11"' in build
    assert 'filevers=(0, 8, 11, 0)' in resource and 'prodvers=(0, 8, 11, 0)' in resource
    assert "StringStruct('ProductVersion', '0.8.11')" in resource
    assert "-ArgumentList @('--self-check'" in build
    assert 'WaitForExit(60000)' in build
    assert 'QtWebEngineWidgets' in build
    assert '--add-binary "bin\\ffmpeg.exe;bin"' in build
    assert 'if not "%PROBE_EXIT%"=="0"' in build
    assert '#define MyAppVersion "0.8.11"' in setup
    assert 'OutputBaseFilename=MeetingSplit_Setup_v{#MyAppVersion}' in setup
    assert 'AppVersion={#MyAppVersion}' in setup
    assert (ROOT/'assets/meetingsplit.ico').is_file()
    assert (ROOT/'assets/meetingsplit.ico').stat().st_size > 1000


def test_portable_only_build_skips_installer_and_keeps_candidate_filename():
    build=(ROOT/'scripts/compilar_windows.bat').read_text(encoding='utf-8')
    bypass='if /I "%~1"=="--portable-only" goto portable_complete'
    assert build.index('Compress-Archive') < build.index(bypass) < build.index('ISCC.exe')
    assert build.index('ISCC.exe') < build.index(':portable_complete')
    assert '%PORTABLE_BASENAME%-candidate' in build


def test_ui_immediate_feedback_and_live_elapsed_visible():
    app=(ROOT/'ui/app.js').read_text(encoding='utf-8')
    html=(ROOT/'ui/index.html').read_text(encoding='utf-8')
    css=(ROOT/'ui/styles.css').read_text(encoding='utf-8')
    assert 'jobStarted=Date.now()' in app
    assert 'button.disabled=working' in app
    assert 'setInterval(updateJobElapsed,1000)' in app
    assert 'id="job-elapsed"' in html
    assert 'processing-spinner' in app and 'processing-spinner' in css
