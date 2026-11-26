"""Headless frozen WebEngine render test; no settings, dialogs or meeting data."""
import json
from pathlib import Path
from desktop.version import VERSION
from desktop.main import MainWindow
from PySide6.QtCore import QSettings,QTimer
from PySide6.QtWidgets import QApplication


def main(output_path):
    app=QApplication.instance() or QApplication([])
    settings_path=str(Path(output_path).parent/'qa-settings')
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    for scope in (QSettings.Scope.UserScope,QSettings.Scope.SystemScope):
        QSettings.setPath(QSettings.Format.IniFormat,scope,settings_path)
    settings=QSettings('MeetingSplit','MeetingSplit')
    settings.setValue('storage/data_root',str(Path(output_path).resolve().parent))
    settings.sync()
    view=MainWindow()
    result={'ok':False,'test':'isolated MainWindow paint on open, maximize and restore'}
    timer=QTimer();timer.setSingleShot(True);timer.timeout.connect(app.quit);timer.start(30000)
    def rendered():
        if app.platformName()=='windows':
            image=view.screen().grabWindow(view.winId()).toImage()
        else:
            image=view.grab().toImage()
        if image.isNull():
            return False
        samples={image.pixelColor(x*image.width()//10,y*image.height()//10).name()
                 for x in range(1,10) for y in range(1,10)}
        return len(samples)>3 and sum(color!='#000000' for color in samples)>3

    def inspect_window(state):
        result[state]=rendered()
        if state=='initial_frame':
            view.showMaximized()
            QTimer.singleShot(700,lambda:inspect_window('maximized_frame'))
        elif state=='maximized_frame':
            view.showNormal()
            QTimer.singleShot(700,lambda:inspect_window('restored_frame'))
        else:
            result['ok']=result['dom_ok'] and all(result[key] for key in
                ('initial_frame','maximized_frame','restored_frame'))
            app.quit()

    def done(state):
        if not state:
            result['error']='HTML load failed';app.quit();return
        def inspect(data):
            data=json.loads(data) if isinstance(data,str) and data else {}
            result.update(data)
            result['dom_ok']=bool(data.get('screens')==5 and data.get('active')==1 and data.get('language')=='en'
                              and data.get('version_label','').endswith('v'+VERSION))
            QTimer.singleShot(700,lambda:inspect_window('initial_frame'))
        view.page().runJavaScript('JSON.stringify({screens:document.querySelectorAll(".screen").length,active:document.querySelectorAll(".active-screen").length,language:document.documentElement.lang,version_label:document.querySelector(".version-chip").textContent.trim()})',inspect)
    view.loadFinished.connect(done)
    view.show()
    app.exec()
    view.close();view.deleteLater()
    Path(output_path).write_text(json.dumps(result,indent=2),encoding='utf-8')
    return 0 if result['ok'] else 2
