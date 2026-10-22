"""Optional component wizard shared by Inno Setup and the existing Settings page."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import time
from PySide6.QtCore import QObject, QThread, QSettings, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton,
    QCheckBox, QFileDialog, QHBoxLayout, QTextEdit, QMessageBox)
from desktop.storage import configure_data_root, validate_local_folder
from engine.control import Cancellation, JobCancelled


class SetupWorker(QObject):
    """Durable stage-by-stage report; retain errors after GUI status is replaced."""

    progress=Signal(str)
    completed=Signal(str)
    finished=Signal()

    def __init__(self, root, gpu, ollama, cancel):
        super().__init__()
        self.root=Path(root);self.gpu=gpu;self.ollama=ollama;self.cancel=cancel
        self.last_update=0
        self.stage='initializing'
        self.report_path=self.root/'Componentes'/'component-setup-report.json'
        self.report={'schema':1,'status':'running','stage':self.stage,
                     'requested':{'cuda':bool(gpu),'ollama':bool(ollama)},
                     'release_allowed':False,
                     'execution_policy':'CPU_ONLY',
                     'note':'CUDA is disabled; Ollama model download is not proof of CPU minutes success.'}

    def save(self, status, detail=None):
        self.report.update(status=status,stage=self.stage)
        if detail is not None: self.report['detail']=str(detail)[:800]
        self.report_path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.report_path.with_suffix('.partial')
        temp.write_text(json.dumps(self.report,indent=2,ensure_ascii=False),encoding='utf-8')
        temp.replace(self.report_path)

    def step(self, name, message):
        self.stage=name
        self.save('running')
        self.progress.emit(message)

    def update(self, message):
        if time.monotonic()-self.last_update>.25:
            self.progress.emit(message);self.last_update=time.monotonic()

    @Slot()
    def run(self):
        try:
            if self.gpu:
                # Fail closed if an obsolete caller tries to request CUDA.
                self.step('cuda_disabled','NVIDIA/CUDA is disabled. CPU only / NVIDIA/CUDA desactivado. Solo CPU')
                raise ValueError('CPU-only policy prohibits optional NVIDIA/CUDA installation')
            if not self.ollama:
                raise ValueError('No optional component selected; CPU transcription needs no installation')
            from engine.ollama import setup_ollama
            self.step('ollama_download_and_test',
                      'Ollama CPU: preparing model / preparando modelo en CPU')
            setup_ollama(self.root,self.update,self.cancel)
            self.report['ollama_validation_ok']=True
            self.step('complete','Ollama CPU validation complete / Validación Ollama CPU completada')
            self.save('success')
            self.completed.emit('Ollama CPU prepared. Report: Componentes/component-setup-report.json / Ollama CPU preparado. Informe guardado.')
        except JobCancelled:
            self.save_failure('cancelled','Setup cancelled by user / Cancelado por el usuario')
            self.completed.emit('Cancelled. See Componentes/component-setup-report.json / Cancelado. Revisa el informe.')
        except Exception as exc:
            self.save_failure('failed',exc)
            self.completed.emit('Setup incomplete at '+self.stage+': '+str(exc)[:400]+
                                ' / Informe: Componentes/component-setup-report.json')
        finally:
            self.finished.emit()

class ComponentDialog(QDialog):
    def __init__(self, root='', language='en', parent=None):
        super().__init__(parent)
        self.language=language;self.root=root;self.thread=None;self.worker=None;self.control=None
        self.setWindowTitle('MeetingSplit — '+self.tr('Optional Ollama CPU','Ollama CPU opcional'))
        self.resize(760,640)
        self.setStyleSheet('QWidget { font-size: 18px; } QPushButton { padding: 9px; }')
        layout=QVBoxLayout(self)
        intro=QLabel(self.tr(
            'CPU-only MeetingSplit. Whisper needs no NVIDIA download. Only Ollama CPU minutes are optional. Choose an internal C: or D: folder; USB/cloud folders are blocked.',
            'MeetingSplit solo CPU. Whisper no necesita descargar NVIDIA. Solo las minutas con Ollama CPU son opcionales. Elige C: o D: internos, sin USB ni nube.'))
        intro.setWordWrap(True);layout.addWidget(intro)
        self.folder=QLabel(root or self.tr('Choose a local folder','Selecciona una carpeta local'))
        self.folder.setWordWrap(True);layout.addWidget(self.folder)
        self.choose=QPushButton(self.tr('Choose folder…','Elegir carpeta…'));self.choose.clicked.connect(self.pick);layout.addWidget(self.choose)
        self.ollama=QCheckBox(self.tr('Ollama + qwen3:4b (~4 GiB download if missing)','Ollama + qwen3:4b (~4 GiB de descarga si faltan)'))
        layout.addWidget(self.ollama)
        self.terms=QCheckBox(self.tr('I accept the Ollama/model licenses and the optional downloads.','Acepto las licencias de Ollama/modelo y las descargas opcionales.'))
        self.terms.setChecked(False)
        notices=QTextEdit();notices.setReadOnly(True)
        notice_path=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))/'docs'/'OPTIONAL_COMPONENTS.md'
        notice_text=notice_path.read_text(encoding='utf-8') if notice_path.is_file() else 'Vendor license notices missing. Setup cannot continue.'
        for license_path in sorted((notice_path.parent/'licenses').glob('*.txt')):
            notice_text+='\n\n--- '+license_path.name+' ---\n'+license_path.read_text(encoding='utf-8')
        notices.setPlainText(notice_text)
        self.notices_present=notice_path.is_file()
        layout.addWidget(notices);layout.addWidget(self.terms)
        self.status=QLabel(self.tr('Nothing will download until you click Prepare. Allow at least 12 GiB free.','No se descargará nada hasta pulsar Preparar. Necesitas al menos 12 GiB libres.'))
        self.status.setWordWrap(True);layout.addWidget(self.status)
        buttons=QHBoxLayout();layout.addLayout(buttons)
        self.prepare=QPushButton(self.tr('Prepare selected components','Preparar componentes seleccionados'))
        self.prepare.clicked.connect(self.start);buttons.addWidget(self.prepare)
        self.close_button=QPushButton(self.tr('Close','Cerrar'));self.close_button.clicked.connect(self.close_or_cancel);buttons.addWidget(self.close_button)
        self.open_report_button=QPushButton(self.tr('Open setup report','Abrir informe de instalación'))
        self.open_report_button.clicked.connect(self.open_report)
        layout.addWidget(self.open_report_button)


    def tr(self, en, es): return es if self.language=='es' else en

    def pick(self):
        folder=QFileDialog.getExistingDirectory(self,self.tr('Internal storage only','Solo almacenamiento interno'),self.root)
        if folder:
            try: self.root=str(configure_data_root(Path(folder)));self.folder.setText(self.root)
            except Exception as exc: QMessageBox.warning(self,'MeetingSplit',str(exc))

    def start(self):
        if self.thread: return
        if not self.root or not self.terms.isChecked() or not self.ollama.isChecked() or not self.notices_present:
            self.status.setText(self.tr('Choose a folder, components and accept their licenses first.','Selecciona carpeta, componentes y acepta sus licencias.'));return
        try:
            root=validate_local_folder(Path(self.root))
            import shutil
            if shutil.disk_usage(root).free<12*1024**3: raise OSError(self.tr('At least 12 GiB free is required.','Se necesitan al menos 12 GiB libres.'))
        except Exception as exc: self.status.setText(str(exc));return
        self.control=Cancellation();self.thread=QThread(self)
        self.worker=SetupWorker(root,False,self.ollama.isChecked(),self.control)
        self.worker.moveToThread(self.thread);self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.status.setText);self.worker.completed.connect(self.status.setText)
        self.worker.finished.connect(self.thread.quit);self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater);self.thread.finished.connect(self.finished_setup)
        for widget in (self.choose,self.ollama,self.terms,self.prepare): widget.setEnabled(False)
        self.close_button.setText(self.tr('Cancel','Cancelar'));self.thread.start()

    def open_report(self):
        if not self.root:
            QMessageBox.information(self,'MeetingSplit',
                self.tr('Choose the component folder first.','Primero selecciona la carpeta de componentes.'))
            return
        report=Path(self.root)/'Componentes'/'component-setup-report.json'
        if not report.is_file():
            QMessageBox.information(self,'MeetingSplit',
                self.tr('No report exists for this attempt. Check prior Ollama receipts in Componentes. The previous app version did not create a summary.',
                        'Todavía no existe informe general de este intento. Revisa los informes de Ollama dentro de Componentes. La versión anterior no generaba resumen.'))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(report)))

    def finished_setup(self):
        self.thread=None;self.worker=None
        self.close_button.setText(self.tr('Close','Cerrar'))
        for widget in (self.choose,self.gpu,self.ollama,self.terms,self.prepare): widget.setEnabled(True)

    def close_or_cancel(self):
        if self.thread:
            self.control.cancel();self.status.setText(self.tr('Cancelling (a stalled connection can take 20 seconds)…','Cancelando (una conexión detenida puede tardar 20 segundos)…'))
        else: self.accept()

    def closeEvent(self, event):
        if self.thread:
            self.close_or_cancel();event.ignore()
        else: super().closeEvent(event)

    def reject(self):
        if self.thread: self.close_or_cancel()
        else: super().reject()


def main():
    app=QApplication(sys.argv)
    settings=QSettings('MeetingSplit','MeetingSplit')
    dialog=ComponentDialog(str(settings.value('storage/data_root','') or ''),str(settings.value('ui/language','en')))
    dialog.exec()
    if dialog.root:
        settings.setValue('storage/data_root',dialog.root);settings.sync()
    return 0
