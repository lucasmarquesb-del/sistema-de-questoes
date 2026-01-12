"""
View: Questão Form
DESCRIÇÃO: Formulário de cadastro/edição de questões
RELACIONAMENTOS: QuestaoController, AlternativaModel, TagModel
COMPONENTES:
    - Campo título (opcional)
    - Editor de enunciado (suporta LaTeX)
    - Radio buttons: Objetiva/Discursiva
    - Campos: Ano, Fonte, Dificuldade
    - Botão adicionar imagem
    - Preview LaTeX
    - 5 campos de alternativas (se objetiva)
    - Seleção de tags (árvore hierárquica)
    - Botões: Salvar, Cancelar, Preview
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QGroupBox, QRadioButton,
    QButtonGroup, QSpinBox, QTextEdit, QTabWidget, QWidget,
    QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.views.widgets import (
    LatexEditor, ImagePicker, TagTreeWidget, DifficultySelector
)
from src.controllers.questao_controller_refactored import criar_questao_controller
from src.application.dtos import QuestaoCreateDTO, QuestaoUpdateDTO, AlternativaDTO

logger = logging.getLogger(__name__)


class QuestaoForm(QDialog):
    """
    Formulário para criar/editar questões.
    Suporta questões objetivas e discursivas.
    """

    questaoSaved = pyqtSignal(int)  # Emite ID da questão salva

    def __init__(self, questao_id=None, parent=None):
        super().__init__(parent)
        self.questao_id = questao_id
        self.is_editing = questao_id is not None

        # Inicializar controller
        self.controller = criar_questao_controller()

        self.setWindowTitle("Editar Questão" if self.is_editing else "Nova Questão")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.init_ui()
        self.setup_connections()

        if self.is_editing:
            self.load_questao(questao_id)

        logger.info(f"QuestaoForm inicializado (ID: {questao_id})")

    def init_ui(self):
        """Configura a interface do formulário"""
        layout = QVBoxLayout(self)

        # Cabeçalho
        header_layout = QHBoxLayout()

        title_label = QLabel("➕ Nova Questão" if not self.is_editing else "✏️ Editar Questão")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Área de scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # ========== INFORMAÇÕES BÁSICAS ==========
        info_group = QGroupBox("Informações Básicas")
        info_layout = QVBoxLayout(info_group)

        # Título (opcional)
        titulo_layout = QHBoxLayout()
        titulo_layout.addWidget(QLabel("Título (opcional):"))
        self.titulo_input = QLineEdit()
        self.titulo_input.setPlaceholderText("Ex: Função Quadrática - Vértice da Parábola")
        titulo_layout.addWidget(self.titulo_input)
        info_layout.addLayout(titulo_layout)

        # Linha com Ano, Fonte, Tipo
        meta_layout = QHBoxLayout()

        # Ano
        meta_layout.addWidget(QLabel("Ano:"))
        self.ano_spin = QSpinBox()
        self.ano_spin.setRange(1900, 2100)
        self.ano_spin.setValue(2026)
        meta_layout.addWidget(self.ano_spin)

        # Fonte
        meta_layout.addWidget(QLabel("Fonte/Banca:"))
        self.fonte_combo = QComboBox()
        self.fonte_combo.setEditable(True)
        self.fonte_combo.addItems([
            "AUTORAL",
            "ENEM",
            "FUVEST",
            "UNICAMP",
            "UNESP",
            "UERJ",
            "ITA",
            "IME",
            "MILITAR"
        ])
        meta_layout.addWidget(self.fonte_combo)

        # Tipo
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

        # Dificuldade
        self.difficulty_selector = DifficultySelector()
        info_layout.addWidget(self.difficulty_selector)

        scroll_layout.addWidget(info_group)

        # ========== ENUNCIADO ==========
        enunciado_group = QGroupBox("Enunciado")
        enunciado_layout = QVBoxLayout(enunciado_group)

        self.enunciado_editor = LatexEditor("Digite o enunciado da questão...")
        enunciado_layout.addWidget(self.enunciado_editor)

        # Imagem do enunciado
        self.enunciado_image = ImagePicker("Imagem do enunciado (opcional):")
        enunciado_layout.addWidget(self.enunciado_image)

        scroll_layout.addWidget(enunciado_group)

        # ========== ALTERNATIVAS (se objetiva) ==========
        self.alternativas_group = QGroupBox("Alternativas")
        alternativas_layout = QVBoxLayout(self.alternativas_group)

        self.alternativas_widgets = []
        letras = ['A', 'B', 'C', 'D', 'E']

        for letra in letras:
            alt_widget = self.create_alternativa_widget(letra)
            self.alternativas_widgets.append(alt_widget)
            alternativas_layout.addWidget(alt_widget)

        scroll_layout.addWidget(self.alternativas_group)

        # ========== RESOLUÇÃO E GABARITO ==========
        tab_widget = QTabWidget()

        # Tab: Resolução
        resolucao_tab = QWidget()
        resolucao_layout = QVBoxLayout(resolucao_tab)
        self.resolucao_editor = LatexEditor("Digite a resolução detalhada (opcional)...")
        resolucao_layout.addWidget(self.resolucao_editor)
        tab_widget.addTab(resolucao_tab, "Resolução")

        # Tab: Gabarito Discursiva
        gabarito_tab = QWidget()
        gabarito_layout = QVBoxLayout(gabarito_tab)
        gabarito_info = QLabel("Para questões discursivas, descreva o gabarito esperado:")
        gabarito_info.setStyleSheet("color: #666; margin-bottom: 5px;")
        gabarito_layout.addWidget(gabarito_info)
        self.gabarito_editor = LatexEditor("Digite o gabarito para questões discursivas...")
        gabarito_layout.addWidget(self.gabarito_editor)
        tab_widget.addTab(gabarito_tab, "Gabarito Discursiva")

        # Tab: Observações
        obs_tab = QWidget()
        obs_layout = QVBoxLayout(obs_tab)
        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setPlaceholderText("Observações adicionais sobre a questão...")
        self.observacoes_edit.setMaximumHeight(150)
        obs_layout.addWidget(self.observacoes_edit)
        tab_widget.addTab(obs_tab, "Observações")

        scroll_layout.addWidget(tab_widget)

        # ========== TAGS ==========
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)

        tags_info = QLabel("Selecione as tags que classificam esta questão:")
        tags_info.setStyleSheet("color: #666; margin-bottom: 5px;")
        tags_layout.addWidget(tags_info)

        self.tag_tree_widget = TagTreeWidget()
        tags_layout.addWidget(self.tag_tree_widget)

        # Carregar tags de exemplo
        self.load_example_tags()

        scroll_layout.addWidget(tags_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # ========== BOTÕES ==========
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_preview = QPushButton("👁️ Preview")
        btn_preview.clicked.connect(self.show_preview)
        btn_layout.addWidget(btn_preview)

        btn_cancel = QPushButton("❌ Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Salvar")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
        """)
        btn_save.clicked.connect(self.save_questao)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def create_alternativa_widget(self, letra):
        """Cria widget de uma alternativa"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)

        # Checkbox para alternativa correta
        checkbox = QCheckBox()
        checkbox.setToolTip("Marque como correta")
        layout.addWidget(checkbox)

        # Letra
        letra_label = QLabel(f"{letra})")
        letra_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        letra_label.setFixedWidth(30)
        layout.addWidget(letra_label)

        # Texto da alternativa
        texto_input = QLineEdit()
        texto_input.setPlaceholderText(f"Digite o texto da alternativa {letra}...")
        layout.addWidget(texto_input)

        # Botão de imagem (opcional)
        btn_image = QPushButton("🖼️")
        btn_image.setMaximumWidth(40)
        btn_image.setToolTip("Adicionar imagem à alternativa")
        layout.addWidget(btn_image)

        # Armazenar referências
        widget.checkbox = checkbox
        widget.letra = letra
        widget.texto_input = texto_input
        widget.btn_image = btn_image
        widget.image_path = None

        return widget

    def setup_connections(self):
        """Configura conexões de sinais"""
        # Ao mudar tipo, mostrar/ocultar alternativas
        self.tipo_objetiva.toggled.connect(self.on_tipo_changed)

    def on_tipo_changed(self, checked):
        """Callback quando tipo de questão muda"""
        is_objetiva = self.tipo_objetiva.isChecked()
        self.alternativas_group.setVisible(is_objetiva)
        logger.info(f"Tipo alterado para: {'Objetiva' if is_objetiva else 'Discursiva'}")

    def load_example_tags(self):
        """Carrega tags de exemplo"""
        # TODO: Buscar tags do banco de dados
        exemplo_tags = [
            {'id': 1, 'nome': 'ÁLGEBRA', 'nivel': 1, 'id_pai': None},
            {'id': 2, 'nome': 'FUNÇÕES', 'nivel': 2, 'id_pai': 1},
            {'id': 3, 'nome': 'FUNÇÃO QUADRÁTICA', 'nivel': 3, 'id_pai': 2},
            {'id': 4, 'nome': 'GEOMETRIA', 'nivel': 1, 'id_pai': None},
            {'id': 5, 'nome': 'GEOMETRIA PLANA', 'nivel': 2, 'id_pai': 4},
        ]
        self.tag_tree_widget.load_tags(exemplo_tags)

    def load_questao(self, questao_id):
        """Carrega dados de uma questão existente"""
        logger.info(f"Carregando questão ID: {questao_id}")
        # TODO: Buscar dados do banco de dados
        # Por enquanto, não faz nada

    def validate_form(self):
        """Validação mínima de UI (apenas campos obrigatórios visuais)

        A validação de regras de negócio é feita pelo ValidationService no Controller
        """
        # Apenas validação básica de UI
        if not self.enunciado_editor.get_text().strip():
            QMessageBox.warning(self, "Validação", "O enunciado é obrigatório!")
            return False

        return True

    def get_form_data(self):
        """Coleta dados do formulário"""
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

        # Coletar alternativas (se objetiva)
        if self.tipo_objetiva.isChecked():
            for widget in self.alternativas_widgets:
                texto = widget.texto_input.text().strip()
                if texto:
                    data['alternativas'].append({
                        'letra': widget.letra,
                        'texto': texto,
                        'correta': widget.checkbox.isChecked(),
                        'imagem': widget.image_path
                    })

        return data

    def save_questao(self):
        """Salva a questão usando o controller"""
        logger.info("Salvando questão")

        # Validação básica de UI
        if not self.validate_form():
            return

        # Coletar dados do formulário
        form_data = self.get_form_data()

        try:
            if self.is_editing:
                # Atualizar questão existente
                self._atualizar_questao(form_data)
            else:
                # Criar nova questão
                self._criar_questao(form_data)

        except Exception as e:
            logger.error(f"Erro ao salvar questão: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao salvar questão:\n{str(e)}"
            )

    def _criar_questao(self, form_data):
        """Cria nova questão via controller"""
        # Converter alternativas para DTOs
        alternativas_dto = []
        for alt in form_data['alternativas']:
            alternativas_dto.append(AlternativaDTO(
                letra=alt['letra'],
                texto=alt['texto'],
                correta=alt.get('correta', False),
                imagem=alt.get('imagem')
            ))

        # Criar DTO de criação
        dto = QuestaoCreateDTO(
            titulo=form_data['titulo'],
            enunciado=form_data['enunciado'],
            tipo=form_data['tipo'],
            ano=form_data['ano'],
            fonte=form_data['fonte'],
            id_dificuldade=form_data['id_dificuldade'],
            resolucao=form_data.get('resolucao'),
            imagem_enunciado=form_data.get('imagem_enunciado'),
            escala_imagem_enunciado=form_data.get('escala_imagem_enunciado'),
            alternativas=alternativas_dto,
            tags=form_data.get('tags', [])
        )

        # Salvar via controller
        id_questao = self.controller.criar_questao_completa(dto)

        if id_questao:
            QMessageBox.information(
                self,
                "Sucesso",
                f"Questão criada com sucesso!\n\nID: {id_questao}"
            )

            # Emitir sinal e fechar
            self.questaoSaved.emit(id_questao)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Falha",
                "Não foi possível criar a questão.\n\n"
                "Verifique os dados e tente novamente.\n"
                "Consulte o log para mais detalhes."
            )

    def _atualizar_questao(self, form_data):
        """Atualiza questão existente via controller"""
        # Converter alternativas para DTOs
        alternativas_dto = []
        for alt in form_data['alternativas']:
            alternativas_dto.append(AlternativaDTO(
                letra=alt['letra'],
                texto=alt['texto'],
                correta=alt.get('correta', False),
                imagem=alt.get('imagem')
            ))

        # Criar DTO de atualização
        dto = QuestaoUpdateDTO(
            id_questao=self.questao_id,
            titulo=form_data['titulo'],
            enunciado=form_data['enunciado'],
            tipo=form_data['tipo'],
            ano=form_data['ano'],
            fonte=form_data['fonte'],
            id_dificuldade=form_data['id_dificuldade'],
            resolucao=form_data.get('resolucao'),
            imagem_enunciado=form_data.get('imagem_enunciado'),
            escala_imagem_enunciado=form_data.get('escala_imagem_enunciado'),
            alternativas=alternativas_dto if alternativas_dto else None,
            tags=form_data.get('tags')
        )

        # Atualizar via controller
        sucesso = self.controller.atualizar_questao_completa(dto)

        if sucesso:
            QMessageBox.information(
                self,
                "Sucesso",
                f"Questão atualizada com sucesso!\n\nID: {self.questao_id}"
            )

            # Emitir sinal e fechar
            self.questaoSaved.emit(self.questao_id)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Falha",
                "Não foi possível atualizar a questão.\n\n"
                "Verifique os dados e tente novamente.\n"
                "Consulte o log para mais detalhes."
            )

    def show_preview(self):
        """Exibe preview da questão"""
        logger.info("Exibindo preview")

        if not self.enunciado_editor.get_text().strip():
            QMessageBox.warning(self, "Preview", "Digite o enunciado primeiro!")
            return

        # TODO: Abrir janela de preview
        QMessageBox.information(
            self,
            "Preview",
            "Preview da questão será exibido aqui"
        )


logger.info("QuestaoForm carregado")
