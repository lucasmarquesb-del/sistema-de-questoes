"""
View: Lista Page
Pagina de visualizacao e gerenciamento de listas de questoes.
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt

from src.controllers.adapters import criar_lista_controller
from src.views.pages.lista_form_page import ListaForm
from src.views.pages.export_page import ExportDialog
from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class ListaPage(QWidget):
    """Pagina para gerenciar todas as listas de questoes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = criar_lista_controller()
        self.init_ui()
        self.load_listas()
        logger.info("ListaPage inicializado.")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Cabecalho
        header_layout = QHBoxLayout()
        title_label = QLabel("Minhas Listas de Questoes")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        btn_nova_lista = QPushButton("+ Nova Lista")
        btn_nova_lista.clicked.connect(self.abrir_form_nova_lista)
        btn_nova_lista.setStyleSheet("background-color: #1abc9c; color: white; padding: 8px 15px; font-weight: bold; border-radius: 4px;")
        header_layout.addWidget(btn_nova_lista)
        layout.addLayout(header_layout)

        # Lista de listas
        self.lista_widget = QListWidget()
        self.lista_widget.setStyleSheet("font-size: 14px;")
        self.lista_widget.itemDoubleClicked.connect(self.abrir_form_edicao_lista)
        layout.addWidget(self.lista_widget)

        # Botoes de acao
        action_layout = QHBoxLayout()

        btn_exportar_lista = QPushButton("Exportar Selecionada")
        btn_exportar_lista.clicked.connect(self.abrir_dialogo_exportacao)
        action_layout.addWidget(btn_exportar_lista)

        action_layout.addStretch()
        btn_editar_lista = QPushButton("Editar Selecionada")
        btn_editar_lista.clicked.connect(self.abrir_form_edicao_lista)
        action_layout.addWidget(btn_editar_lista)
        btn_deletar_lista = QPushButton("Deletar Selecionada")
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
                for lista in listas:
                    # Acessar como dict - usar codigo como identificador
                    titulo = lista.get('titulo', 'Sem titulo')
                    total_questoes = lista.get('total_questoes', 0)
                    lista_codigo = lista.get('codigo')  # Usar codigo, nao id
                    texto = f"{titulo} ({total_questoes} questoes)"
                    item = QListWidgetItem(texto)
                    item.setData(Qt.ItemDataRole.UserRole, lista_codigo)
                    self.lista_widget.addItem(item)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar listas.")

    def abrir_form_nova_lista(self):
        """Abre o formulario para criar uma nova lista."""
        dialog = ListaForm(parent=self)
        # Conecta o sinal de sucesso do form ao metodo de recarregar
        dialog.listaSaved.connect(self.load_listas)
        dialog.exec()

    def abrir_form_edicao_lista(self):
        """Abre o formulario para editar a lista selecionada."""
        item_selecionado = self.lista_widget.currentItem()
        if not item_selecionado or item_selecionado.data(Qt.ItemDataRole.UserRole) is None:
            QMessageBox.warning(self, "Atencao", "Por favor, selecione uma lista para editar.")
            return

        id_lista = item_selecionado.data(Qt.ItemDataRole.UserRole)
        dialog = ListaForm(lista_id=id_lista, parent=self)
        dialog.listaSaved.connect(self.load_listas)
        dialog.exec()

    def deletar_lista_selecionada(self):
        """Deleta a lista selecionada apos confirmacao."""
        item_selecionado = self.lista_widget.currentItem()
        if not item_selecionado or item_selecionado.data(Qt.ItemDataRole.UserRole) is None:
            QMessageBox.warning(self, "Atencao", "Por favor, selecione uma lista para deletar.")
            return

        id_lista = item_selecionado.data(Qt.ItemDataRole.UserRole)
        titulo = item_selecionado.text().split(' (')[0]

        reply = QMessageBox.question(
            self,
            "Confirmar Delecao",
            f"Tem certeza que deseja deletar a lista '{titulo}'?\n\nEsta acao nao pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.controller.deletar_lista(id_lista):
                    ErrorHandler.show_success(self, "Sucesso", "Lista deletada com sucesso.")
                    self.load_listas()
                else:
                    ErrorHandler.show_error(self, "Erro", "Nao foi possivel deletar a lista.")
            except Exception as e:
                ErrorHandler.handle_exception(self, e, "Erro ao deletar lista.")

    def abrir_dialogo_exportacao(self):
        """Abre o dialogo de exportacao para a lista selecionada."""
        item_selecionado = self.lista_widget.currentItem()
        if not item_selecionado or item_selecionado.data(Qt.ItemDataRole.UserRole) is None:
            QMessageBox.warning(self, "Atencao", "Por favor, selecione uma lista para exportar.")
            return

        id_lista = item_selecionado.data(Qt.ItemDataRole.UserRole)
        dialog = ExportDialog(id_lista=id_lista, parent=self)
        dialog.exec()


# Alias para compatibilidade
ListaPanel = ListaPage
