"""
Page: Questao Form
Formulario de cadastro/edicao de questoes
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QGroupBox, QRadioButton,
    QButtonGroup, QSpinBox, QTextEdit, QTabWidget, QWidget,
    QCheckBox, QMessageBox, QInputDialog, QCompleter
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.views.components.forms.latex_editor import LatexEditor
from src.views.components.forms.tag_tree import TagTreeWidget
from src.views.components.forms.difficulty_selector import DifficultySelector
from src.views.pages.questao_preview_page import QuestaoPreview
from src.views.components.dialogs.image_insert_dialog import ImageInsertDialog
from src.controllers.adapters import criar_questao_controller
from src.controllers.adapters import criar_tag_controller
from src.application.dtos import QuestaoCreateDTO, QuestaoUpdateDTO, AlternativaDTO, TagCreateDTO
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
        tags_header_layout = QHBoxLayout()
        tags_header_layout.addWidget(QLabel("Selecione as tags que classificam esta questao:"))
        tags_header_layout.addStretch()
        btn_criar_tag = QPushButton("+ Criar Tag")
        btn_criar_tag.setToolTip("Criar uma nova tag de conteudo")
        btn_criar_tag.clicked.connect(self.criar_tag_conteudo)
        tags_header_layout.addWidget(btn_criar_tag)
        tags_layout.addLayout(tags_header_layout)
        self.tag_tree_widget = TagTreeWidget()
        tags_layout.addWidget(self.tag_tree_widget)
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
        """Carrega a arvore de tags de conteudo usando o TagController."""
        try:
            tags_arvore = self.tag_controller.obter_arvore_conteudos()
            self.tag_tree_widget.load_tags(tags_arvore)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar as tags")

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
                for tag in tags:
                    tag_uuid = None
                    tag_numeracao = None
                    tag_nome = None

                    if hasattr(tag, 'uuid'):
                        tag_uuid = tag.uuid
                        tag_numeracao = getattr(tag, 'numeracao', '') or ''
                        tag_nome = getattr(tag, 'nome', '') or ''
                    elif isinstance(tag, dict):
                        tag_uuid = tag.get('uuid')
                        tag_numeracao = tag.get('numeracao', '') or ''
                        tag_nome = tag.get('nome', '') or ''

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

                self.tag_tree_widget.set_selected_tags(tag_conteudo_uuids)

        except Exception as e:
            ErrorHandler.handle_exception(self, e, f"Erro ao carregar dados da questao {questao_id}")
            self.close()

    def get_form_data(self) -> dict:
        """Coleta e retorna os dados do formulario em um dicionario."""
        tags = self.tag_tree_widget.get_selected_tag_ids()

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

        tags_conteudo = self.tag_tree_widget.get_selected_content_tags()
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
            content_tags = self.tag_tree_widget.get_selected_content_tags_with_names()
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

    def criar_tag_conteudo(self):
        """Cria uma nova tag de conteudo, permitindo escolher se e raiz ou sub-tag."""
        opcoes = ["Tag Raiz (nova categoria)", "Sub-tag (filha de outra tag)"]
        opcao_escolhida, ok = QInputDialog.getItem(
            self, "Nova Tag de Conteudo",
            "Selecione o tipo de criacao:",
            opcoes, 0, False
        )
        if not ok:
            return

        if opcao_escolhida == opcoes[0]:
            self._criar_tag_raiz()
        else:
            self._criar_subtag()

    def _criar_tag_raiz(self):
        """Cria uma nova tag raiz de conteudo."""
        nome, ok = QInputDialog.getText(
            self, "Nova Tag Raiz",
            "Nome da nova tag de conteudo:"
        )
        if ok and nome.strip():
            self._executar_criacao_tag(nome.strip(), uuid_pai=None)

    def _criar_subtag(self):
        """Cria uma sub-tag, permitindo escolher a tag pai."""
        tags_disponiveis = self._obter_tags_para_pai()

        if not tags_disponiveis:
            QMessageBox.information(
                self, "Aviso",
                "Nao ha tags de conteudo disponiveis para criar sub-tags.\n"
                "Crie primeiro uma tag raiz."
            )
            return

        opcoes = [f"{tag['caminho']}" for tag in tags_disponiveis]

        pai_escolhido, ok = QInputDialog.getItem(
            self, "Selecionar Tag Pai",
            "Selecione a tag pai para a nova sub-tag:",
            opcoes, 0, False
        )
        if not ok:
            return

        idx = opcoes.index(pai_escolhido)
        uuid_pai = tags_disponiveis[idx]['uuid']

        if not self.tag_controller.pode_criar_subtag(uuid_pai):
            QMessageBox.warning(
                self, "Aviso",
                "Esta tag nao permite a criacao de sub-tags."
            )
            return

        nome, ok = QInputDialog.getText(
            self, "Nova Sub-tag",
            f"Nome da nova sub-tag de '{pai_escolhido}':"
        )
        if ok and nome.strip():
            self._executar_criacao_tag(nome.strip(), uuid_pai=uuid_pai)

    def _obter_tags_para_pai(self):
        """Retorna lista de tags de conteudo que podem ser pai."""
        resultado = []
        tree = self.tag_tree_widget.tree

        def _processar_item(item, caminho_pai=""):
            tag_uuid = item.data(0, Qt.ItemDataRole.UserRole)
            numeracao = item.data(0, Qt.ItemDataRole.UserRole + 1) or ""
            nome = item.text(0)

            if not numeracao or not numeracao[0].isdigit():
                return

            caminho = f"{caminho_pai} > {nome}" if caminho_pai else nome

            resultado.append({
                'uuid': tag_uuid,
                'nome': nome,
                'numeracao': numeracao,
                'caminho': caminho
            })

            for i in range(item.childCount()):
                _processar_item(item.child(i), caminho)

        for i in range(tree.topLevelItemCount()):
            _processar_item(tree.topLevelItem(i))

        return resultado

    def _executar_criacao_tag(self, nome: str, uuid_pai: str = None):
        """Executa a criacao da tag e atualiza a arvore."""
        try:
            dto = TagCreateDTO(nome=nome, id_tag_pai=uuid_pai)
            nova_tag = self.tag_controller.criar_tag(dto, tipo='CONTEUDO')
            if nova_tag:
                ErrorHandler.show_success(self, "Sucesso", f"Tag '{nome}' criada com sucesso!")
                self.load_tags_tree()
                if nova_tag.get('uuid'):
                    self.tag_tree_widget.set_selected_tags([nova_tag['uuid']])
        except ValueError as ve:
            QMessageBox.warning(self, "Erro de Validacao", str(ve))
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao criar tag")

    def show_preview(self):
        """Mostra preview da questao com os dados atuais do formulario."""
        try:
            form_data = self.get_form_data()

            fonte_nome = self.fonte_input.text().strip() or None

            dificuldade_id = self.difficulty_selector.get_selected_difficulty()
            dificuldade_map = {1: 'Facil', 2: 'Medio', 3: 'Dificil'}
            dificuldade_nome = dificuldade_map.get(dificuldade_id, 'N/A')

            tags_nomes = []
            content_tags = self.tag_tree_widget.get_selected_content_tags_with_names()
            for uuid, nome in content_tags:
                tags_nomes.append(nome)

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
