"""Native Windows desktop window with an offline, cinematic HTML UI."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
from PySide6.QtCore import QObject, QThread, Qt, QUrl, QSettings, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from engine.job import run_job
from engine.control import Cancellation, JobCancelled
from desktop.storage import configure_data_root, validate_local_folder, UnsafeStorage

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))

class BlockNetwork(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        # Visual interface has NO permission to request remote resources.
        if info.requestUrl().scheme().lower() in ('https','http','ws','wss','ftp'):
            info.block(True)

class JobWorker(QObject):
    progress=Signal(str,int)
    complete=Signal(str)
    error=Signal(str)
    finished=Signal()
    cancelled=Signal(str)
    def __init__(self, configuration, control:Cancellation):
        super().__init__();self.configuration=configuration;self.control=control
    @Slot()
    def run(self):
        try:
            output=run_job(self.configuration,lambda message,pct:self.progress.emit(message,pct),self.control)
            self.complete.emit(str(output))
        except JobCancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

class DesktopBridge(QObject):
    fileSelected=Signal(str)
    folderSelected=Signal(str)
    progress=Signal(str,int)
    completed=Signal(str)
    failed=Signal(str)
    cancelled=Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread=None;self._worker=None;self._control=None;self._last_folder=None
        self._source=''
        self._settings=QSettings('MeetingSplit','MeetingSplit')
        self._output=str(self._settings.value('storage/data_root','') or '')
        if self._output:
            try: validate_local_folder(Path(self._output))
            except (OSError,UnsafeStorage): self._output=''


    @Slot(result=str)
    def getUILanguage(self):
        language=str(self._settings.value('ui/language','en') or 'en')
        return language if language in ('en','es') else 'en'

    @Slot(str)
    def setUILanguage(self, language):
        if language in ('en','es'):
            self._settings.setValue('ui/language', language)
            self._settings.sync()

    @Slot()
    def openPayPalSupport(self):
        """Open the public owner-supplied PayPal link in the SYSTEM browser.

        Invoked solely from the support link click; the audio UI stays offline.
        """
        url=QUrl('https://www.paypal.com/ncp/payment/XPUK3HVHJW8KE')
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(None,
                self._tr('Cannot open PayPal','No se pudo abrir PayPal'),
                self._tr('Could not open your browser. Please try again.',
                         'No se pudo abrir el navegador. Inténtalo nuevamente.'))

    def _tr(self, english, spanish):
        return english if self.getUILanguage()=='en' else spanish

    @Slot()
    def pickFile(self):
        file,_=QFileDialog.getOpenFileName(None,self._tr('Select a recording','Selecciona tu grabación'),'',
            self._tr('Audio recordings','Grabaciones')+' (*.mp3 *.m4a *.wav *.aac *.flac *.ogg *.mp4 *.opus *.wma);;'+self._tr('All files','Todos los archivos')+' (*)')
        if file:
            self._source=file
            self.fileSelected.emit(file)

    @Slot()
    def pickOutput(self):
        # LocalAppData is normally outside OneDrive-synced Desktop/Documents.
        safe_start=Path(os.environ.get('LOCALAPPDATA') or str(Path.home()))
        start=self._output if self._output else str(safe_start if safe_start.is_dir() else Path.home())
        folder=QFileDialog.getExistingDirectory(None,
            self._tr('Choose a LOCAL folder for MeetingSplit data (no USB)','Elige una carpeta LOCAL para los datos de MeetingSplit (no USB)'),start)
        if not folder:
            if not self._output:
                self.failed.emit(self._tr('You must choose a local folder before processing.','Debes seleccionar una carpeta local para guardar datos antes de procesar.'))
            return
        try:
            root=configure_data_root(Path(folder))
        except (OSError,UnsafeStorage) as exc:
            QMessageBox.warning(None,self._tr('Drive not allowed','Unidad no permitida'),str(exc))
            self.failed.emit(str(exc));return
        self._output=str(root)
        self._settings.setValue('storage/data_root',self._output)
        self._settings.sync()
        self.folderSelected.emit(self._output)

    @Slot()
    def ensureOutput(self):
        if self._output:return
        QMessageBox.information(None,
            self._tr('MeetingSplit first-time setup','Configuración inicial de MeetingSplit'),
            self._tr(
               'Choose where to store your data, models, and results.\n\n'
               'If your PC has internal C: and D: drives, you can choose either. '
               'If it only has C:, select a folder on C:.\n\n'
               'Removable USB drives such as J: and cloud-synced folders '
               'will not be used for results.\n\n'
               'Your choice will be remembered and can be changed in Settings.',
               'Escoge dónde guardar los datos, modelos y resultados.\n\n'
               'En un equipo con C: y D:, puedes escoger cualquiera de las dos unidades internas. '
               'En un equipo con solo C:, selecciona una carpeta de C:.\n\n'
               'Las unidades USB extraíbles, como J:, y las carpetas sincronizadas con la nube '
               'no se usarán para almacenar los resultados.\n\n'
               'Esta elección se recordará y podrás cambiarla desde la aplicación.'))
        self.pickOutput()

    @Slot(result=str)
    def getDefaultOutput(self):
        return self._output

    @Slot(str)
    def startJob(self, payload):
        if self._thread and self._thread.isRunning():
            self.failed.emit(self._tr('A meeting is already processing.','Hay una reunión procesándose.'));return
        try:
            conf=json.loads(payload)
            conf['file']=self._source
            conf['output']=self._output
            conf['model_cache']=str(Path(self._output)/'Modelos')
            if not self._source: raise ValueError(self._tr('Choose a recording first.','Primero selecciona una grabación.'))
            if not self._output:raise ValueError(self._tr('Choose a local folder for your data first.','Primero escoge una carpeta local para los datos.'))
            validate_local_folder(Path(self._output))
        except Exception as exc:
            self.failed.emit(str(exc));return
        self._control=Cancellation()
        self._thread=QThread(self)
        self._worker=JobWorker(conf,self._control)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress.emit)
        self._worker.complete.connect(self._completed)
        self._worker.cancelled.connect(self.cancelled.emit)
        self._worker.error.connect(self.failed.emit)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()

    @Slot(str)
    def _completed(self, path):
        self._last_folder=path
        self.completed.emit(path)

    @Slot()
    def _cleanup(self):
        self._thread=None
        self._worker=None
        self._control=None

    @Slot()
    def cancelJob(self):
        if self._control and self._thread and self._thread.isRunning():
            self._control.cancel()
            self.progress.emit(self._tr('Cancelling; completed parts will be kept...','Cancelando; se conservarán las partes completadas...'),0)

    @Slot(result=str)
    def getResultIndex(self):
        """Return only known generated files from the completed job folder."""
        if not self._last_folder:
            return '[]'
        root=Path(self._last_folder)
        if not root.is_dir():
            return '[]'
        exact={'TRANSCRIPCION_COMPLETA.txt':'Transcripción completa',
               'TRANSCRIPCION_SUBTITULOS.srt':'Subtítulos SRT',
               'RESUMEN_Y_MINUTA_LOCAL.md':'Resumen y minuta local',
               'RESULTADOS_COMPLETOS.zip':'Paquete ZIP',
               'INSTRUCCIONES_CHATGPT_GEMINI.txt':'Instrucciones para IA'}
        files=[]
        for name,title in exact.items():
            path=root/name
            if path.is_file() and not path.is_symlink():
                files.append({'name':name,'label':title,'bytes':path.stat().st_size})
        return json.dumps(files,ensure_ascii=False)

    @Slot(str)
    def openOutputFile(self, name):
        """Open a generated, explicitly allowlisted result; prevent traversal."""
        if not self._last_folder or not isinstance(name,str):
            return
        names={'TRANSCRIPCION_COMPLETA.txt','TRANSCRIPCION_SUBTITULOS.srt',
               'RESUMEN_Y_MINUTA_LOCAL.md','RESULTADOS_COMPLETOS.zip',
               'INSTRUCCIONES_CHATGPT_GEMINI.txt'}
        if name not in names:
            return
        root=Path(self._last_folder).resolve()
        file=(root/name).resolve()
        if file.parent==root and file.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file)))

    @Slot()
    def openResult(self):
        if self._last_folder and Path(self._last_folder).is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_folder))

class MainWindow(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MeetingSplit | Private Audio Studio')
        self.resize(1366,880)
        self.setMinimumSize(920,670)
        self._interceptor=BlockNetwork(self)
        self.page().profile().setUrlRequestInterceptor(self._interceptor)
        self.bridge=DesktopBridge(self)
        self.channel=QWebChannel(self.page())
        self.channel.registerObject('desktop',self.bridge)
        self.page().setWebChannel(self.channel)
        self.load(QUrl.fromLocalFile(str(ROOT/'ui'/'index.html')))

    def closeEvent(self, event):
        thread=self.bridge._thread
        if thread and thread.isRunning():
            QMessageBox.warning(self,
                'Meeting in progress' if self.bridge.getUILanguage()=='en' else 'Grabación en proceso',
                ('Press CANCEL and wait for processing to stop.\nCompleted results will be kept.' if self.bridge.getUILanguage()=='en' else
                 'Para salir, pulsa CANCELAR y espera a que el motor se detenga.\nLos resultados ya completados se conservarán.'))
            event.ignore()
            return
        super().closeEvent(event)


def main():
    app=QApplication(sys.argv)
    app.setApplicationName('MeetingSplit')
    app.setOrganizationName('MeetingSplit')
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    view=MainWindow();view.show()
    sys.exit(app.exec())

if __name__=='__main__':main()
