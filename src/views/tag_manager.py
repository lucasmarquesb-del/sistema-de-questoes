"""
View: Tag Manager
DESCRIÇÃO: Interface de gerenciamento de tags
RELACIONAMENTOS: TagController
COMPONENTES:
    - Árvore hierárquica de tags
    - Botões: Nova Tag, Editar, Inativar, Reativar
    - Drag-and-drop para reorganizar (opcional)
    - Contador de questões por tag
    - Validação de nomes duplicados
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QGroupBox, QInputDialog
)
from PyQt6.QtCore import Qt
import logging
from typing import List

from src.utils import ErrorHandler
from src.controllers.adapters import criar_tag_controller
from src.application.dtos.tag_dto import TagCreateDTO, TagUpdateDTO, TagResponseDTO

logger = logging.getLogger(__name__)


class TagManager(QDialog):
    """
    Gerenciador de tags hierárquicas.
    Permite criar, editar e organizar tags.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Tags")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # Injeção de dependência
        self.controller = criar_tag_controller()

        self.init_ui()
        self.load_tags()

        logger.info("TagManager inicializado")

    def init_ui(self):
        """Configura a interface"""
        layout = QVBoxLayout(self)

        header = QLabel("🏷️ Gerenciamento de Tags Hierárquicas")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        main_layout = QHBoxLayout()
        tree_group = QGroupBox("Tags Existentes")
        tree_layout = QVBoxLayout(tree_group)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nome", "Numeração"])
        self.tree.setColumnWidth(0, 350)
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        tree_layout.addWidget(self.tree)

        expand_layout = QHBoxLayout()
        btn_expand = QPushButton("Expandir Tudo")
        btn_expand.clicked.connect(self.tree.expandAll)
        expand_layout.addWidget(btn_expand)
        btn_collapse = QPushButton("Recolher Tudo")
        btn_collapse.clicked.connect(self.tree.collapseAll)
        expand_layout.addWidget(btn_collapse)
        tree_layout.addLayout(expand_layout)

        main_layout.addWidget(tree_group, 2)

        actions_group = QGroupBox("Ações")
        actions_layout = QVBoxLayout(actions_group)
        self.info_label = QLabel("Selecione uma tag para ver detalhes")
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(80)
        actions_layout.addWidget(self.info_label)
        actions_layout.addSpacing(20)

        btn_nova = QPushButton("➕ Nova Tag Raiz")
        btn_nova.clicked.connect(self.criar_tag_raiz)
        btn_nova.setStyleSheet("background-color: #1abc9c; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        actions_layout.addWidget(btn_nova)

        self.btn_criar_filho = QPushButton("➕ Criar Sub-tag")
        self.btn_criar_filho.clicked.connect(self.criar_subtag)
        self.btn_criar_filho.setEnabled(False)
        actions_layout.addWidget(self.btn_criar_filho)
        
        self.btn_editar = QPushButton("✏️ Editar Nome")
        self.btn_editar.clicked.connect(self.editar_tag)
        self.btn_editar.setEnabled(False)
        actions_layout.addWidget(self.btn_editar)

        self.btn_deletar = QPushButton("🗑️ Deletar")
        self.btn_deletar.clicked.connect(self.deletar_tag)
        self.btn_deletar.setEnabled(False)
        self.btn_deletar.setStyleSheet("color: #e74c3c;")
        actions_layout.addWidget(self.btn_deletar)

        actions_layout.addStretch()
        main_layout.addWidget(actions_group, 1)
        layout.addLayout(main_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("✔️ Fechar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _add_tree_items(self, parent_item, tags: List[TagResponseDTO]):
        """Adiciona recursivamente itens à árvore."""
        for tag_dto in tags:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, tag_dto.nome)
            item.setText(1, tag_dto.numeracao)
            item.setData(0, Qt.ItemDataRole.UserRole, tag_dto.id_tag)
            
            if tag_dto.filhos:
                self._add_tree_items(item, tag_dto.filhos)

    def load_tags(self):
        """Carrega tags do banco de dados e popula a árvore."""
        try:
            self.tree.clear()
            tags_arvore = self.controller.obter_arvore_tags_completa()
            self._add_tree_items(self.tree, tags_arvore)
            self.tree.expandAll()
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar tags")

    def on_selection_changed(self):
        """Atualiza o painel de informações e o estado dos botões quando a seleção muda."""
        selected = self.tree.selectedItems()
        is_item_selected = bool(selected)

        if is_item_selected:
            item = selected[0]
            nome = item.text(0)
            numeracao = item.text(1)
            self.info_label.setText(f"<b>{nome}</b><br>Numeração: {numeracao}")
        else:
            self.info_label.setText("Selecione uma tag para ver detalhes")

        self.btn_editar.setEnabled(is_item_selected)
        self.btn_criar_filho.setEnabled(is_item_selected)
        self.btn_deletar.setEnabled(is_item_selected)

    def _handle_creation(self, nome: str, pai_id: int = None):
        """Lógica central para criar uma tag."""
        if not nome:
            return
        try:
            dto = TagCreateDTO(nome=nome, id_tag_pai=pai_id)
            nova_tag = self.controller.criar_tag(dto)
            if nova_tag:
                ErrorHandler.show_success(self, "Sucesso", f"Tag '{nome}' criada com sucesso!")
                self.load_tags()
        except ValueError as ve:
            QMessageBox.warning(self, "Erro de Validação", str(ve))
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao criar tag")

    def criar_tag_raiz(self):
        """Cria uma nova tag no nível raiz."""
        nome, ok = QInputDialog.getText(self, "Nova Tag Raiz", "Nome da tag:")
        if ok:
            self._handle_creation(nome.strip())

    def criar_subtag(self):
        """Cria uma sub-tag para o item selecionado."""
        selected = self.tree.selectedItems()
        if not selected:
            return
        
        pai_item = selected[0]
        pai_nome = pai_item.text(0)
        pai_id = pai_item.data(0, Qt.ItemDataRole.UserRole)

        nome, ok = QInputDialog.getText(self, "Nova Sub-tag", f"Nome da sub-tag para '{pai_nome}':")
        if ok:
            self._handle_creation(nome.strip(), pai_id=pai_id)

    def editar_tag(self):
        """Edita o nome da tag selecionada."""
        selected = self.tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        nome_atual = item.text(0)
        tag_id = item.data(0, Qt.ItemDataRole.UserRole)

        novo_nome, ok = QInputDialog.getText(self, "Editar Tag", "Novo nome:", text=nome_atual)
        if not ok or not novo_nome.strip() or novo_nome.strip() == nome_atual:
            return
        
        try:
            dto = TagUpdateDTO(id_tag=tag_id, nome=novo_nome.strip())
            if self.controller.atualizar_tag(dto):
                ErrorHandler.show_success(self, "Sucesso", "Tag atualizada com sucesso!")
                self.load_tags()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível atualizar a tag.")
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao editar tag")

    def deletar_tag(self):
        """Deleta a tag selecionada após confirmação e validação."""
        selected = self.tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        nome = item.text(0)
        tag_id = item.data(0, Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "Confirmar Deleção",
            f"Tem certeza que deseja deletar a tag '{nome}'?\n\n A ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            if self.controller.deletar_tag(tag_id):
                ErrorHandler.show_success(self, "Sucesso", f"Tag '{nome}' deletada com sucesso!")
                self.load_tags()
        except (ValueError, RuntimeError) as e:
            QMessageBox.warning(self, "Não foi possível deletar", str(e))
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao deletar tag")


logger.info("TagManager carregado")