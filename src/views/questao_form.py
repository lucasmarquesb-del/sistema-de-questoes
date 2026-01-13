"""
View: Questão Form
DESCRIÇÃO: Formulário de cadastro/edição de questões
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QGroupBox, QRadioButton,
    QButtonGroup, QSpinBox, QTextEdit, QTabWidget, QWidget,
    QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
from typing import List

from src.views.widgets import (
    LatexEditor, ImagePicker, TagTreeWidget, DifficultySelector
)
from src.controllers.adapters import criar_questao_controller
from src.controllers.adapters import criar_tag_controller
from src.application.dtos import QuestaoCreateDTO, QuestaoUpdateDTO, AlternativaDTO
from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class QuestaoForm(QDialog):
    """
    Formulário para criar/editar questões.
    Suporta questões objetivas e discursivas.
    """
    questaoSaved = pyqtSignal(int)

    def __init__(self, questao_id=None, parent=None):
        super().__init__(parent)
        self.questao_id = questao_id
        self.is_editing = questao_id is not None

        # Inicializar controllers
        self.controller = criar_questao_controller()
        self.tag_controller = criar_tag_controller()

        self.setWindowTitle("Editar Questão" if self.is_editing else "Nova Questão")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.init_ui()
        self.setup_connections()
        self.load_tags_tree()

        if self.is_editing:
            self.load_questao_data(questao_id)

        logger.info(f"QuestaoForm inicializado (ID: {questao_id})")

    def init_ui(self):
        layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        title_label = QLabel("➕ Nova Questão" if not self.is_editing else "✏️ Editar Questão")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Informações Básicas
        info_group = QGroupBox("Informações Básicas")
        info_layout = QVBoxLayout(info_group)
        titulo_layout = QHBoxLayout()
        titulo_layout.addWidget(QLabel("Título (opcional):"))
        self.titulo_input = QLineEdit()
        self.titulo_input.setPlaceholderText("Ex: Função Quadrática - Vértice da Parábola")
        titulo_layout.addWidget(self.titulo_input)
        info_layout.addLayout(titulo_layout)
        meta_layout = QHBoxLayout()
        meta_layout.addWidget(QLabel("Ano:"))
        self.ano_spin = QSpinBox()
        self.ano_spin.setRange(1900, 2100)
        self.ano_spin.setValue(2026)
        meta_layout.addWidget(self.ano_spin)
        meta_layout.addWidget(QLabel("Fonte/Banca:"))
        self.fonte_combo = QComboBox()
        self.fonte_combo.setEditable(True)
        self.fonte_combo.addItems(["AUTORAL", "ENEM", "FUVEST", "UNICAMP", "UNESP", "UERJ", "ITA", "IME", "MILITAR"])
        meta_layout.addWidget(self.fonte_combo)
        meta_layout.addWidget(QLabel("Tipo:"))
        self.tipo_objetiva = QRadioButton("Objetiva")
        self.tipo_discursiva = QRadioButton("Discursiva")
        self.tipo_objetiva.setChecked(True)
        self.tipo_group = QButtonGroup()
        self.tipo_group.addButton(self.tipo_objetiva, 1)
        self.tipo_group.addButton(self.tipo_discursiva, 2)
        meta_layout.addWidget(self.tipo_objetiva)
        meta_layout.addWidget(self.tipo_discursiva)
        meta_layout.addStretch()
        info_layout.addLayout(meta_layout)
        self.difficulty_selector = DifficultySelector()
        info_layout.addWidget(self.difficulty_selector)
        scroll_layout.addWidget(info_group)

        # Enunciado
        enunciado_group = QGroupBox("Enunciado")
        enunciado_layout = QVBoxLayout(enunciado_group)
        self.enunciado_editor = LatexEditor("Digite o enunciado da questão...")
        enunciado_layout.addWidget(self.enunciado_editor)
        self.enunciado_image = ImagePicker("Imagem do enunciado (opcional):")
        enunciado_layout.addWidget(self.enunciado_image)
        scroll_layout.addWidget(enunciado_group)

        # Alternativas
        self.alternativas_group = QGroupBox("Alternativas")
        alternativas_layout = QVBoxLayout(self.alternativas_group)
        self.alternativas_widgets = []
        for letra in ['A', 'B', 'C', 'D', 'E']:
            alt_widget = self.create_alternativa_widget(letra)
            self.alternativas_widgets.append(alt_widget)
            alternativas_layout.addWidget(alt_widget)
        scroll_layout.addWidget(self.alternativas_group)

        # Abas de Resolução, Gabarito, etc.
        tab_widget = QTabWidget()
        resolucao_tab = QWidget()
        resolucao_layout = QVBoxLayout(resolucao_tab)
        self.resolucao_editor = LatexEditor("Digite a resolução detalhada (opcional)...")
        resolucao_layout.addWidget(self.resolucao_editor)
        tab_widget.addTab(resolucao_tab, "Resolução")
        gabarito_tab = QWidget()
        gabarito_layout = QVBoxLayout(gabarito_tab)
        gabarito_layout.addWidget(QLabel("Para questões discursivas, descreva o gabarito esperado:"))
        self.gabarito_editor = LatexEditor("Digite o gabarito para questões discursivas...")
        gabarito_layout.addWidget(self.gabarito_editor)
        tab_widget.addTab(gabarito_tab, "Gabarito Discursiva")
        obs_tab = QWidget()
        obs_layout = QVBoxLayout(obs_tab)
        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setPlaceholderText("Observações adicionais sobre a questão...")
        obs_layout.addWidget(self.observacoes_edit)
        tab_widget.addTab(obs_tab, "Observações")
        scroll_layout.addWidget(tab_widget)

        # Tags
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        tags_layout.addWidget(QLabel("Selecione as tags que classificam esta questão:"))
        self.tag_tree_widget = TagTreeWidget()
        tags_layout.addWidget(self.tag_tree_widget)
        scroll_layout.addWidget(tags_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_preview = QPushButton("👁️ Preview")
        btn_preview.clicked.connect(self.show_preview)
        btn_layout.addWidget(btn_preview)
        btn_cancel = QPushButton("❌ Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_save = QPushButton("💾 Salvar")
        btn_save.setStyleSheet("background-color: #1abc9c; color: white; padding: 8px 20px; border-radius: 4px; font-weight: bold;")
        btn_save.clicked.connect(self.save_questao)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def create_alternativa_widget(self, letra):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        checkbox = QCheckBox()
        checkbox.setToolTip("Marque como correta")
        layout.addWidget(checkbox)
        letra_label = QLabel(f"{letra})")
        letra_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(letra_label)
        texto_input = QLineEdit()
        texto_input.setPlaceholderText(f"Digite o texto da alternativa {letra}...")
        layout.addWidget(texto_input)
        btn_image = QPushButton("🖼️")
        btn_image.setMaximumWidth(40)
        btn_image.setToolTip("Adicionar imagem à alternativa")
        layout.addWidget(btn_image)
        widget.checkbox = checkbox
        widget.letra = letra
        widget.texto_input = texto_input
        widget.btn_image = btn_image
        widget.image_path = None
        return widget

    def setup_connections(self):
        self.tipo_objetiva.toggled.connect(self.on_tipo_changed)

    def on_tipo_changed(self, checked):
        is_objetiva = self.tipo_objetiva.isChecked()
        self.alternativas_group.setVisible(is_objetiva)

    def load_tags_tree(self):
        """Carrega a árvore de tags usando o TagController."""
        try:
            tags_arvore = self.tag_controller.obter_arvore_tags_completa()
            self.tag_tree_widget.load_tags(tags_arvore)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar as tags")

    def load_questao_data(self, questao_id):
        """Carrega os dados de uma questão existente para edição."""
        logger.info(f"Carregando dados da questão ID: {questao_id} para edição.")
        try:
            dto = self.controller.obter_questao_completa(questao_id)
            if not dto:
                QMessageBox.critical(self, "Erro", "Não foi possível carregar a questão.")
                self.close()
                return

            self.titulo_input.setText(dto.titulo or "")
            self.ano_spin.setValue(dto.ano or 2026)
            self.fonte_combo.setCurrentText(dto.fonte or "")
            self.difficulty_selector.set_difficulty(dto.id_dificuldade)
            self.enunciado_editor.set_text(dto.enunciado)
            self.resolucao_editor.set_text(dto.resolucao or "")
            self.observacoes_edit.setPlainText(dto.observacoes or "")
            
            if dto.tipo == 'OBJETIVA':
                self.tipo_objetiva.setChecked(True)
                if dto.alternativas:
                    for i, alt_dto in enumerate(dto.alternativas):
                        if i < len(self.alternativas_widgets):
                            alt_widget = self.alternativas_widgets[i]
                            alt_widget.texto_input.setText(alt_dto.texto)
                            alt_widget.checkbox.setChecked(alt_dto.correta)
            else:
                self.tipo_discursiva.setChecked(True)
            
            if dto.tags:
                tag_ids = [tag['id_tag'] for tag in dto.tags]
                self.tag_tree_widget.set_selected_tags(tag_ids)

        except Exception as e:
            ErrorHandler.handle_exception(self, e, f"Erro ao carregar dados da questão {questao_id}")
            self.close()

    def get_form_data(self) -> dict:
        """Coleta e retorna os dados do formulário em um dicionário."""
        data = {
            'titulo': self.titulo_input.text().strip() or None,
            'enunciado': self.enunciado_editor.get_text(),
            'tipo': 'OBJETIVA' if self.tipo_objetiva.isChecked() else 'DISCURSIVA',
            'ano': self.ano_spin.value(),
            'fonte': self.fonte_combo.currentText(),
            'id_dificuldade': self.difficulty_selector.get_selected_difficulty(),
            'imagem_enunciado': self.enunciado_image.get_image_path(),
            'escala_imagem_enunciado': self.enunciado_image.get_scale(),
            'resolucao': self.resolucao_editor.get_text() or None,
            'gabarito_discursiva': self.gabarito_editor.get_text() or None,
            'observacoes': self.observacoes_edit.toPlainText().strip() or None,
            'tags': self.tag_tree_widget.get_selected_tag_ids(),
            'alternativas': []
        }
        if data['tipo'] == 'OBJETIVA':
            for widget in self.alternativas_widgets:
                data['alternativas'].append({
                    'letra': widget.letra,
                    'texto': widget.texto_input.text().strip(),
                    'correta': widget.checkbox.isChecked(),
                    'imagem': widget.image_path
                })
        return data

    def save_questao(self):
        """Valida e salva a questão (criação ou atualização)."""
        logger.info("Tentando salvar a questão...")
        form_data = self.get_form_data()
        
        try:
            if self.is_editing:
                dto = QuestaoUpdateDTO(id_questao=self.questao_id, **form_data)
                sucesso = self.controller.atualizar_questao_completa(dto)
                msg = f"Questão {self.questao_id} atualizada com sucesso!"
            else:
                alternativas_dto = [AlternativaDTO(**alt) for alt in form_data.pop('alternativas')]
                dto = QuestaoCreateDTO(alternativas=alternativas_dto, **form_data)
                id_questao = self.controller.criar_questao_completa(dto)
                sucesso = id_questao is not None
                msg = f"Questão criada com sucesso! ID: {id_questao}"

            if sucesso:
                ErrorHandler.show_success(self, "Sucesso", msg)
                self.questaoSaved.emit(self.questao_id or id_questao)
                self.accept()
            else:
                ErrorHandler.show_warning(self, "Falha", "Não foi possível salvar a questão.")

        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao salvar questão")
            
    def show_preview(self):
        QMessageBox.information(self, "Preview", "Funcionalidade de preview ainda não implementada.")

logger.info("QuestaoForm carregado")