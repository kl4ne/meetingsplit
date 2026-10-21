"""Optional component wizard shared by Inno Setup and the existing Settings page."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import time
from PySide6.QtCore import QObject, QThread, QSettings, Signal, Slot
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QPushButton,
    QCheckBox, QFileDialog, QHBoxLayout, QTextEdit, QMessageBox)
from desktop.storage import configure_data_root, validate_local_folder
from engine.control import Cancellation, JobCancelled


class SetupWorker(QObject):
    progress=Signal(str)
    completed=Signal(str)
    finished=Signal()

    def __init__(self, root, gpu, ollama, cancel):
        super().__init__();self.root=root;self.gpu=gpu;self.ollama=ollama;self.cancel=cancel
        self.last_update=0

    def update(self, message):
        if time.monotonic()-self.last_update>.25:
            self.progress.emit(message);self.last_update=time.monotonic()

    @Slot()
    def run(self):
        try:
            if self.gpu:
                from desktop.components import install_gpu
                from desktop.cuda_probe import probe_cuda
                install_gpu(self.root,self.update,self.cancel)
                self.progress.emit('CUDA: testing real inference / probando inferencia real (small)...')
                report=probe_cuda('small',self.root/'Modelos',cancel=self.cancel)
                (self.root/'Componentes'/'cuda-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                if not report.get('ok'): raise RuntimeError(report.get('error','CUDA test failed'))
            if self.ollama:
                from engine.ollama import setup_ollama
                setup_ollama(self.root,self.update,self.cancel)
            self.completed.emit('Components prepared. Review the local test reports. / Componentes preparados. Revisa los informes de prueba locales.')
        except JobCancelled:
            self.completed.emit('Cancelled. Verified completed components kept. / Cancelado. Se conservaron los componentes completos verificados.')
        except Exception as exc:
            self.completed.emit('Setup incomplete / Configuración incompleta: '+str(exc))
        finally: self.finished.emit()


class ComponentDialog(QDialog):
    def __init__(self, root='', language='en', parent=None):
        super().__init__(parent)
        self.language=language;self.root=root;self.thread=None;self.worker=None;self.control=None
        self.setWindowTitle('MeetingSplit — '+self.tr('Optional components','Componentes opcionales'))
        self.resize(760,640)
        self.setStyleSheet('QWidget { font-size: 18px; } QPushButton { padding: 9px; }')
        layout=QVBoxLayout(self)
        intro=QLabel(self.tr(
            'Optional downloads for this PC. Choose an internal folder on C: or D:.\nUSB and cloud folders remain blocked. CPU transcription remains available.',
            'Descargas opcionales para este equipo. Escoge una carpeta interna en C: o D:.\nUSB y nube siguen bloqueados. La transcripción CPU sigue disponible.'))
        intro.setWordWrap(True);layout.addWidget(intro)
        self.folder=QLabel(root or self.tr('Choose a local folder','Selecciona una carpeta local'))
        self.folder.setWordWrap(True);layout.addWidget(self.folder)
        self.choose=QPushButton(self.tr('Choose folder…','Elegir carpeta…'));self.choose.clicked.connect(self.pick);layout.addWidget(self.choose)
        self.gpu=QCheckBox(self.tr('NVIDIA CUDA 12 + cuDNN 9 (~1.1 GiB download)','NVIDIA CUDA 12 + cuDNN 9 (~1.1 GiB de descarga)'))
        self.ollama=QCheckBox(self.tr('Ollama + qwen3:4b (~4 GiB download if missing)','Ollama + qwen3:4b (~4 GiB de descarga si faltan)'))
        layout.addWidget(self.gpu);layout.addWidget(self.ollama)
        self.terms=QCheckBox(self.tr('I accept the selected vendor licenses and optional downloads.','Acepto las licencias y descargas opcionales seleccionadas.'))
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

    def tr(self, en, es): return es if self.language=='es' else en

    def pick(self):
        folder=QFileDialog.getExistingDirectory(self,self.tr('Internal storage only','Solo almacenamiento interno'),self.root)
        if folder:
            try: self.root=str(configure_data_root(Path(folder)));self.folder.setText(self.root)
            except Exception as exc: QMessageBox.warning(self,'MeetingSplit',str(exc))

    def start(self):
        if self.thread: return
        if not self.root or not self.terms.isChecked() or not (self.gpu.isChecked() or self.ollama.isChecked()) or not self.notices_present:
            self.status.setText(self.tr('Choose a folder, components and accept their licenses first.','Selecciona carpeta, componentes y acepta sus licencias.'));return
        try:
            root=validate_local_folder(Path(self.root))
            import shutil
            if shutil.disk_usage(root).free<12*1024**3: raise OSError(self.tr('At least 12 GiB free is required.','Se necesitan al menos 12 GiB libres.'))
        except Exception as exc: self.status.setText(str(exc));return
        self.control=Cancellation();self.thread=QThread(self)
        self.worker=SetupWorker(root,self.gpu.isChecked(),self.ollama.isChecked(),self.control)
        self.worker.moveToThread(self.thread);self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.status.setText);self.worker.completed.connect(self.status.setText)
        self.worker.finished.connect(self.thread.quit);self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater);self.thread.finished.connect(self.finished_setup)
        for widget in (self.choose,self.gpu,self.ollama,self.terms,self.prepare): widget.setEnabled(False)
        self.close_button.setText(self.tr('Cancel','Cancelar'));self.thread.start()

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
