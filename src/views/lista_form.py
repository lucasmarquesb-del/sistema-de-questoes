"""
View: Lista Form
DESCRIÇÃO: Formulário de criação/edição de listas de questões.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QMessageBox,
    QGroupBox, QInputDialog, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
from typing import List

from src.utils import ErrorHandler
from src.controllers.adapters import criar_lista_controller
from src.controllers.adapters import criar_questao_controller
from src.application.dtos import ListaCreateDTO, ListaUpdateDTO, QuestaoResponseDTO

logger = logging.getLogger(__name__)


class ListaForm(QDialog):
    """Formulário para criar/editar listas de questões"""
    listaSaved = pyqtSignal()

    def __init__(self, lista_id=None, parent=None):
        super().__init__(parent)
        self.lista_id = lista_id
        self.is_editing = self.lista_id is not None
        
        # Controllers
        self.controller = criar_lista_controller()
        self.questao_controller = criar_questao_controller()
        
        self.questoes_na_lista: List[QuestaoResponseDTO] = []

        self.setWindowTitle("Editar Lista" if self.is_editing else "Nova Lista")
        self.setMinimumSize(1000, 700)
        self.init_ui()
        
        if self.is_editing:
            self.load_lista_data(self.lista_id)
            
        logger.info(f"ListaForm inicializado (ID: {self.lista_id})")

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("📋 " + ("Editar Lista" if self.is_editing else "Nova Lista"))
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Informações básicas
        info_group = QGroupBox("Informações da Lista")
        info_layout = QFormLayout(info_group)
        self.titulo_input = QLineEdit()
        self.titulo_input.setPlaceholderText("Ex: Prova de Matemática - 1º Bimestre")
        info_layout.addRow(QLabel("Título:"), self.titulo_input)
        self.tipo_input = QLineEdit()
        self.tipo_input.setPlaceholderText("Ex: Prova, Lista de Exercícios, Simulado...")
        info_layout.addRow(QLabel("Tipo:"), self.tipo_input)
        layout.addWidget(info_group)

        # Cabeçalho e instruções
        text_group = QGroupBox("Cabeçalho e Instruções (para exportação)")
        text_layout = QVBoxLayout(text_group)
        self.cabecalho_edit = QTextEdit()
        self.cabecalho_edit.setPlaceholderText("Nome da Instituição\nDisciplina\nData...")
        text_layout.addWidget(QLabel("Cabeçalho:"))
        text_layout.addWidget(self.cabecalho_edit)
        self.instrucoes_edit = QTextEdit()
        self.instrucoes_edit.setPlaceholderText("Instruções para os alunos...")
        text_layout.addWidget(QLabel("Instruções:"))
        text_layout.addWidget(self.instrucoes_edit)
        layout.addWidget(text_group)

        # Questões
        questoes_group = QGroupBox("Questões da Lista")
        questoes_layout = QVBoxLayout(questoes_group)
        self.questoes_list = QListWidget()
        self.questoes_list.setMinimumHeight(200)
        questoes_layout.addWidget(self.questoes_list)
        btn_questoes_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Adicionar Questão")
        btn_add.clicked.connect(self.adicionar_questao)
        btn_questoes_layout.addWidget(btn_add)
        btn_remove = QPushButton("➖ Remover Selecionada")
        btn_remove.clicked.connect(self.remover_questao)
        btn_questoes_layout.addWidget(btn_remove)
        btn_questoes_layout.addStretch()
        questoes_layout.addLayout(btn_questoes_layout)
        layout.addWidget(questoes_group)

        # Botões finais
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("❌ Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_save = QPushButton("💾 Salvar")
        btn_save.setStyleSheet("background-color: #1abc9c; color: white; padding: 8px 20px; font-weight: bold; border-radius: 4px;")
        btn_save.clicked.connect(self.salvar_lista)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def load_lista_data(self, id_lista):
        try:
            lista_dto = self.controller.obter_lista_completa(id_lista)
            if not lista_dto:
                ErrorHandler.show_error(self, "Erro", "Lista não encontrada.")
                self.close()
                return
            
            self.titulo_input.setText(lista_dto.titulo)
            self.tipo_input.setText(lista_dto.tipo or "")
            self.cabecalho_edit.setPlainText(lista_dto.cabecalho or "")
            self.instrucoes_edit.setPlainText(lista_dto.instrucoes or "")
            self.questoes_na_lista = lista_dto.questoes
            self._popular_lista_questoes()
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar dados da lista.")

    def _popular_lista_questoes(self):
        self.questoes_list.clear()
        for q in self.questoes_na_lista:
            texto = f"ID: {q.id} - {q.titulo or q.enunciado[:50]}..."
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, q.id)
            self.questoes_list.addItem(item)

    def adicionar_questao(self):
        # TODO: Substituir por um diálogo de busca de questões (SearchPanel)
        questao_id, ok = QInputDialog.getInt(self, "Adicionar Questão", "Digite o ID da questão:")
        if not ok or not questao_id:
            return
            
        try:
            if any(q.id == questao_id for q in self.questoes_na_lista):
                ErrorHandler.show_info(self, "Informação", "Esta questão já está na lista.")
                return

            questao_dto = self.questao_controller.obter_questao_completa(questao_id)
            if not questao_dto:
                ErrorHandler.show_warning(self, "Não encontrada", f"Questão com ID {questao_id} não encontrada.")
                return
            
            self.questoes_na_lista.append(questao_dto)
            self._popular_lista_questoes()
            
            if self.is_editing:
                self.controller.adicionar_questao_lista(self.lista_id, questao_id)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao adicionar questão.")

    def remover_questao(self):
        item_selecionado = self.questoes_list.currentItem()
        if not item_selecionado:
            return
            
        id_questao = item_selecionado.data(Qt.ItemDataRole.UserRole)
        
        self.questoes_na_lista = [q for q in self.questoes_na_lista if q.id != id_questao]
        self._popular_lista_questoes()
        
        if self.is_editing:
            try:
                self.controller.remover_questao_lista(self.lista_id, id_questao)
            except Exception as e:
                ErrorHandler.handle_exception(self, e, "Erro ao remover questão da lista no banco de dados.")

    def salvar_lista(self):
        try:
            titulo = self.titulo_input.text().strip()
            if not titulo:
                ErrorHandler.show_warning(self, "Validação", "O título é obrigatório!")
                return

            if self.is_editing:
                dto = ListaUpdateDTO(
                    id_lista=self.lista_id,
                    titulo=titulo,
                    tipo=self.tipo_input.text().strip() or None,
                    cabecalho=self.cabecalho_edit.toPlainText().strip() or None,
                    instrucoes=self.instrucoes_edit.toPlainText().strip() or None
                )
                self.controller.atualizar_lista(dto)
            else:
                dto = ListaCreateDTO(
                    titulo=titulo,
                    tipo=self.tipo_input.text().strip() or None,
                    cabecalho=self.cabecalho_edit.toPlainText().strip() or None,
                    instrucoes=self.instrucoes_edit.toPlainText().strip() or None
                )
                id_nova_lista = self.controller.criar_lista(dto)
                if not id_nova_lista:
                    ErrorHandler.show_error(self, "Erro", "Não foi possível criar a lista.")
                    return
                
                # Adicionar questões à lista recém-criada
                for q in self.questoes_na_lista:
                    self.controller.adicionar_questao_lista(id_nova_lista, q.id)
            
            ErrorHandler.show_success(self, "Sucesso", f"Lista '{titulo}' salva com sucesso!")
            self.listaSaved.emit()
            self.accept()

        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao salvar lista.")

logger.info("ListaForm carregado")