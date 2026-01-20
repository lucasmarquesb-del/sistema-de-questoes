"""
View: Search Page
Pagina de busca e filtros de questoes
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QSpinBox,
    QGroupBox, QSplitter, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.controllers.adapters import criar_questao_controller
from src.controllers.adapters import criar_tag_controller
from src.application.dtos import FiltroQuestaoDTO
from src.utils import ErrorHandler
from src.views.components.forms.tag_tree import TagTreeWidget
from src.views.components.cards.questao_card import QuestaoCard

logger = logging.getLogger(__name__)


class SearchPage(QWidget):
    """Pagina de busca e filtros de questoes."""
    questaoSelected = pyqtSignal(str)  # Emite codigo da questao
    editQuestao = pyqtSignal(str)
    inactivateQuestao = pyqtSignal(str)
    reactivateQuestao = pyqtSignal(str)
    addToListQuestao = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = criar_questao_controller()
        self.tag_controller = criar_tag_controller()
        self.init_ui()
        self.load_tags()
        self.load_fontes()
        self.load_series()
        logger.info("SearchPage inicializado")

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        filters_panel = self._create_filters_panel()
        results_panel = self._create_results_panel()
        splitter.addWidget(filters_panel)
        splitter.addWidget(results_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        layout.addWidget(splitter)

    def _create_filters_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        title_label = QLabel("Filtros de Busca")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Filtros principais
        main_filters_group = QGroupBox("Filtros Principais")
        main_filters_layout = QVBoxLayout(main_filters_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar em titulo e enunciado...")
        main_filters_layout.addWidget(self.search_input)
        main_filters_layout.addWidget(QLabel("Fonte/Banca:"))
        self.fonte_combo = QComboBox()
        self.fonte_combo.addItem("Todas as Fontes", None)
        main_filters_layout.addWidget(self.fonte_combo)
        main_filters_layout.addWidget(QLabel("Serie/Nivel:"))
        self.serie_combo = QComboBox()
        self.serie_combo.addItem("Todas as Series", None)
        main_filters_layout.addWidget(self.serie_combo)
        layout.addWidget(main_filters_group)

        # Filtros por atributos
        attr_filters_group = QGroupBox("Atributos")
        attr_filters_layout = QVBoxLayout(attr_filters_group)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItem("Todos os Tipos", None)
        self.tipo_combo.addItem("Objetiva", "OBJETIVA")
        self.tipo_combo.addItem("Discursiva", "DISCURSIVA")
        attr_filters_layout.addWidget(self.tipo_combo)
        self.dificuldade_combo = QComboBox()
        self.dificuldade_combo.addItem("Todas as Dificuldades", None)
        self.dificuldade_combo.addItem("Facil", "FACIL")
        self.dificuldade_combo.addItem("Medio", "MEDIO")
        self.dificuldade_combo.addItem("Dificil", "DIFICIL")
        attr_filters_layout.addWidget(self.dificuldade_combo)
        ano_layout = QHBoxLayout()
        ano_layout.addWidget(QLabel("Ano de:"))
        self.ano_de_spin = QSpinBox()
        self.ano_de_spin.setRange(1900, 2100)
        self.ano_de_spin.setValue(2000)
        ano_layout.addWidget(self.ano_de_spin)
        ano_layout.addWidget(QLabel("ate:"))
        self.ano_ate_spin = QSpinBox()
        self.ano_ate_spin.setRange(1900, 2100)
        self.ano_ate_spin.setValue(datetime.now().year)
        ano_layout.addWidget(self.ano_ate_spin)
        attr_filters_layout.addLayout(ano_layout)
        layout.addWidget(attr_filters_group)

        # Filtro por Tags
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        self.tag_tree_widget = TagTreeWidget()
        tags_layout.addWidget(self.tag_tree_widget)
        layout.addWidget(tags_group)

        # Filtro de status (ativas/inativas)
        self.incluir_inativas_check = QCheckBox("Incluir questoes inativas")
        self.incluir_inativas_check.setStyleSheet("color: #e67e22; font-weight: bold;")
        layout.addWidget(self.incluir_inativas_check)

        layout.addStretch()

        # Acoes
        btn_layout = QHBoxLayout()
        btn_search = QPushButton("Buscar")
        btn_search.clicked.connect(self.perform_search)
        btn_search.setStyleSheet("background-color: #1abc9c; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        btn_layout.addWidget(btn_search)
        btn_clear = QPushButton("Limpar")
        btn_clear.clicked.connect(self.clear_filters)
        btn_layout.addWidget(btn_clear)
        layout.addLayout(btn_layout)

        self.results_count_label = QLabel("Resultados: 0")
        self.results_count_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(self.results_count_label)
        return panel

    def _create_results_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        header_layout = QHBoxLayout()
        title_label = QLabel("Resultados da Busca")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(10)
        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)
        self.show_empty_state()
        return panel

    def load_tags(self):
        """Carrega apenas tags de conteudos (exclui banca/vestibular e etapa)"""
        try:
            tags_arvore = self.tag_controller.obter_arvore_conteudos()
            self.tag_tree_widget.load_tags(tags_arvore)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar tags para filtro.")

    def load_fontes(self):
        """Carrega as tags de vestibular/banca para o dropdown"""
        try:
            vestibulares = self.tag_controller.listar_vestibulares()
            for vest in vestibulares:
                self.fonte_combo.addItem(vest['nome'], vest['uuid'])
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar fontes/vestibulares.")

    def load_series(self):
        """Carrega as series/niveis de escolaridade para o dropdown"""
        try:
            series = self.tag_controller.listar_series()
            for serie in series:
                self.serie_combo.addItem(serie['nome'], serie['uuid'])
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar series.")

    def show_empty_state(self):
        self.clear_results()
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label = QLabel("?")
        icon_label.setStyleSheet("font-size: 64px; color: #ccc;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_label)
        msg_label = QLabel("Nenhuma questao encontrada")
        msg_label.setStyleSheet("font-size: 18px; color: #666; margin-top: 10px;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(msg_label)
        hint_label = QLabel("Ajuste os filtros e clique em Buscar")
        hint_label.setStyleSheet("font-size: 14px; color: #999; margin-top: 5px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hint_label)
        self.results_layout.addWidget(empty_widget)

    def clear_results(self):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def clear_filters(self):
        logger.info("Limpando filtros")
        self.search_input.clear()
        self.tipo_combo.setCurrentIndex(0)
        self.dificuldade_combo.setCurrentIndex(0)
        self.ano_de_spin.setValue(2000)
        self.ano_ate_spin.setValue(datetime.now().year)
        self.fonte_combo.setCurrentIndex(0)
        self.serie_combo.setCurrentIndex(0)
        self.tag_tree_widget.clear_selection()
        self.show_empty_state()
        self.results_count_label.setText("Resultados: 0")

    def perform_search(self):
        logger.info("Executando busca")
        self.clear_results()
        try:
            filtro_dto = self._get_filtros()
            # Converter DTO para dict
            filtro = {
                'titulo': filtro_dto.titulo,
                'tipo': filtro_dto.tipo,
                'ano_inicio': filtro_dto.ano_inicio,
                'ano_fim': filtro_dto.ano_fim,
                'fonte': filtro_dto.fonte,
                'dificuldade': filtro_dto.dificuldade,
                'tags': filtro_dto.tags,
                'ativa': filtro_dto.ativa
            }
            questoes_dto = self.controller.buscar_questoes(filtro)
            if not questoes_dto:
                self.show_empty_state()
            else:
                for questao_dto in questoes_dto:
                    card = QuestaoCard(questao_dto)
                    card.clicked.connect(self.questaoSelected.emit)
                    card.editClicked.connect(self.editQuestao.emit)
                    card.inactivateClicked.connect(self.inactivateQuestao.emit)
                    card.reactivateClicked.connect(self.reactivateQuestao.emit)
                    card.addToListClicked.connect(self.addToListQuestao.emit)
                    self.results_layout.addWidget(card)
            self.results_count_label.setText(f"Resultados: {len(questoes_dto)}")
            logger.info(f"Busca concluida: {len(questoes_dto)} questoes encontradas")
        except Exception as e:
            self.results_count_label.setText("Erro ao buscar questoes")
            ErrorHandler.handle_exception(self, e, "Erro ao buscar questoes")

    def _get_filtros(self) -> FiltroQuestaoDTO:
        titulo = self.search_input.text().strip() or None
        tipo = self.tipo_combo.currentData()  # Retorna o codigo ou None
        ano_inicio = self.ano_de_spin.value()
        ano_fim = self.ano_ate_spin.value()

        dificuldade_texto = self.dificuldade_combo.currentData()  # Retorna o codigo ou None

        # Coletar tags selecionadas (conteudos)
        tags = self.tag_tree_widget.get_selected_tag_ids()

        # Adicionar vestibular/fonte selecionada as tags (se houver)
        fonte_uuid = self.fonte_combo.currentData()
        if fonte_uuid:
            tags.append(fonte_uuid)

        # Adicionar serie selecionada as tags (se houver)
        serie_uuid = self.serie_combo.currentData()
        if serie_uuid:
            tags.append(serie_uuid)

        # Se incluir inativas, ativa=None (buscar todas), senao ativa=True (so ativas)
        incluir_inativas = self.incluir_inativas_check.isChecked()
        ativa = None if incluir_inativas else True

        return FiltroQuestaoDTO(
            titulo=titulo,
            tipo=tipo,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
            fonte=None,  # Nao usar mais fonte_questao, usar tags
            dificuldade=dificuldade_texto,
            tags=tags if tags else None,
            ativa=ativa
        )

    def filter_by_tag(self, tag_uuid: str):
        """Filtra questoes por uma tag especifica (chamado pela sidebar)"""
        logger.info(f"Filtrando por tag: {tag_uuid}")
        # Limpar filtros existentes
        self.clear_filters()
        # Selecionar a tag na arvore (se encontra-la)
        self.tag_tree_widget.set_selected_tags([tag_uuid])
        # Executar busca
        self.perform_search()


# Alias para compatibilidade
SearchPanel = SearchPage
