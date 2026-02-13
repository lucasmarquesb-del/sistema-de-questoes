"""Diálogo de atualização OTA do app."""

import logging
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)


class _CheckUpdateThread(QThread):
    """Thread para verificar atualizações sem bloquear a UI."""

    update_available = pyqtSignal(dict)  # {version, download_url, notes}
    no_update = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            from src.services.update_service import UpdateService

            service = UpdateService()
            result = service.check_for_update()
            if result:
                self.update_available.emit(result)
            else:
                self.no_update.emit()
        except Exception as e:
            self.error.emit(str(e))


class _DownloadThread(QThread):
    """Thread para baixar a atualização."""

    progress = pyqtSignal(int, int)  # bytes_downloaded, total_bytes
    finished = pyqtSignal(object)  # Path do zip ou None se falhou
    error = pyqtSignal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            from src.services.update_service import UpdateService

            service = UpdateService()
            dest = Path(tempfile.gettempdir()) / "OharaBank_update.zip"
            ok = service.download_update(self.url, dest, self._on_progress)
            self.finished.emit(dest if ok else None)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, downloaded: int, total: int):
        self.progress.emit(downloaded, total)


class UpdateDialog(QDialog):
    """Diálogo que exibe informações sobre uma nova versão e permite atualizar."""

    update_accepted = pyqtSignal(Path)  # Emitido com o path do zip baixado

    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self._download_thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Atualização Disponível")
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Título
        version = self.update_info["version"]
        title = QLabel(f"Nova versão {version} disponível!")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1258e2;")
        layout.addWidget(title)

        # Subtítulo
        from src.version import __version__
        subtitle = QLabel(f"Versão atual: {__version__}")
        subtitle.setStyleSheet("font-size: 13px; color: #616f89;")
        layout.addWidget(subtitle)

        # Release notes
        notes = self.update_info.get("notes", "").strip()
        if notes:
            notes_label = QLabel("Novidades:")
            notes_label.setStyleSheet("font-size: 13px; font-weight: 600; margin-top: 4px;")
            layout.addWidget(notes_label)

            notes_text = QTextEdit()
            notes_text.setReadOnly(True)
            notes_text.setMarkdown(notes)
            notes_text.setMaximumHeight(160)
            notes_text.setStyleSheet(
                "QTextEdit { background: #f6f6f8; border: 1px solid #e0e0e0; "
                "border-radius: 6px; padding: 8px; font-size: 13px; }"
            )
            layout.addWidget(notes_text)

        # Barra de progresso (inicialmente oculta)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #e0e0e0; border-radius: 4px; "
            "text-align: center; height: 22px; background: #f6f6f8; }"
            "QProgressBar::chunk { background: #1258e2; border-radius: 3px; }"
        )
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; color: #616f89;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_later = QPushButton("Depois")
        self.btn_later.setMinimumWidth(100)
        self.btn_later.setStyleSheet(
            "QPushButton { padding: 8px 20px; border: 1px solid #e0e0e0; "
            "border-radius: 6px; background: white; color: #616f89; font-size: 13px; }"
            "QPushButton:hover { background: #f6f6f8; }"
        )
        self.btn_later.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_later)

        self.btn_update = QPushButton("Atualizar agora")
        self.btn_update.setMinimumWidth(140)
        self.btn_update.setStyleSheet(
            "QPushButton { padding: 8px 20px; border: none; border-radius: 6px; "
            "background: #1258e2; color: white; font-weight: bold; font-size: 13px; }"
            "QPushButton:hover { background: #0d47b8; }"
        )
        self.btn_update.clicked.connect(self._start_download)
        btn_layout.addWidget(self.btn_update)

        layout.addLayout(btn_layout)

    def _start_download(self):
        """Inicia o download da atualização."""
        self.btn_update.setEnabled(False)
        self.btn_update.setText("Baixando...")
        self.btn_later.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("Iniciando download...")

        url = self.update_info["download_url"]
        self._download_thread = _DownloadThread(url, self)
        self._download_thread.progress.connect(self._on_progress)
        self._download_thread.finished.connect(self._on_download_finished)
        self._download_thread.error.connect(self._on_download_error)
        self._download_thread.start()

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int(downloaded * 100 / total)
            self.progress_bar.setValue(pct)
            mb_down = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(f"Baixando... {mb_down:.1f} / {mb_total:.1f} MB")
        else:
            mb_down = downloaded / (1024 * 1024)
            self.status_label.setText(f"Baixando... {mb_down:.1f} MB")

    def _on_download_finished(self, zip_path):
        if zip_path:
            self.status_label.setText("Download concluído! Aplicando atualização...")
            self.update_accepted.emit(zip_path)
            self.accept()
        else:
            self._on_download_error("Falha no download.")

    def _on_download_error(self, msg: str):
        self.status_label.setText(f"Erro: {msg}")
        self.status_label.setStyleSheet("font-size: 12px; color: #dc2626;")
        self.btn_update.setEnabled(True)
        self.btn_update.setText("Tentar novamente")
        self.btn_later.setEnabled(True)


def check_for_updates_async(parent=None, on_update_available=None):
    """
    Verifica atualizações em background. Chama on_update_available(dict) se houver.
    Retorna a thread (deve ser mantida como referência para não ser coletada pelo GC).
    """
    thread = _CheckUpdateThread(parent)

    def _on_available(info):
        if on_update_available:
            on_update_available(info)

    thread.update_available.connect(_on_available)
    thread.no_update.connect(lambda: logger.info("Nenhuma atualização disponível."))
    thread.error.connect(lambda e: logger.warning(f"Erro ao verificar atualizações: {e}"))
    thread.start()
    return thread
