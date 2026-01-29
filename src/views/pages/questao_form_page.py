"""
Page: Questao Form
Formulario de cadastro/edicao de questoes
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QGroupBox, QRadioButton,
    QButtonGroup, QSpinBox, QTextEdit, QTabWidget, QWidget,
    QCheckBox, QMessageBox, QInputDialog, QCompleter, QListWidget,
    QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.views.components.forms.latex_editor import LatexEditor
from src.views.components.forms.difficulty_selector import DifficultySelector
from src.views.pages.questao_preview_page import QuestaoPreview
from src.views.components.dialogs.image_insert_dialog import ImageInsertDialog
from src.controllers.adapters import criar_questao_controller
from src.controllers.adapters import criar_tag_controller
from src.application.dtos import QuestaoCreateDTO, QuestaoUpdateDTO, AlternativaDTO
from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class QuestaoFormPage(QDialog):
    """
    Formulario para criar/editar questoes.
    Suporta questoes objetivas e discursivas.
    """
    questaoSaved = pyqtSignal(object)

    def __init__(self, questao_id=None, parent=None):
        super().__init__(parent)
        self.questao_id = questao_id
        self.is_editing = questao_id is not None

        # Inicializar controllers
        self.controller = criar_questao_controller()
        self.tag_controller = criar_tag_controller()

        self.setWindowTitle("Editar Questao" if self.is_editing else "Nova Questao")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.init_ui()
        self.setup_connections()
        self.load_fontes()
        self.load_series()
        self.load_tags_tree()

        if self.is_editing:
            self.load_questao_data(questao_id)

        logger.info(f"QuestaoFormPage inicializado (ID: {questao_id})")

    def init_ui(self):
        layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        title_label = QLabel("Nova Questao" if not self.is_editing else "Editar Questao")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Informacoes Basicas
        info_group = QGroupBox("Informacoes Basicas")
        info_layout = QVBoxLayout(info_group)
        titulo_layout = QHBoxLayout()
        titulo_layout.addWidget(QLabel("Titulo (opcional):"))
        self.titulo_input = QLineEdit()
        self.titulo_input.setPlaceholderText("Ex: Funcao Quadratica - Vertice da Parabola")
        titulo_layout.addWidget(self.titulo_input)
        info_layout.addLayout(titulo_layout)
        meta_layout = QHBoxLayout()
        meta_layout.addWidget(QLabel("Ano:"))
        self.ano_spin = QSpinBox()
        self.ano_spin.setRange(1900, 2100)
        self.ano_spin.setValue(2026)
        meta_layout.addWidget(self.ano_spin)
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

        # Segunda linha: Fonte, Serie, Dificuldade
        meta_layout2 = QHBoxLayout()
        meta_layout2.addWidget(QLabel("Fonte/Banca:"))
        self.fonte_input = QLineEdit()
        self.fonte_input.setPlaceholderText("Ex: ENEM, FUVEST, UNICAMP...")
        self.fonte_input.setToolTip("Digite a fonte/banca. Se nao existir, sera criada automaticamente.")
        meta_layout2.addWidget(self.fonte_input)
        meta_layout2.addWidget(QLabel("Serie/Nivel:"))
        self.serie_combo = QComboBox()
        self.serie_combo.addItem("Selecione...", None)
        meta_layout2.addWidget(self.serie_combo)
        meta_layout2.addStretch()
        info_layout.addLayout(meta_layout2)

        self.difficulty_selector = DifficultySelector()
        info_layout.addWidget(self.difficulty_selector)
        scroll_layout.addWidget(info_group)

        # Enunciado
        enunciado_group = QGroupBox("Enunciado")
        enunciado_layout = QVBoxLayout(enunciado_group)
        self.enunciado_editor = LatexEditor("Digite o enunciado da questao...")
        enunciado_layout.addWidget(self.enunciado_editor)
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

        # Abas de Resolucao, Gabarito, etc.
        tab_widget = QTabWidget()
        resolucao_tab = QWidget()
        resolucao_layout = QVBoxLayout(resolucao_tab)
        self.resolucao_editor = LatexEditor("Digite a resolucao detalhada (opcional)...")
        resolucao_layout.addWidget(self.resolucao_editor)
        tab_widget.addTab(resolucao_tab, "Resolucao")
        gabarito_tab = QWidget()
        gabarito_layout = QVBoxLayout(gabarito_tab)
        gabarito_layout.addWidget(QLabel("Para questoes discursivas, descreva o gabarito esperado:"))
        self.gabarito_editor = LatexEditor("Digite o gabarito para questoes discursivas...")
        gabarito_layout.addWidget(self.gabarito_editor)
        tab_widget.addTab(gabarito_tab, "Gabarito Discursiva")
        obs_tab = QWidget()
        obs_layout = QVBoxLayout(obs_tab)
        self.observacoes_edit = QTextEdit()
        self.observacoes_edit.setPlaceholderText("Observacoes adicionais sobre a questao...")
        obs_layout.addWidget(self.observacoes_edit)
        tab_widget.addTab(obs_tab, "Observacoes")
        scroll_layout.addWidget(tab_widget)

        # Tags
        tags_group = QGroupBox("Tags de Conteudo")
        tags_layout = QVBoxLayout(tags_group)

        # Dropdown de Disciplina
        disciplina_layout = QHBoxLayout()
        disciplina_layout.addWidget(QLabel("Disciplina:"))
        self.disciplina_combo = QComboBox()
        self.disciplina_combo.addItem("Selecione a disciplina...", None)
        self.disciplina_combo.setMinimumWidth(250)
        self.disciplina_combo.currentIndexChanged.connect(self.on_disciplina_changed)
        disciplina_layout.addWidget(self.disciplina_combo)
        disciplina_layout.addStretch()
        tags_layout.addLayout(disciplina_layout)

        # Dropdown de Tags (multiselect via QListWidget)
        tags_select_layout = QVBoxLayout()
        tags_select_layout.addWidget(QLabel("Conteudos/Tags (selecione um ou mais):"))
        self.tags_list = QListWidget()
        self.tags_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tags_list.setMinimumHeight(150)
        self.tags_list.setMaximumHeight(200)
        tags_select_layout.addWidget(self.tags_list)
        tags_layout.addLayout(tags_select_layout)

        # Tags selecionadas (exibição)
        self.selected_tags_label = QLabel("Tags selecionadas: Nenhuma")
        self.selected_tags_label.setWordWrap(True)
        self.selected_tags_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        tags_layout.addWidget(self.selected_tags_label)
        self.tags_list.itemSelectionChanged.connect(self.on_tags_selection_changed)

        scroll_layout.addWidget(tags_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Botoes
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_preview = QPushButton("Preview")
        btn_preview.clicked.connect(self.show_preview)
        btn_layout.addWidget(btn_preview)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_save = QPushButton("Salvar")
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
        btn_image = QPushButton("IMG")
        btn_image.setMaximumWidth(40)
        btn_image.setToolTip("Adicionar imagem a alternativa")
        btn_image.clicked.connect(lambda checked, ti=texto_input: self._inserir_imagem_alternativa(ti))
        layout.addWidget(btn_image)
        widget.checkbox = checkbox
        widget.letra = letra
        widget.texto_input = texto_input
        widget.btn_image = btn_image
        widget.image_path = None
        return widget

    def _inserir_imagem_alternativa(self, texto_input: QLineEdit):
        """Insere uma imagem no texto da alternativa."""
        dialog = ImageInsertDialog(self)
        if dialog.exec():
            caminho = dialog.get_image_path()
            escala = dialog.get_scale()
            if caminho:
                placeholder = f"[IMG:{caminho}:{escala}]"
                texto_atual = texto_input.text()
                cursor_pos = texto_input.cursorPosition()
                novo_texto = texto_atual[:cursor_pos] + placeholder + texto_atual[cursor_pos:]
                texto_input.setText(novo_texto)

    def setup_connections(self):
        self.tipo_objetiva.toggled.connect(self.on_tipo_changed)

    def on_tipo_changed(self, checked):
        is_objetiva = self.tipo_objetiva.isChecked()
        self.alternativas_group.setVisible(is_objetiva)

    def load_fontes(self):
        """Configura autocomplete para o campo fonte com as fontes existentes."""
        try:
            vestibulares = self.tag_controller.listar_vestibulares()
            nomes = [vest['nome'] for vest in vestibulares]
            completer = QCompleter(nomes, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.fonte_input.setCompleter(completer)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar fontes/vestibulares")

    def load_series(self):
        """Carrega as series/niveis no dropdown."""
        try:
            series = self.tag_controller.listar_series()
            for serie in series:
                self.serie_combo.addItem(serie['nome'], serie['uuid'])
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar series")

    def load_tags_tree(self):
        """Carrega as disciplinas no dropdown."""
        try:
            disciplinas = self.tag_controller.listar_disciplinas()
            for disc in disciplinas:
                self.disciplina_combo.addItem(disc['texto'], disc['uuid'])
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar disciplinas")

    def on_disciplina_changed(self, index):
        """Atualiza a lista de tags quando a disciplina muda."""
        self.tags_list.clear()
        uuid_disciplina = self.disciplina_combo.currentData()

        if not uuid_disciplina:
            return

        try:
            tags = self.tag_controller.listar_tags_por_disciplina(uuid_disciplina)
            for tag in tags:
                item = QListWidgetItem(tag['caminho_completo'] or tag['nome'])
                item.setData(Qt.ItemDataRole.UserRole, tag['uuid'])
                item.setData(Qt.ItemDataRole.UserRole + 1, tag['nome'])
                self.tags_list.addItem(item)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar tags da disciplina")

    def on_tags_selection_changed(self):
        """Atualiza o label com as tags selecionadas."""
        selected_items = self.tags_list.selectedItems()
        if selected_items:
            nomes = [item.data(Qt.ItemDataRole.UserRole + 1) for item in selected_items]
            self.selected_tags_label.setText(f"Tags selecionadas: {', '.join(nomes)}")
            self.selected_tags_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.selected_tags_label.setText("Tags selecionadas: Nenhuma")
            self.selected_tags_label.setStyleSheet("color: #7f8c8d; font-style: italic;")

    def load_questao_data(self, questao_id):
        """Carrega os dados de uma questao existente para edicao."""
        logger.info(f"Carregando dados da questao ID: {questao_id} para edicao.")
        try:
            dto = self.controller.obter_questao_completa(questao_id)
            if not dto:
                QMessageBox.critical(self, "Erro", "Nao foi possivel carregar a questao.")
                self.close()
                return

            self.titulo_input.setText(getattr(dto, 'titulo', '') or "")
            self.ano_spin.setValue(getattr(dto, 'ano', 2026) or 2026)

            dificuldade = getattr(dto, 'dificuldade', None)
            dificuldade_map = {'FACIL': 1, 'MEDIO': 2, 'DIFICIL': 3}
            id_dificuldade = dificuldade_map.get(dificuldade, 0)
            if id_dificuldade:
                self.difficulty_selector.set_difficulty(id_dificuldade)

            self.enunciado_editor.set_text(getattr(dto, 'enunciado', '') or '')
            self.resolucao_editor.set_text(getattr(dto, 'resolucao', '') or "")
            self.observacoes_edit.setPlainText(getattr(dto, 'observacoes', '') or "")

            tipo = getattr(dto, 'tipo', 'OBJETIVA')
            if tipo == 'OBJETIVA':
                self.tipo_objetiva.setChecked(True)
                alternativas = getattr(dto, 'alternativas', [])
                if alternativas:
                    for i, alt_dto in enumerate(alternativas):
                        if i < len(self.alternativas_widgets):
                            alt_widget = self.alternativas_widgets[i]
                            texto = getattr(alt_dto, 'texto', '') if hasattr(alt_dto, 'texto') else alt_dto.get('texto', '')
                            correta = getattr(alt_dto, 'correta', False) if hasattr(alt_dto, 'correta') else alt_dto.get('correta', False)
                            alt_widget.texto_input.setText(texto)
                            alt_widget.checkbox.setChecked(correta)
            else:
                self.tipo_discursiva.setChecked(True)

            tags = getattr(dto, 'tags', [])
            if tags:
                tag_conteudo_uuids = []
                uuid_disciplina_encontrada = None
                for tag in tags:
                    tag_uuid = None
                    tag_numeracao = None
                    tag_nome = None
                    tag_disciplina = None

                    if hasattr(tag, 'uuid'):
                        tag_uuid = tag.uuid
                        tag_numeracao = getattr(tag, 'numeracao', '') or ''
                        tag_nome = getattr(tag, 'nome', '') or ''
                        tag_disciplina = getattr(tag, 'uuid_disciplina', None)
                    elif isinstance(tag, dict):
                        tag_uuid = tag.get('uuid')
                        tag_numeracao = tag.get('numeracao', '') or ''
                        tag_nome = tag.get('nome', '') or ''
                        tag_disciplina = tag.get('uuid_disciplina')

                    if not tag_uuid:
                        continue

                    if tag_numeracao.startswith('V'):
                        if tag_nome:
                            self.fonte_input.setText(tag_nome)
                    elif tag_numeracao.startswith('N'):
                        idx = self.serie_combo.findData(tag_uuid)
                        if idx >= 0:
                            self.serie_combo.setCurrentIndex(idx)
                    else:
                        tag_conteudo_uuids.append(tag_uuid)
                        if tag_disciplina and not uuid_disciplina_encontrada:
                            uuid_disciplina_encontrada = tag_disciplina

                # Selecionar disciplina se encontrada
                if uuid_disciplina_encontrada:
                    idx = self.disciplina_combo.findData(uuid_disciplina_encontrada)
                    if idx >= 0:
                        self.disciplina_combo.setCurrentIndex(idx)

                # Selecionar as tags na lista
                for i in range(self.tags_list.count()):
                    item = self.tags_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) in tag_conteudo_uuids:
                        item.setSelected(True)

        except Exception as e:
            ErrorHandler.handle_exception(self, e, f"Erro ao carregar dados da questao {questao_id}")
            self.close()

    def get_form_data(self) -> dict:
        """Coleta e retorna os dados do formulario em um dicionario."""
        tags = [item.data(Qt.ItemDataRole.UserRole) for item in self.tags_list.selectedItems()]

        fonte_uuid = self._obter_ou_criar_fonte_tag()
        if fonte_uuid:
            tags.append(fonte_uuid)

        serie_uuid = self.serie_combo.currentData()
        if serie_uuid:
            tags.append(serie_uuid)

        data = {
            'titulo': self.titulo_input.text().strip() or None,
            'enunciado': self.enunciado_editor.get_text(),
            'tipo': 'OBJETIVA' if self.tipo_objetiva.isChecked() else 'DISCURSIVA',
            'ano': self.ano_spin.value(),
            'fonte': None,
            'id_dificuldade': self.difficulty_selector.get_selected_difficulty(),
            'resolucao': self.resolucao_editor.get_text() or None,
            'gabarito_discursiva': self.gabarito_editor.get_text() or None,
            'observacoes': self.observacoes_edit.toPlainText().strip() or None,
            'tags': tags,
            'alternativas': []
        }
        if data['tipo'] == 'OBJETIVA':
            for widget in self.alternativas_widgets:
                data['alternativas'].append({
                    'letra': widget.letra,
                    'texto': widget.texto_input.text().strip(),
                    'correta': widget.checkbox.isChecked(),
                    'uuid_imagem': widget.image_path
                })
        return data

    def _obter_ou_criar_fonte_tag(self) -> str:
        """Obtem o UUID da tag de fonte, criando-a se nao existir."""
        from src.application.dtos import TagCreateDTO

        fonte_texto = self.fonte_input.text().strip()
        if not fonte_texto:
            return None

        fonte_texto = fonte_texto.upper()

        tag_existente = self.tag_controller.buscar_por_nome(fonte_texto)
        if tag_existente:
            return tag_existente.get('uuid')

        try:
            dto = TagCreateDTO(nome=fonte_texto, id_tag_pai=None)
            nova_tag = self.tag_controller.criar_tag(dto, tipo='VESTIBULAR')
            if nova_tag:
                logger.info(f"Tag de fonte '{fonte_texto}' criada automaticamente")
                self.load_fontes()
                return nova_tag.get('uuid')
        except Exception as e:
            logger.error(f"Erro ao criar tag de fonte '{fonte_texto}': {e}")

        return None

    def validar_formulario(self, form_data: dict) -> tuple:
        """Valida os dados do formulario antes de salvar."""
        if not form_data.get('enunciado', '').strip():
            return False, "O enunciado da questao e obrigatorio."

        if not self.fonte_input.text().strip():
            return False, "E necessario informar uma fonte/banca para a questao."

        tags_conteudo = self.tags_list.selectedItems()
        if not tags_conteudo:
            return False, "E necessario selecionar pelo menos uma tag de conteudo (assunto)."

        if form_data.get('tipo') == 'OBJETIVA':
            alternativas = form_data.get('alternativas', [])

            alternativas_vazias = []
            for alt in alternativas:
                if not alt.get('texto', '').strip():
                    alternativas_vazias.append(alt.get('letra'))

            if alternativas_vazias:
                letras = ', '.join(alternativas_vazias)
                return False, f"Todas as 5 alternativas devem ser preenchidas.\nAlternativas vazias: {letras}"

            alternativas_corretas = [alt for alt in alternativas if alt.get('correta')]
            if len(alternativas_corretas) == 0:
                return False, "E necessario marcar uma alternativa como correta."
            elif len(alternativas_corretas) > 1:
                letras = ', '.join([alt.get('letra') for alt in alternativas_corretas])
                return False, f"Apenas uma alternativa pode ser marcada como correta.\nMarcadas: {letras}"

        return True, ""

    def save_questao(self):
        """Valida e salva a questao (criacao ou atualizacao)."""
        logger.info("Tentando salvar a questao...")
        form_data = self.get_form_data()

        valido, erro = self.validar_formulario(form_data)
        if not valido:
            QMessageBox.warning(self, "Validacao", erro)
            return

        titulo = form_data.get('titulo')
        if not titulo or not titulo.strip():
            content_tags = [(item.data(Qt.ItemDataRole.UserRole), item.data(Qt.ItemDataRole.UserRole + 1)) for item in self.tags_list.selectedItems()]
            if len(content_tags) > 1:
                nomes = [nome for _, nome in content_tags]
                escolhido, ok = QInputDialog.getItem(
                    self,
                    "Conteudo Principal",
                    "A questao possui multiplos conteudos.\nSelecione o conteudo principal para o titulo:",
                    nomes,
                    0,
                    False
                )
                if not ok:
                    return

                idx_principal = nomes.index(escolhido)
                uuid_principal = content_tags[idx_principal][0]

                tags = form_data['tags']
                if uuid_principal in tags:
                    tags.remove(uuid_principal)
                    tags.insert(0, uuid_principal)

        campos_extras = ['resolucao', 'gabarito_discursiva']
        extras = {k: form_data.pop(k, None) for k in campos_extras}

        try:
            if self.is_editing:
                dto = QuestaoUpdateDTO(id_questao=self.questao_id, **form_data)
                sucesso = self.controller.atualizar_questao_completa(dto)
                msg = f"Questao {self.questao_id} atualizada com sucesso!"
                codigo_questao = self.questao_id
            else:
                alternativas_dto = [AlternativaDTO(**alt) for alt in form_data.pop('alternativas')]
                dto = QuestaoCreateDTO(alternativas=alternativas_dto, **form_data)
                resultado = self.controller.criar_questao_completa(dto)
                sucesso = resultado is not None
                codigo_questao = resultado.get('codigo') if isinstance(resultado, dict) else resultado
                msg = f"Questao criada com sucesso! Codigo: {codigo_questao}"

            if sucesso:
                ErrorHandler.show_success(self, "Sucesso", msg)
                self.questaoSaved.emit(codigo_questao)
                self.accept()
            else:
                ErrorHandler.show_warning(self, "Falha", "Nao foi possivel salvar a questao.")

        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao salvar questao")


    def show_preview(self):
        """Mostra preview da questao com os dados atuais do formulario."""
        try:
            form_data = self.get_form_data()

            fonte_nome = self.fonte_input.text().strip() or None

            dificuldade_id = self.difficulty_selector.get_selected_difficulty()
            dificuldade_map = {1: 'Facil', 2: 'Medio', 3: 'Dificil'}
            dificuldade_nome = dificuldade_map.get(dificuldade_id, 'N/A')

            tags_nomes = []
            for item in self.tags_list.selectedItems():
                tags_nomes.append(item.data(Qt.ItemDataRole.UserRole + 1))

            preview_data = {
                'id': self.questao_id,
                'titulo': form_data.get('titulo') or 'Sem titulo',
                'tipo': form_data.get('tipo'),
                'enunciado': form_data.get('enunciado'),
                'fonte': fonte_nome,
                'ano': form_data.get('ano'),
                'dificuldade': dificuldade_nome,
                'resolucao': self.resolucao_editor.get_text() or None,
                'tags': tags_nomes,
                'alternativas': []
            }

            if form_data.get('tipo') == 'OBJETIVA':
                for alt in form_data.get('alternativas', []):
                    preview_data['alternativas'].append({
                        'letra': alt.get('letra'),
                        'texto': alt.get('texto'),
                        'correta': alt.get('correta', False)
                    })

            preview_dialog = QuestaoPreview(preview_data, self)
            preview_dialog.exec()

        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao gerar preview")


# Alias para compatibilidade
QuestaoForm = QuestaoFormPage
