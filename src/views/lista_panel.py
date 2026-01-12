"""
View: Lista Panel
DESCRIÇÃO: Painel de visualização e gerenciamento de listas de questões.
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt

from src.controllers.lista_controller import criar_lista_controller
from src.views.lista_form import ListaForm
from src.views.export_dialog import ExportDialog # Novo import
from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class ListaPanel(QWidget):
    """Painel para gerenciar todas as listas de questões."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = criar_lista_controller()
        self.init_ui()
        self.load_listas()
        logger.info("ListaPanel inicializado.")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Cabeçalho
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Minhas Listas de Questões")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        btn_nova_lista = QPushButton("➕ Nova Lista")
        btn_nova_lista.clicked.connect(self.abrir_form_nova_lista)
        btn_nova_lista.setStyleSheet("background-color: #1abc9c; color: white; padding: 8px 15px; font-weight: bold; border-radius: 4px;")
        header_layout.addWidget(btn_nova_lista)
        layout.addLayout(header_layout)

        # Lista de listas
        self.lista_widget = QListWidget()
        self.lista_widget.setStyleSheet("font-size: 14px;")
        self.lista_widget.itemDoubleClicked.connect(self.abrir_form_edicao_lista)
        layout.addWidget(self.lista_widget)

        # Botões de ação
        action_layout = QHBoxLayout()
        
        btn_exportar_lista = QPushButton("📄 Exportar Selecionada") # Novo botão
        btn_exportar_lista.clicked.connect(self.abrir_dialogo_exportacao) # Nova conexão
        action_layout.addWidget(btn_exportar_lista)

        action_layout.addStretch()
        btn_editar_lista = QPushButton("✏️ Editar Selecionada")
        btn_editar_lista.clicked.connect(self.abrir_form_edicao_lista)
        action_layout.addWidget(btn_editar_lista)
        btn_deletar_lista = QPushButton("🗑️ Deletar Selecionada")
        btn_deletar_lista.setStyleSheet("color: #e74c3c;")
        btn_deletar_lista.clicked.connect(self.deletar_lista_selecionada)
        action_layout.addWidget(btn_deletar_lista)
        layout.addLayout(action_layout)

    def load_listas(self):
        """Carrega ou atualiza a lista de listas exibida."""
        try:
            self.lista_widget.clear()
            listas = self.controller.listar_todas_listas()
            if not listas:
                item = QListWidgetItem("Nenhuma lista criada ainda.")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.lista_widget.addItem(item)
            else:
                for lista_dto in listas:
                    texto = f"{lista_dto.titulo} ({lista_dto.total_questoes} questões)"
                    item = QListWidgetItem(texto)
                    item.setData(Qt.ItemDataRole.UserRole, lista_dto.id)
                    self.lista_widget.addItem(item)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar listas.")

    def abrir_form_nova_lista(self):
        """Abre o formulário para criar uma nova lista."""
        dialog = ListaForm(parent=self)
        # Conecta o sinal de sucesso do form ao método de recarregar
        dialog.listaSaved.connect(self.load_listas)
        dialog.exec()

    def abrir_form_edicao_lista(self):
        """Abre o formulário para editar a lista selecionada."""
        item_selecionado = self.lista_widget.currentItem()
        if not item_selecionado or item_selecionado.data(Qt.ItemDataRole.UserRole) is None:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma lista para editar.")
            return
            
        id_lista = item_selecionado.data(Qt.ItemDataRole.UserRole)
        dialog = ListaForm(lista_id=id_lista, parent=self)
        dialog.listaSaved.connect(self.load_listas)
        dialog.exec()

    def deletar_lista_selecionada(self):
        """Deleta a lista selecionada após confirmação."""
        item_selecionado = self.lista_widget.currentItem()
        if not item_selecionado or item_selecionado.data(Qt.ItemDataRole.UserRole) is None:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma lista para deletar.")
            return

        id_lista = item_selecionado.data(Qt.ItemDataRole.UserRole)
        titulo = item_selecionado.text().split(' (')[0]

        reply = QMessageBox.question(
            self,
            "Confirmar Deleção",
            f"Tem certeza que deseja deletar a lista '{titulo}'?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.controller.deletar_lista(id_lista):
                    ErrorHandler.show_success(self, "Sucesso", "Lista deletada com sucesso.")
                    self.load_listas()
                else:
                    ErrorHandler.show_error(self, "Erro", "Não foi possível deletar a lista.")
            except Exception as e:
                ErrorHandler.handle_exception(self, e, "Erro ao deletar lista.")

    def abrir_dialogo_exportacao(self):
        """Abre o diálogo de exportação para a lista selecionada."""
        item_selecionado = self.lista_widget.currentItem()
        if not item_selecionado or item_selecionado.data(Qt.ItemDataRole.UserRole) is None:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma lista para exportar.")
            return

        id_lista = item_selecionado.data(Qt.ItemDataRole.UserRole)
        dialog = ExportDialog(id_lista=id_lista, parent=self)
        dialog.exec()


logger.info("ListaPanel carregado.")
