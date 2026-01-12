"""
View: Export Dialog
DESCRIÇÃO: Diálogo de configuração de exportação
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QRadioButton, QButtonGroup, QSpinBox, QSlider,
    QComboBox, QGroupBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
import logging
from pathlib import Path

from src.utils import ErrorHandler
from src.controllers.export_controller import criar_export_controller
from src.application.dtos.export_dto import ExportOptionsDTO

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """Diálogo de configuração de exportação LaTeX"""

    def __init__(self, id_lista: int, parent=None):
        super().__init__(parent)
        self.id_lista = id_lista
        self.controller = criar_export_controller()
        self.setWindowTitle(f"Exportar Lista ID {id_lista} para LaTeX")
        self.setMinimumSize(500, 600)
        self.init_ui()
        self.load_templates()
        logger.info(f"ExportDialog inicializado para lista ID: {id_lista}")

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("📄 Configuração de Exportação LaTeX")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        mode_group = QGroupBox("Modo de Exportação")
        mode_layout = QVBoxLayout(mode_group)
        self.direct_radio = QRadioButton("Exportação Direta (compilar automaticamente para PDF)")
        self.manual_radio = QRadioButton("Exportação Manual (apenas gerar arquivo .tex)")
        self.direct_radio.setChecked(True) # Mudar default para direta
        mode_layout.addWidget(self.direct_radio)
        mode_layout.addWidget(self.manual_radio)
        layout.addWidget(mode_group)

        content_group = QGroupBox("Conteúdo")
        content_layout = QVBoxLayout(content_group)
        self.gabarito_check = QCheckBox("Incluir Gabarito")
        self.gabarito_check.setChecked(True)
        content_layout.addWidget(self.gabarito_check)
        self.resolucao_check = QCheckBox("Incluir Resoluções")
        content_layout.addWidget(self.resolucao_check)
        self.randomizar_check = QCheckBox("Randomizar ordem das questões")
        content_layout.addWidget(self.randomizar_check)
        layout.addWidget(content_group)

        layout_group = QGroupBox("Layout")
        layout_layout = QVBoxLayout(layout_group)
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("Número de colunas:"))
        self.colunas_spin = QSpinBox()
        self.colunas_spin.setRange(1, 2)
        self.colunas_spin.setValue(1)
        col_layout.addWidget(self.colunas_spin)
        col_layout.addStretch()
        layout_layout.addLayout(col_layout)
        # TODO: Implementar espaço para respostas, se necessário no futuro
        # espaco_layout = QHBoxLayout()
        # espaco_layout.addWidget(QLabel("Linhas para resposta:"))
        # self.espaco_spin = QSpinBox()
        # self.espaco_spin.setRange(0, 20)
        # self.espaco_spin.setValue(5)
        # espaco_layout.addWidget(self.espaco_spin)
        # espaco_layout.addStretch()
        # layout_layout.addLayout(espaco_layout)
        layout.addWidget(layout_group)

        img_group = QGroupBox("Imagens")
        img_layout = QVBoxLayout(img_group)
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Escala padrão de imagens (%):"))
        self.escala_slider = QSlider(Qt.Orientation.Horizontal)
        self.escala_slider.setRange(10, 100)
        self.escala_slider.setValue(70) # 0.7
        self.escala_slider.setSingleStep(5)
        self.escala_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.escala_slider.setTickInterval(10)
        scale_layout.addWidget(self.escala_slider)
        self.escala_label = QLabel("70%")
        self.escala_slider.valueChanged.connect(lambda v: self.escala_label.setText(f"{v}%"))
        scale_layout.addWidget(self.escala_label)
        img_layout.addLayout(scale_layout)
        layout.addWidget(img_group)

        template_group = QGroupBox("Template LaTeX")
        template_layout = QVBoxLayout(template_group)
        template_h_layout = QHBoxLayout()
        template_h_layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        template_h_layout.addWidget(self.template_combo)
        template_layout.addLayout(template_h_layout)
        layout.addWidget(template_group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("❌ Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_export = QPushButton("📄 Exportar")
        btn_export.setStyleSheet("background-color: #2980b9; color: white; padding: 8px 20px; font-weight: bold; border-radius: 4px;")
        btn_export.clicked.connect(self.perform_export)
        btn_layout.addWidget(btn_export)
        layout.addLayout(btn_layout)

    def load_templates(self):
        """Carrega os templates LaTeX disponíveis no combobox."""
        try:
            templates = self.controller.listar_templates_disponiveis()
            self.template_combo.clear()
            self.template_combo.addItems(templates)
            # Tenta selecionar o template 'default.tex' se existir
            if "default.tex" in templates:
                self.template_combo.setCurrentText("default.tex")
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar templates LaTeX.")

    def perform_export(self):
        """Executa a exportação da lista com as configurações escolhidas."""
        try:
            # 1. Obter o diretório de saída
            output_dir_str = QFileDialog.getExistingDirectory(
                self, "Selecionar Pasta para Salvar Exportação", str(Path.home())
            )
            if not output_dir_str: # Usuário cancelou
                return
            output_dir = Path(output_dir_str)

            # 2. Coletar as opções do formulário
            opcoes = ExportOptionsDTO(
                id_lista=self.id_lista,
                layout_colunas=self.colunas_spin.value(),
                incluir_gabarito=self.gabarito_check.isChecked(),
                incluir_resolucoes=self.resolucao_check.isChecked(),
                randomizar_questoes=self.randomizar_check.isChecked(),
                escala_imagens=self.escala_slider.value() / 100.0,
                template_latex=self.template_combo.currentText(),
                tipo_exportacao="direta" if self.direct_radio.isChecked() else "manual",
                output_dir=str(output_dir)
            )

            # 3. Chamar o controller para exportar
            result_path = self.controller.exportar_lista(opcoes)

            if result_path:
                msg = f"Exportação concluída com sucesso para:\n{result_path}"
                ErrorHandler.show_success(self, "Sucesso na Exportação", msg)
                
                # Oferecer para abrir o arquivo gerado
                if opcoes.tipo_exportacao == "direta" and result_path.suffix == ".pdf":
                    reply = QMessageBox.question(
                        self, "Abrir PDF", "Deseja abrir o arquivo PDF gerado agora?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        # Abrir o arquivo PDF (multi-plataforma)
                        import os
                        os.startfile(result_path)
                
                self.accept()
            else:
                ErrorHandler.show_error(self, "Erro", "A exportação não gerou nenhum arquivo.")

        except ValueError as ve:
            ErrorHandler.show_warning(self, "Erro de Configuração", str(ve))
        except RuntimeError as re:
            ErrorHandler.show_error(self, "Erro de Compilação", str(re) + "\nVerifique o log para detalhes.")
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro inesperado durante a exportação.")

logger.info("ExportDialog carregado")