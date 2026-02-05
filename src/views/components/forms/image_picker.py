"""
Component: ImagePicker
Seletor de imagens com preview e upload remoto
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QSpinBox, QCheckBox, QProgressBar, QApplication,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap
from pathlib import Path
import logging
import configparser

logger = logging.getLogger(__name__)


class UploadWorker(QThread):
    """Worker thread para upload de imagens"""
    finished = pyqtSignal(object)  # UploadResult
    error = pyqtSignal(str)

    def __init__(self, file_path: str, config_path: str = "config.ini"):
        super().__init__()
        self.file_path = file_path
        self.config_path = config_path

    def run(self):
        try:
            from src.services.image_upload import UploaderFactory
            uploader = UploaderFactory.criar_uploader(self.config_path)
            result = uploader.upload(self.file_path)
            self.finished.emit(result)
        except Exception as e:
            logger.exception(f"Erro no upload: {e}")
            self.error.emit(str(e))


class ImagePicker(QWidget):
    """Seletor de imagens com preview e suporte a upload remoto."""
    imageChanged = pyqtSignal(str)
    uploadCompleted = pyqtSignal(str)  # Emite URL remota após upload

    def __init__(self, label="Imagem:", parent=None, enable_remote_upload=True):
        super().__init__(parent)
        self.image_path = None
        self.remote_url = None
        self._upload_worker = None
        self._enable_remote_upload = enable_remote_upload
        self.init_ui(label)

    def init_ui(self, label):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Linha superior: label e botões
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(label))
        self.btn_select = QPushButton("Selecionar Imagem")
        self.btn_select.clicked.connect(self.select_image)
        top_layout.addWidget(self.btn_select)
        self.btn_clear = QPushButton("Remover")
        self.btn_clear.clicked.connect(self.clear_image)
        self.btn_clear.setEnabled(False)
        top_layout.addWidget(self.btn_clear)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Preview da imagem
        self.preview_label = QLabel("Nenhuma imagem selecionada")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(150)
        self.preview_label.setMaximumHeight(300)
        self.preview_label.setStyleSheet("border: 2px dashed #ccc; border-radius: 5px; background-color: #f5f5f5;")
        layout.addWidget(self.preview_label)

        # Escala para LaTeX
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Escala para LaTeX:"))
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(10, 100)
        self.scale_spin.setValue(70)
        self.scale_spin.setSuffix("%")
        scale_layout.addWidget(self.scale_spin)
        scale_layout.addStretch()
        layout.addLayout(scale_layout)

        # Upload remoto (se habilitado)
        if self._enable_remote_upload:
            remote_layout = QHBoxLayout()

            self.chk_upload_remote = QCheckBox("Fazer upload para serviço externo")
            self.chk_upload_remote.setChecked(self._is_remote_upload_configured())
            self.chk_upload_remote.setToolTip(
                "Faz upload da imagem para um serviço externo (ImgBB) "
                "para referenciá-la por URL. Requer API key configurada."
            )
            remote_layout.addWidget(self.chk_upload_remote)

            self.btn_copy_url = QPushButton("Copiar URL")
            self.btn_copy_url.clicked.connect(self.copy_url_to_clipboard)
            self.btn_copy_url.setEnabled(False)
            self.btn_copy_url.setVisible(False)
            remote_layout.addWidget(self.btn_copy_url)

            remote_layout.addStretch()
            layout.addLayout(remote_layout)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_bar.setVisible(False)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setFormat("Fazendo upload...")
            layout.addWidget(self.progress_bar)

            # URL label
            self.url_label = QLabel("")
            self.url_label.setWordWrap(True)
            self.url_label.setVisible(False)
            self.url_label.setStyleSheet("color: #28a745; font-size: 11px;")
            layout.addWidget(self.url_label)

    def _is_remote_upload_configured(self) -> bool:
        """Verifica se o upload remoto está configurado"""
        try:
            config = configparser.ConfigParser()
            config.read("config.ini", encoding="utf-8")
            service = config.get("IMAGES", "upload_service", fallback="local")
            if service == "imgbb":
                api_key = config.get("IMGBB", "api_key", fallback="")
                return bool(api_key and len(api_key) > 10)
            return False
        except Exception:
            return False

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.gif *.bmp *.svg)"
        )
        if file_path:
            self.image_path = file_path
            self.remote_url = None
            self.load_preview()
            self.btn_clear.setEnabled(True)
            self.imageChanged.emit(file_path)

            # Fazer upload remoto se checkbox marcado
            if self._enable_remote_upload and self.chk_upload_remote.isChecked():
                self._start_remote_upload(file_path)
            else:
                self._update_url_display(None)

    def _start_remote_upload(self, file_path: str):
        """Inicia upload remoto em thread separada"""
        self.progress_bar.setVisible(True)
        self.btn_select.setEnabled(False)
        self.btn_clear.setEnabled(False)

        self._upload_worker = UploadWorker(file_path)
        self._upload_worker.finished.connect(self._on_upload_finished)
        self._upload_worker.error.connect(self._on_upload_error)
        self._upload_worker.start()

    @pyqtSlot(object)
    def _on_upload_finished(self, result):
        """Callback quando upload termina"""
        self.progress_bar.setVisible(False)
        self.btn_select.setEnabled(True)
        self.btn_clear.setEnabled(True)

        if result.success:
            self.remote_url = result.url
            self._update_url_display(result.url)
            self.uploadCompleted.emit(result.url)
            logger.info(f"Upload concluído: {result.url}")
        else:
            self._update_url_display(None, error=result.erro)
            logger.error(f"Erro no upload: {result.erro}")

    @pyqtSlot(str)
    def _on_upload_error(self, error_msg: str):
        """Callback quando ocorre erro no upload"""
        self.progress_bar.setVisible(False)
        self.btn_select.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self._update_url_display(None, error=error_msg)

    def _update_url_display(self, url: str, error: str = None):
        """Atualiza exibição da URL/erro"""
        if not self._enable_remote_upload:
            return

        if error:
            self.url_label.setText(f"Erro no upload: {error}")
            self.url_label.setStyleSheet("color: #dc3545; font-size: 11px;")
            self.url_label.setVisible(True)
            self.btn_copy_url.setVisible(False)
            self.btn_copy_url.setEnabled(False)
        elif url:
            self.url_label.setText(f"URL: {url}")
            self.url_label.setStyleSheet("color: #28a745; font-size: 11px;")
            self.url_label.setVisible(True)
            self.btn_copy_url.setVisible(True)
            self.btn_copy_url.setEnabled(True)
        else:
            self.url_label.setVisible(False)
            self.btn_copy_url.setVisible(False)
            self.btn_copy_url.setEnabled(False)

    def copy_url_to_clipboard(self):
        """Copia URL para clipboard"""
        if self.remote_url:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.remote_url)
            QMessageBox.information(self, "URL Copiada", "URL da imagem copiada para a área de transferência!")

    def load_preview(self):
        if self.image_path:
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    400, 300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText("Erro ao carregar imagem")

    def clear_image(self):
        self.image_path = None
        self.remote_url = None
        self.preview_label.clear()
        self.preview_label.setText("Nenhuma imagem selecionada")
        self.btn_clear.setEnabled(False)
        self._update_url_display(None)
        self.imageChanged.emit("")

    def get_image_path(self):
        return self.image_path

    def get_remote_url(self):
        """Retorna URL remota se disponível"""
        return self.remote_url

    def get_best_url(self):
        """Retorna URL remota se disponível, senão caminho local"""
        return self.remote_url or self.image_path

    def get_scale(self):
        return self.scale_spin.value() / 100.0

    def set_image(self, path, scale=0.7, remote_url=None):
        """Define imagem com caminho local e/ou URL remota"""
        if path and Path(path).exists():
            self.image_path = path
            self.load_preview()
            self.btn_clear.setEnabled(True)
            self.scale_spin.setValue(int(scale * 100))

        if remote_url:
            self.remote_url = remote_url
            self._update_url_display(remote_url)

    def set_remote_upload_enabled(self, enabled: bool):
        """Habilita/desabilita upload remoto"""
        if self._enable_remote_upload:
            self.chk_upload_remote.setChecked(enabled)
