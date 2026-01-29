# src/views/components/question/tags_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy, QComboBox, QListWidget, QListWidgetItem,
    QAbstractItemView, QPushButton, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.views.design.constants import Color, Spacing, Typography, Dimensions
from src.views.components.common.inputs import SearchInput
from src.views.components.common.badges import RemovableBadge, Badge
from src.controllers.adapters import criar_tag_controller

class TagsTab(QWidget):
    """
    Tab for managing tags associated with a question.
    Allows selecting discipline and then selecting tags from that discipline.
    """
    tags_changed = pyqtSignal(list) # Emits a list of selected tag UUIDs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tags_tab")
        self.selected_tag_uuids = [] # List to store UUIDs of selected tags
        self.tag_controller = criar_tag_controller()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # 1. Selected Tags (Chips removiveis)
        selected_tags_frame = QFrame(self)
        selected_tags_frame.setObjectName("selected_tags_frame")
        selected_tags_frame.setStyleSheet(f"QFrame#selected_tags_frame {{ border: 1px solid {Color.BORDER_LIGHT}; border-radius: {Dimensions.BORDER_RADIUS_MD}; padding: {Spacing.MD}px; background-color: {Color.LIGHT_BACKGROUND}; }}")
        selected_tags_layout = QVBoxLayout(selected_tags_frame)
        selected_tags_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        selected_tags_layout.setSpacing(Spacing.SM)

        selected_tags_label = QLabel("Tags Selecionadas:", selected_tags_frame)
        selected_tags_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; color: {Color.DARK_TEXT};")
        selected_tags_layout.addWidget(selected_tags_label)

        self.selected_tags_flow_layout = QHBoxLayout() # For flowing removable badges
        self.selected_tags_flow_layout.setContentsMargins(0,0,0,0)
        self.selected_tags_flow_layout.setSpacing(Spacing.SM)
        self.selected_tags_flow_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        selected_tags_layout.addLayout(self.selected_tags_flow_layout)

        selected_tags_layout.addStretch() # Push tags to the top left
        main_layout.addWidget(selected_tags_frame)

        # 2. Disciplina Selection
        disciplina_frame = QFrame(self)
        disciplina_frame.setObjectName("disciplina_frame")
        disciplina_frame.setStyleSheet(f"QFrame#disciplina_frame {{ border: 1px solid {Color.BORDER_LIGHT}; border-radius: {Dimensions.BORDER_RADIUS_MD}; padding: {Spacing.MD}px; }}")
        disciplina_layout = QVBoxLayout(disciplina_frame)
        disciplina_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        disciplina_layout.setSpacing(Spacing.SM)

        disciplina_label = QLabel("Disciplina:", disciplina_frame)
        disciplina_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; color: {Color.DARK_TEXT};")
        disciplina_layout.addWidget(disciplina_label)

        self.disciplina_combo = QComboBox(disciplina_frame)
        self.disciplina_combo.addItem("Selecione a disciplina...", None)
        self.disciplina_combo.setMinimumWidth(300)
        self.disciplina_combo.setStyleSheet(f"""
            QComboBox {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                background-color: {Color.WHITE};
                font-size: {Typography.FONT_SIZE_MD};
            }}
            QComboBox:hover {{
                border-color: {Color.PRIMARY_BLUE};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: {Spacing.SM}px;
            }}
        """)
        self.disciplina_combo.currentIndexChanged.connect(self._on_disciplina_changed)
        disciplina_layout.addWidget(self.disciplina_combo)

        main_layout.addWidget(disciplina_frame)

        # 3. Tags Selection (Multi-select list)
        tags_frame = QFrame(self)
        tags_frame.setObjectName("tags_frame")
        tags_frame.setStyleSheet(f"QFrame#tags_frame {{ border: 1px solid {Color.BORDER_LIGHT}; border-radius: {Dimensions.BORDER_RADIUS_MD}; padding: {Spacing.MD}px; }}")
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        tags_layout.setSpacing(Spacing.SM)

        # Header com label e botao de criar tag
        tags_header_layout = QHBoxLayout()
        tags_label = QLabel("Conteudos/Tags (selecione um ou mais):", tags_frame)
        tags_label.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; color: {Color.DARK_TEXT};")
        tags_header_layout.addWidget(tags_label)
        tags_header_layout.addStretch()

        self.btn_criar_tag = QPushButton("+ Criar Tag", tags_frame)
        self.btn_criar_tag.setToolTip("Criar uma nova tag de conteudo para a disciplina selecionada")
        self.btn_criar_tag.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.PRIMARY_BLUE};
                color: white;
                border: none;
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
            QPushButton:disabled {{
                background-color: {Color.GRAY_TEXT};
            }}
        """)
        self.btn_criar_tag.setEnabled(False)  # Desabilitado ate selecionar disciplina
        self.btn_criar_tag.clicked.connect(self._on_criar_tag_clicked)
        tags_header_layout.addWidget(self.btn_criar_tag)
        tags_layout.addLayout(tags_header_layout)

        self.tags_list = QListWidget(tags_frame)
        self.tags_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tags_list.setMinimumHeight(200)
        self.tags_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                background-color: {Color.WHITE};
                font-size: {Typography.FONT_SIZE_MD};
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px;
                border-bottom: 1px solid {Color.BORDER_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {Color.PRIMARY_BLUE};
                color: {Color.WHITE};
            }}
            QListWidget::item:hover {{
                background-color: {Color.LIGHT_BACKGROUND};
            }}
        """)
        self.tags_list.itemSelectionChanged.connect(self._on_tags_selection_changed)
        tags_layout.addWidget(self.tags_list)

        # Placeholder message when no discipline selected
        self.no_discipline_label = QLabel("Selecione uma disciplina para ver os conteudos disponiveis.", tags_frame)
        self.no_discipline_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-style: italic; padding: {Spacing.MD}px;")
        self.no_discipline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tags_layout.addWidget(self.no_discipline_label)

        main_layout.addWidget(tags_frame, 1) # Occupy remaining space

        self.setLayout(main_layout)

        # Load disciplines from database
        self._load_disciplinas()

    def _load_disciplinas(self):
        """Carrega as disciplinas no dropdown."""
        try:
            disciplinas = self.tag_controller.listar_disciplinas()
            for disc in disciplinas:
                self.disciplina_combo.addItem(disc['texto'], disc['uuid'])
        except Exception as e:
            print(f"Erro ao carregar disciplinas: {e}")

    def _on_disciplina_changed(self, index):
        """Atualiza a lista de tags quando a disciplina muda."""
        self.tags_list.clear()
        uuid_disciplina = self.disciplina_combo.currentData()

        if not uuid_disciplina:
            self.tags_list.setVisible(False)
            self.no_discipline_label.setVisible(True)
            self.btn_criar_tag.setEnabled(False)
            return

        self.tags_list.setVisible(True)
        self.no_discipline_label.setVisible(False)
        self.btn_criar_tag.setEnabled(True)

        try:
            tags = self.tag_controller.listar_tags_por_disciplina(uuid_disciplina)
            for tag in tags:
                display_text = tag.get('caminho_completo') or tag.get('nome', '')
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, tag['uuid'])
                item.setData(Qt.ItemDataRole.UserRole + 1, tag['nome'])
                self.tags_list.addItem(item)

                # Se esta tag ja estava selecionada, manter a selecao
                if tag['uuid'] in self.selected_tag_uuids:
                    item.setSelected(True)
        except Exception as e:
            print(f"Erro ao carregar tags da disciplina: {e}")

    def _on_criar_tag_clicked(self):
        """Handler para criar uma nova tag."""
        uuid_disciplina = self.disciplina_combo.currentData()
        if not uuid_disciplina:
            QMessageBox.warning(self, "Aviso", "Selecione uma disciplina antes de criar uma tag.")
            return

        # Perguntar tipo de criacao
        opcoes = ["Tag Raiz (nova categoria)", "Sub-tag (filha de outra tag)"]
        opcao_escolhida, ok = QInputDialog.getItem(
            self, "Nova Tag de Conteudo",
            "Selecione o tipo de criacao:",
            opcoes, 0, False
        )
        if not ok:
            return

        if opcao_escolhida == opcoes[0]:
            self._criar_tag_raiz(uuid_disciplina)
        else:
            self._criar_subtag(uuid_disciplina)

    def _criar_tag_raiz(self, uuid_disciplina: str):
        """Cria uma nova tag raiz de conteudo."""
        nome, ok = QInputDialog.getText(
            self, "Nova Tag Raiz",
            "Nome da nova tag de conteudo:"
        )
        if ok and nome.strip():
            self._executar_criacao_tag(nome.strip(), uuid_pai=None, uuid_disciplina=uuid_disciplina)

    def _criar_subtag(self, uuid_disciplina: str):
        """Cria uma sub-tag, permitindo escolher a tag pai."""
        # Obter tags disponiveis como pai
        tags_disponiveis = []
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            tag_uuid = item.data(Qt.ItemDataRole.UserRole)
            tag_nome = item.data(Qt.ItemDataRole.UserRole + 1)
            display_text = item.text()
            tags_disponiveis.append({
                'uuid': tag_uuid,
                'nome': tag_nome,
                'display': display_text
            })

        if not tags_disponiveis:
            QMessageBox.information(
                self, "Aviso",
                "Nao ha tags de conteudo disponiveis para criar sub-tags.\n"
                "Crie primeiro uma tag raiz."
            )
            return

        opcoes = [tag['display'] for tag in tags_disponiveis]

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
            f"Nome da nova sub-tag de '{tags_disponiveis[idx]['nome']}':"
        )
        if ok and nome.strip():
            self._executar_criacao_tag(nome.strip(), uuid_pai=uuid_pai, uuid_disciplina=uuid_disciplina)

    def _executar_criacao_tag(self, nome: str, uuid_pai: str = None, uuid_disciplina: str = None):
        """Executa a criacao da tag e atualiza a lista."""
        try:
            from src.application.dtos import TagCreateDTO
            dto = TagCreateDTO(nome=nome, id_tag_pai=uuid_pai)
            # Passar uuid_disciplina para associar a tag a disciplina
            nova_tag = self.tag_controller.criar_tag(dto, tipo='CONTEUDO', uuid_disciplina=uuid_disciplina)
            if nova_tag:
                QMessageBox.information(self, "Sucesso", f"Tag '{nome}' criada com sucesso!")
                # Recarregar lista de tags da disciplina atual
                self._recarregar_tags_disciplina()
                # Selecionar a nova tag
                if nova_tag.get('uuid'):
                    for i in range(self.tags_list.count()):
                        item = self.tags_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) == nova_tag['uuid']:
                            item.setSelected(True)
                            break
        except ValueError as ve:
            QMessageBox.warning(self, "Erro de Validacao", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar tag: {str(e)}")

    def _recarregar_tags_disciplina(self):
        """Recarrega a lista de tags da disciplina selecionada."""
        uuid_disciplina = self.disciplina_combo.currentData()
        if not uuid_disciplina:
            return

        # Guardar selecoes atuais
        selecoes_atuais = self.selected_tag_uuids.copy()

        # Limpar lista
        self.tags_list.clear()

        try:
            tags = self.tag_controller.listar_tags_por_disciplina(uuid_disciplina)
            for tag in tags:
                display_text = tag.get('caminho_completo') or tag.get('nome', '')
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, tag['uuid'])
                item.setData(Qt.ItemDataRole.UserRole + 1, tag['nome'])
                self.tags_list.addItem(item)

                # Restaurar selecao se estava selecionada
                if tag['uuid'] in selecoes_atuais:
                    item.setSelected(True)
        except Exception as e:
            print(f"Erro ao recarregar tags da disciplina: {e}")

    def _on_tags_selection_changed(self):
        """Handler quando a selecao de tags muda na lista."""
        # Obter UUIDs selecionados da lista atual
        current_selection = []
        for item in self.tags_list.selectedItems():
            uuid = item.data(Qt.ItemDataRole.UserRole)
            if uuid:
                current_selection.append(uuid)

        # Atualizar lista interna (manter tags de outras disciplinas + adicionar novas)
        # Primeiro, remover tags da disciplina atual que nao estao mais selecionadas
        tags_da_disciplina_atual = []
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            uuid = item.data(Qt.ItemDataRole.UserRole)
            if uuid:
                tags_da_disciplina_atual.append(uuid)

        # Remover da selecao geral as tags desta disciplina que foram desmarcadas
        self.selected_tag_uuids = [
            uuid for uuid in self.selected_tag_uuids
            if uuid not in tags_da_disciplina_atual or uuid in current_selection
        ]

        # Adicionar as novas selecoes
        for uuid in current_selection:
            if uuid not in self.selected_tag_uuids:
                self.selected_tag_uuids.append(uuid)

        # Atualizar badges visuais
        self._update_selected_badges()

        # Emitir sinal
        self.tags_changed.emit(self.selected_tag_uuids)

    def _update_selected_badges(self):
        """Atualiza os badges visuais com base nas tags selecionadas."""
        # Limpar badges existentes
        while self.selected_tags_flow_layout.count():
            item = self.selected_tags_flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Obter nomes das tags selecionadas
        selected_tags_with_names = []
        for item in self.tags_list.selectedItems():
            tag_uuid = item.data(Qt.ItemDataRole.UserRole)
            tag_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if tag_uuid and tag_name:
                selected_tags_with_names.append((tag_uuid, tag_name))

        # Cores de fundo para as tags (cores claras)
        bg_colors = ['#dbeafe', '#dcfce7', '#f3e8ff', '#ffedd5', '#fee2e2', '#fef9c3']

        for i, (tag_uuid, tag_name) in enumerate(selected_tags_with_names):
            bg_color = bg_colors[i % len(bg_colors)]
            # Usar texto preto para melhor visibilidade
            badge = RemovableBadge(tag_name, color=bg_color, text_color="#000000", parent=self)
            badge.tag_uuid = tag_uuid
            badge.removed.connect(self._on_removable_badge_removed)
            self.selected_tags_flow_layout.addWidget(badge)

    def _on_removable_badge_removed(self, tag_name: str):
        """Handler quando um badge e removido pelo usuario."""
        # Encontrar o UUID pelo nome e desmarcar na lista
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole + 1) == tag_name:
                item.setSelected(False)
                break

    def get_selected_tag_ids(self):
        """Retorna lista de UUIDs das tags selecionadas."""
        return self.selected_tag_uuids.copy()

    def get_selected_content_tags_with_names(self):
        """Retorna lista de tuplas (uuid, nome) das tags selecionadas."""
        result = []
        for item in self.tags_list.selectedItems():
            tag_uuid = item.data(Qt.ItemDataRole.UserRole)
            tag_name = item.data(Qt.ItemDataRole.UserRole + 1)
            if tag_uuid and tag_name:
                result.append((tag_uuid, tag_name))
        return result

    def set_selected_tags(self, tag_uuids: list):
        """Define as tags selecionadas por lista de UUIDs."""
        self.selected_tag_uuids = tag_uuids.copy()
        # Atualizar selecao na lista
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            uuid = item.data(Qt.ItemDataRole.UserRole)
            item.setSelected(uuid in tag_uuids)
        self._update_selected_badges()

    def clear_selection(self):
        """Limpa todas as selecoes."""
        self.selected_tag_uuids = []
        self.tags_list.clearSelection()
        self._update_selected_badges()
        self.tags_changed.emit([])


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from src.views.design.theme import ThemeManager
    ThemeManager.apply_global_theme(app)

    class TestMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Tags Tab Test")
            self.setGeometry(100, 100, 800, 900)

            self.tags_tab = TagsTab(self)
            self.setCentralWidget(self.tags_tab)

            self.tags_tab.tags_changed.connect(lambda tags: print(f"Selected Tags UUIDs: {tags}"))

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
