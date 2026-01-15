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

        # Estado: mostrar tags ativas ou inativas
        self.mostrando_inativas = False

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

        btn_nova = QPushButton("➕ Nova Tag")
        btn_nova.clicked.connect(self.criar_tag)
        btn_nova.setStyleSheet("background-color: #1abc9c; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        actions_layout.addWidget(btn_nova)

        self.btn_editar = QPushButton("✏️ Editar Nome")
        self.btn_editar.clicked.connect(self.editar_tag)
        self.btn_editar.setEnabled(False)
        actions_layout.addWidget(self.btn_editar)

        self.btn_inativar = QPushButton("🚫 Inativar")
        self.btn_inativar.clicked.connect(self.inativar_tag)
        self.btn_inativar.setEnabled(False)
        self.btn_inativar.setStyleSheet("color: #e67e22;")
        actions_layout.addWidget(self.btn_inativar)

        self.btn_reativar = QPushButton("✅ Reativar")
        self.btn_reativar.clicked.connect(self.reativar_tag)
        self.btn_reativar.setEnabled(False)
        self.btn_reativar.setStyleSheet("color: #27ae60;")
        self.btn_reativar.setVisible(False)  # Só visível ao mostrar inativas
        actions_layout.addWidget(self.btn_reativar)

        actions_layout.addSpacing(20)

        self.btn_toggle_inativas = QPushButton("👁️ Ver Tags Inativas")
        self.btn_toggle_inativas.clicked.connect(self.toggle_visualizacao_inativas)
        self.btn_toggle_inativas.setStyleSheet("color: #7f8c8d;")
        actions_layout.addWidget(self.btn_toggle_inativas)

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
            # Armazenar UUID para operações
            item.setData(0, Qt.ItemDataRole.UserRole, tag_dto.uuid)

            if tag_dto.filhos:
                self._add_tree_items(item, tag_dto.filhos)

    def load_tags(self):
        """Carrega tags do banco de dados e popula a árvore."""
        try:
            self.tree.clear()

            if self.mostrando_inativas:
                tags_arvore = self.controller.obter_arvore_tags_inativas()
                if not tags_arvore:
                    self.info_label.setText("Nenhuma tag inativa encontrada.")
            else:
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
            status = "Inativa" if self.mostrando_inativas else "Ativa"
            self.info_label.setText(f"<b>{nome}</b><br>Numeração: {numeracao}<br>Status: {status}")

            # Tags de vestibular (V) e série (N) não podem ser editadas ou inativadas
            is_special_tag = numeracao and (numeracao.startswith('V') or numeracao.startswith('N'))

            if self.mostrando_inativas:
                # Modo inativas: só pode reativar
                self.btn_editar.setEnabled(False)
                self.btn_inativar.setEnabled(False)
                self.btn_reativar.setEnabled(not is_special_tag)
            else:
                # Modo ativas: pode editar e inativar
                self.btn_editar.setEnabled(not is_special_tag)
                self.btn_inativar.setEnabled(not is_special_tag)
                self.btn_reativar.setEnabled(False)
        else:
            self.info_label.setText("Selecione uma tag para ver detalhes")
            self.btn_editar.setEnabled(False)
            self.btn_inativar.setEnabled(False)
            self.btn_reativar.setEnabled(False)

    def _handle_creation(self, nome: str, uuid_pai: str = None, tipo: str = 'CONTEUDO'):
        """Lógica central para criar uma tag."""
        if not nome:
            return
        try:
            dto = TagCreateDTO(nome=nome, id_tag_pai=uuid_pai)
            nova_tag = self.controller.criar_tag(dto, tipo)
            if nova_tag:
                ErrorHandler.show_success(self, "Sucesso", f"Tag '{nome}' criada com sucesso!")
                self.load_tags()
        except ValueError as ve:
            QMessageBox.warning(self, "Erro de Validação", str(ve))
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao criar tag")

    def criar_tag(self):
        """Cria uma nova tag, permitindo escolher se é raiz ou sub-tag."""
        # Primeiro, perguntar se é tag raiz ou sub-tag
        opcoes = ["Tag Raiz", "Sub-tag (filha de outra tag)"]
        opcao_escolhida, ok = QInputDialog.getItem(
            self, "Nova Tag",
            "Selecione o tipo de criação:",
            opcoes, 0, False
        )
        if not ok:
            return

        if opcao_escolhida == "Tag Raiz":
            self._criar_tag_raiz()
        else:
            self._criar_subtag()

    def _criar_tag_raiz(self):
        """Cria uma nova tag no nível raiz, permitindo escolher o tipo."""
        tipos = ["Conteúdo (assunto)", "Vestibular/Banca", "Série/Nível"]
        tipo_escolhido, ok = QInputDialog.getItem(
            self, "Tipo de Tag Raiz",
            "Selecione o tipo da tag raiz:",
            tipos, 0, False
        )
        if not ok:
            return

        tipo_map = {
            "Conteúdo (assunto)": "CONTEUDO",
            "Vestibular/Banca": "VESTIBULAR",
            "Série/Nível": "SERIE"
        }
        tipo = tipo_map.get(tipo_escolhido, "CONTEUDO")

        nome, ok = QInputDialog.getText(self, "Nova Tag Raiz", f"Nome da tag ({tipo_escolhido}):")
        if ok and nome.strip():
            self._handle_creation(nome.strip(), tipo=tipo)

    def _criar_subtag(self):
        """Cria uma sub-tag, permitindo escolher a tag pai."""
        # Obter todas as tags de conteúdo que podem ter filhas
        tags_disponiveis = self._obter_tags_para_pai()

        if not tags_disponiveis:
            QMessageBox.information(
                self, "Aviso",
                "Não há tags de conteúdo disponíveis para criar sub-tags.\n"
                "Tags de Vestibular/Banca e Série/Nível não aceitam sub-tags."
            )
            return

        # Criar lista de opções com caminho completo
        opcoes = [f"{tag['caminho']} ({tag['numeracao']})" for tag in tags_disponiveis]

        pai_escolhido, ok = QInputDialog.getItem(
            self, "Selecionar Tag Pai",
            "Selecione a tag pai para a nova sub-tag:",
            opcoes, 0, False
        )
        if not ok:
            return

        # Encontrar a tag selecionada
        idx = opcoes.index(pai_escolhido)
        tag_pai = tags_disponiveis[idx]

        nome, ok = QInputDialog.getText(
            self, "Nova Sub-tag",
            f"Nome da sub-tag para '{tag_pai['nome']}':"
        )
        if ok and nome.strip():
            self._handle_creation(nome.strip(), uuid_pai=tag_pai['uuid'])

    def _obter_tags_para_pai(self):
        """Retorna lista de tags que podem ser pai (apenas conteúdo)."""
        resultado = []

        def _processar_item(item, caminho_pai=""):
            numeracao = item.text(1)
            nome = item.text(0)
            uuid = item.data(0, Qt.ItemDataRole.UserRole)

            # Ignorar tags de vestibular (V) e série (N)
            if numeracao and (numeracao.startswith('V') or numeracao.startswith('N')):
                return

            caminho = f"{caminho_pai} > {nome}" if caminho_pai else nome

            resultado.append({
                'uuid': uuid,
                'nome': nome,
                'numeracao': numeracao,
                'caminho': caminho
            })

            # Processar filhos
            for i in range(item.childCount()):
                _processar_item(item.child(i), caminho)

        # Processar todos os itens raiz da árvore
        for i in range(self.tree.topLevelItemCount()):
            _processar_item(self.tree.topLevelItem(i))

        return resultado

    def editar_tag(self):
        """Edita o nome da tag selecionada."""
        selected = self.tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        nome_atual = item.text(0)
        tag_uuid = item.data(0, Qt.ItemDataRole.UserRole)

        novo_nome, ok = QInputDialog.getText(self, "Editar Tag", "Novo nome:", text=nome_atual)
        if not ok or not novo_nome.strip() or novo_nome.strip() == nome_atual:
            return

        try:
            dto = TagUpdateDTO(id_tag=tag_uuid, nome=novo_nome.strip())
            if self.controller.atualizar_tag(dto):
                ErrorHandler.show_success(self, "Sucesso", "Tag atualizada com sucesso!")
                self.load_tags()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível atualizar a tag.")
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao editar tag")

    def inativar_tag(self):
        """Inativa a tag selecionada após confirmação."""
        selected = self.tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        nome = item.text(0)
        tag_uuid = item.data(0, Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "Confirmar Inativação",
            f"Tem certeza que deseja inativar a tag '{nome}'?\n\n"
            "A tag ficará oculta mas poderá ser reativada posteriormente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            if self.controller.inativar_tag(tag_uuid):
                ErrorHandler.show_success(self, "Sucesso", f"Tag '{nome}' inativada com sucesso!")
                self.load_tags()
        except (ValueError, RuntimeError) as e:
            QMessageBox.warning(self, "Não foi possível inativar", str(e))
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao inativar tag")

    def reativar_tag(self):
        """Reativa a tag selecionada."""
        selected = self.tree.selectedItems()
        if not selected:
            return

        item = selected[0]
        nome = item.text(0)
        tag_uuid = item.data(0, Qt.ItemDataRole.UserRole)

        try:
            if self.controller.reativar_tag(tag_uuid):
                ErrorHandler.show_success(self, "Sucesso", f"Tag '{nome}' reativada com sucesso!")
                self.load_tags()
        except (ValueError, RuntimeError) as e:
            QMessageBox.warning(self, "Não foi possível reativar", str(e))
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao reativar tag")

    def toggle_visualizacao_inativas(self):
        """Alterna entre visualização de tags ativas e inativas."""
        self.mostrando_inativas = not self.mostrando_inativas

        if self.mostrando_inativas:
            self.btn_toggle_inativas.setText("👁️ Ver Tags Ativas")
            self.btn_toggle_inativas.setStyleSheet("color: #27ae60;")
            self.btn_reativar.setVisible(True)
            self.btn_inativar.setVisible(False)
        else:
            self.btn_toggle_inativas.setText("👁️ Ver Tags Inativas")
            self.btn_toggle_inativas.setStyleSheet("color: #7f8c8d;")
            self.btn_reativar.setVisible(False)
            self.btn_inativar.setVisible(True)

        self.load_tags()


logger.info("TagManager carregado")