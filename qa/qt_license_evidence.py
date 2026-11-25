"""Collect runtime version and possible Chromium credits from the exact wheel.
The page, even if present, is not proof of complete corresponding source.
"""
import hashlib,json,os,sys
from pathlib import Path
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='kl4ne/meetingsplit':
    raise SystemExit('CI only')
from PySide6 import __file__ as binding_file
from PySide6.QtCore import QUrl,QTimer,qVersion
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEnginePage,qWebEngineVersion,qWebEngineChromiumVersion,qWebEngineChromiumSecurityPatchVersion
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
expected='54488cfc8fea4057377302cec5a1fb1100fb4bc4231cd7e60f43e4fcff28e89e'
path=Path(binding_file).parent/'Qt6WebEngineCore.dll'
h=hashlib.sha256()
with path.open('rb') as stream:
    for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
result={'qt':qVersion(),'webengine':qWebEngineVersion(),'chromium':qWebEngineChromiumVersion(),
        'security_patch':qWebEngineChromiumSecurityPatchVersion(),'dll_sha256':h.hexdigest(),
        'matches_old_package':h.hexdigest()==expected,'credits_captured':False,
        'legal_review_complete':False,'release_allowed':False}
def save(): (out/'qt-evidence.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
save()
app=QApplication([])
page=QWebEnginePage()
def captured(html):
    result['credits_bytes']=len(html.encode('utf-8'))
    # Blank/error pages are not evidence.
    if len(html)>10000 and 'license' in html.lower():
        (out/'chromium-credits.html').write_text(html,encoding='utf-8')
        result['credits_captured']=True
    save();app.quit()
def loaded(ok):
    result['credits_load_ok']=bool(ok)
    if ok:page.toHtml(captured)
    else:save();app.quit()
def expired():
    result['credits_timeout']=True;save();app.quit()
page.loadFinished.connect(loaded)
QTimer.singleShot(45000,expired)
page.load(QUrl('chrome://credits'))
app.exec()
save()
