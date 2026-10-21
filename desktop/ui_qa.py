"""Headless frozen WebEngine render test; no settings, dialogs or meeting data."""
import json
from pathlib import Path
import sys
from PySide6.QtCore import QTimer,QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView


def main(output_path):
    app=QApplication.instance() or QApplication([])
    view=QWebEngineView()
    result={'ok':False,'test':'hidden WebEngine rendering of existing five-screen HTML'}
    timer=QTimer();timer.setSingleShot(True);timer.timeout.connect(app.quit);timer.start(30000)
    def done(state):
        if not state:
            result['error']='HTML load failed';app.quit();return
        def inspect(data):
            data=json.loads(data) if isinstance(data,str) and data else {}
            result.update(data)
            result['ok']=bool(data.get('screens')==5 and data.get('active')==1 and data.get('language')=='en')
            app.quit()
        view.page().runJavaScript('JSON.stringify({screens:document.querySelectorAll(".screen").length,active:document.querySelectorAll(".active-screen").length,language:document.documentElement.lang})',inspect)
    view.loadFinished.connect(done)
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
    # WebEngine does not start a renderer for an unexposed view on all platforms.
    # Callers run this internal check with QT_QPA_PLATFORM=offscreen.
    view.resize(1366,768);view.show()
    view.load(QUrl.fromLocalFile(str(root/'ui'/'index.html')))
    app.exec()
    view.close();view.deleteLater()
    Path(output_path).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return 0 if result['ok'] else 2
