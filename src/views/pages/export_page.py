"""
Page: Export Dialog
Diálogo de configuração de exportação LaTeX
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QRadioButton, QButtonGroup, QSpinBox, QSlider,
    QComboBox, QGroupBox, QFileDialog, QMessageBox, QLineEdit,
    QSizePolicy
)
from PyQt6.QtCore import Qt
import logging
from pathlib import Path

from src.utils import ErrorHandler
from src.controllers.adapters import criar_export_controller
from src.application.dtos.export_dto import ExportOptionsDTO

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """Diálogo de configuração de exportação LaTeX"""

    def __init__(self, id_lista: str, parent=None):
        super().__init__(parent)
        self.id_lista = id_lista
        self.controller = criar_export_controller()
        self.setWindowTitle(f"Exportar Lista ID {id_lista} para LaTeX")
        self.setMinimumSize(550, 800)
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
        self.direct_radio.setChecked(True)
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
        layout.addWidget(layout_group)

        img_group = QGroupBox("Imagens")
        img_layout = QVBoxLayout(img_group)
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Escala padrão de imagens (%):"))
        self.escala_slider = QSlider(Qt.Orientation.Horizontal)
        self.escala_slider.setRange(10, 100)
        self.escala_slider.setValue(70)
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
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        template_h_layout.addWidget(self.template_combo)
        template_layout.addLayout(template_h_layout)
        layout.addWidget(template_group)

        # Campos específicos do template Wallon (inicialmente ocultos)
        self.wallon_group = QGroupBox("Configurações do Template Wallon")
        wallon_layout = QVBoxLayout(self.wallon_group)
        wallon_layout.setSpacing(8)

        label_width = 80
        field_height = 30

        # Trimestre
        trimestre_layout = QHBoxLayout()
        lbl_trimestre = QLabel("Trimestre:")
        lbl_trimestre.setFixedSize(label_width, field_height)
        trimestre_layout.addWidget(lbl_trimestre)
        self.trimestre_combo = QComboBox()
        self.trimestre_combo.addItems(["I", "II", "III", "IV"])
        self.trimestre_combo.setFixedSize(100, field_height)
        self.trimestre_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        trimestre_layout.addWidget(self.trimestre_combo)
        trimestre_layout.addStretch()
        wallon_layout.addLayout(trimestre_layout)

        # Professor
        prof_layout = QHBoxLayout()
        lbl_professor = QLabel("Professor:")
        lbl_professor.setFixedSize(label_width, field_height)
        prof_layout.addWidget(lbl_professor)
        self.professor_input = QLineEdit()
        self.professor_input.setPlaceholderText("Nome do professor")
        self.professor_input.setFixedHeight(field_height)
        self.professor_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        prof_layout.addWidget(self.professor_input)
        wallon_layout.addLayout(prof_layout)

        # Disciplina
        disc_layout = QHBoxLayout()
        lbl_disciplina = QLabel("Disciplina:")
        lbl_disciplina.setFixedSize(label_width, field_height)
        disc_layout.addWidget(lbl_disciplina)
        self.disciplina_input = QLineEdit()
        self.disciplina_input.setPlaceholderText("Nome da disciplina")
        self.disciplina_input.setFixedHeight(field_height)
        self.disciplina_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        disc_layout.addWidget(self.disciplina_input)
        wallon_layout.addLayout(disc_layout)

        # Ano
        ano_layout = QHBoxLayout()
        lbl_ano = QLabel("Ano:")
        lbl_ano.setFixedSize(label_width, field_height)
        ano_layout.addWidget(lbl_ano)
        self.ano_input = QLineEdit()
        self.ano_input.setPlaceholderText("Ex: 2025")
        self.ano_input.setText("2025")
        self.ano_input.setFixedSize(100, field_height)
        self.ano_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ano_layout.addWidget(self.ano_input)
        ano_layout.addStretch()
        wallon_layout.addLayout(ano_layout)

        self.wallon_group.setVisible(False)
        self.wallon_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout.addWidget(self.wallon_group)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("❌ Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_preview = QPushButton("👁️ Preview")
        btn_preview.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px 20px; font-weight: bold; border-radius: 4px;")
        btn_preview.setToolTip("Gera um PDF temporário para visualização antes de exportar")
        btn_preview.clicked.connect(self.perform_preview)
        btn_layout.addWidget(btn_preview)
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
            if "default.tex" in templates:
                self.template_combo.setCurrentText("default.tex")
            self._on_template_changed(self.template_combo.currentText())
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar templates LaTeX.")

    def _on_template_changed(self, template_name: str):
        """Mostra/oculta campos específicos do template selecionado."""
        is_wallon = "wallon" in template_name.lower()
        self.wallon_group.setVisible(is_wallon)
        self.adjustSize()

    def perform_preview(self):
        """Gera um PDF temporário para preview antes da exportação final."""
        import tempfile
        import subprocess
        import sys
        import os
        from PyQt6.QtWidgets import QApplication

        logger.info(f"Iniciando preview para lista ID: {self.id_lista}")

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            QApplication.processEvents()

            try:
                temp_dir = Path.home() / ".questoes_preview"
                temp_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Diretório temporário: {temp_dir}")

                template_selecionado = self.template_combo.currentText()
                logger.info(f"Template selecionado: '{template_selecionado}'")

                if not template_selecionado:
                    QApplication.restoreOverrideCursor()
                    ErrorHandler.show_error(self, "Erro", "Nenhum template LaTeX selecionado.")
                    return

                opcoes = ExportOptionsDTO(
                    id_lista=self.id_lista,
                    layout_colunas=self.colunas_spin.value(),
                    incluir_gabarito=self.gabarito_check.isChecked(),
                    incluir_resolucoes=self.resolucao_check.isChecked(),
                    randomizar_questoes=self.randomizar_check.isChecked(),
                    escala_imagens=self.escala_slider.value() / 100.0,
                    template_latex=template_selecionado,
                    tipo_exportacao="direta",
                    output_dir=str(temp_dir),
                    trimestre=self.trimestre_combo.currentText() if self.wallon_group.isVisible() else None,
                    professor=self.professor_input.text() if self.wallon_group.isVisible() else None,
                    disciplina=self.disciplina_input.text() if self.wallon_group.isVisible() else None,
                    ano=self.ano_input.text() if self.wallon_group.isVisible() else None
                )

                logger.info(f"Opções de exportação: {opcoes}")
                result_path = self.controller.exportar_lista(opcoes)
                logger.info(f"Resultado da exportação: {result_path}")

            finally:
                QApplication.restoreOverrideCursor()

            if result_path:
                result_path = Path(result_path) if not isinstance(result_path, Path) else result_path
                logger.info(f"Verificando existência do arquivo: {result_path}")
                if result_path.exists():
                    logger.info(f"Preview gerado com sucesso: {result_path}")
                    if sys.platform == 'win32':
                        os.startfile(str(result_path))
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', str(result_path)])
                    else:
                        subprocess.run(['xdg-open', str(result_path)])
                    return
                else:
                    logger.error(f"Arquivo não existe: {result_path}")

            ErrorHandler.show_error(self, "Erro", "Não foi possível gerar o preview.")

        except RuntimeError as re:
            QApplication.restoreOverrideCursor()
            logger.error(f"RuntimeError no preview: {re}")
            QMessageBox.critical(self, "Erro de Compilação", str(re) + "\nVerifique se há erros no conteúdo LaTeX.")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logger.error(f"Exception no preview: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro no Preview", f"Erro ao gerar preview:\n\n{str(e)}")

    def perform_export(self):
        """Executa a exportação da lista com as configurações escolhidas."""
        try:
            output_dir_str = QFileDialog.getExistingDirectory(
                self, "Selecionar Pasta para Salvar Exportação", str(Path.home())
            )
            if not output_dir_str:
                return
            output_dir = Path(output_dir_str)

            opcoes = ExportOptionsDTO(
                id_lista=self.id_lista,
                layout_colunas=self.colunas_spin.value(),
                incluir_gabarito=self.gabarito_check.isChecked(),
                incluir_resolucoes=self.resolucao_check.isChecked(),
                randomizar_questoes=self.randomizar_check.isChecked(),
                escala_imagens=self.escala_slider.value() / 100.0,
                template_latex=self.template_combo.currentText(),
                tipo_exportacao="direta" if self.direct_radio.isChecked() else "manual",
                output_dir=str(output_dir),
                trimestre=self.trimestre_combo.currentText() if self.wallon_group.isVisible() else None,
                professor=self.professor_input.text() if self.wallon_group.isVisible() else None,
                disciplina=self.disciplina_input.text() if self.wallon_group.isVisible() else None,
                ano=self.ano_input.text() if self.wallon_group.isVisible() else None
            )

            result_path = self.controller.exportar_lista(opcoes)

            if result_path:
                msg = f"Exportação concluída com sucesso para:\n{result_path}"
                ErrorHandler.show_success(self, "Sucesso na Exportação", msg)

                if opcoes.tipo_exportacao == "direta" and result_path.suffix == ".pdf":
                    reply = QMessageBox.question(
                        self, "Abrir PDF", "Deseja abrir o arquivo PDF gerado agora?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
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
