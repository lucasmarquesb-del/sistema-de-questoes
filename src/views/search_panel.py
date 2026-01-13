"""
View: Search Panel
DESCRIÇÃO: Painel de busca e filtros de questões
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFrame, QSpinBox,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from src.controllers.adapters import criar_questao_controller
from src.controllers.adapters import criar_tag_controller
from src.application.dtos import FiltroQuestaoDTO
from src.utils import ErrorHandler
from src.views.widgets import TagTreeWidget, QuestaoCard

logger = logging.getLogger(__name__)


class SearchPanel(QWidget):
    """Painel de busca e filtros de questões."""
    questaoSelected = pyqtSignal(int)
    editQuestao = pyqtSignal(int)
    deleteQuestao = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = criar_questao_controller()
        self.tag_controller = criar_tag_controller()
        self.init_ui()
        self.load_tags()
        logger.info("SearchPanel inicializado")

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
        title_label = QLabel("🔍 Filtros de Busca")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Filtros principais
        main_filters_group = QGroupBox("Filtros Principais")
        main_filters_layout = QVBoxLayout(main_filters_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar em título e enunciado...")
        main_filters_layout.addWidget(self.search_input)
        self.fonte_input = QLineEdit()
        self.fonte_input.setPlaceholderText("Fonte/Banca (ex: ENEM)...")
        main_filters_layout.addWidget(self.fonte_input)
        layout.addWidget(main_filters_group)

        # Filtros por atributos
        attr_filters_group = QGroupBox("Atributos")
        attr_filters_layout = QVBoxLayout(attr_filters_group)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Todos os Tipos", "OBJETIVA", "DISCURSIVA"])
        attr_filters_layout.addWidget(self.tipo_combo)
        self.dificuldade_combo = QComboBox()
        self.dificuldade_combo.addItems(["Todas as Dificuldades", "FÁCIL", "MÉDIO", "DIFÍCIL"])
        attr_filters_layout.addWidget(self.dificuldade_combo)
        ano_layout = QHBoxLayout()
        ano_layout.addWidget(QLabel("Ano de:"))
        self.ano_de_spin = QSpinBox()
        self.ano_de_spin.setRange(1900, 2100)
        self.ano_de_spin.setValue(2000)
        ano_layout.addWidget(self.ano_de_spin)
        ano_layout.addWidget(QLabel("até:"))
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

        layout.addStretch()
        
        # Ações
        btn_layout = QHBoxLayout()
        btn_search = QPushButton("🔍 Buscar")
        btn_search.clicked.connect(self.perform_search)
        btn_search.setStyleSheet("background-color: #1abc9c; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        btn_layout.addWidget(btn_search)
        btn_clear = QPushButton("🔄 Limpar")
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
        title_label = QLabel("📋 Resultados da Busca")
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
        try:
            tags_arvore = self.tag_controller.obter_arvore_tags_completa()
            self.tag_tree_widget.load_tags(tags_arvore)
        except Exception as e:
            ErrorHandler.handle_exception(self, e, "Erro ao carregar tags para filtro.")

    def show_empty_state(self):
        self.clear_results()
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label = QLabel("🔍")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_label)
        msg_label = QLabel("Nenhuma questão encontrada")
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
        self.fonte_input.clear()
        self.tag_tree_widget.clear_selection()
        self.show_empty_state()
        self.results_count_label.setText("Resultados: 0")

    def perform_search(self):
        logger.info("Executando busca")
        self.clear_results()
        try:
            filtro = self._get_filtros()
            questoes_dto = self.controller.buscar_questoes(filtro)
            if not questoes_dto:
                self.show_empty_state()
            else:
                for questao_dto in questoes_dto:
                    card = QuestaoCard(questao_dto)
                    card.editClicked.connect(self.editQuestao.emit)
                    card.deleteClicked.connect(self.deleteQuestao.emit)
                    card.clicked.connect(self.questaoSelected.emit)
                    self.results_layout.addWidget(card)
            self.results_count_label.setText(f"Resultados: {len(questoes_dto)}")
            logger.info(f"Busca concluída: {len(questoes_dto)} questões encontradas")
        except Exception as e:
            self.results_count_label.setText("Erro ao buscar questões")
            ErrorHandler.handle_exception(self, e, "Erro ao buscar questões")

    def _get_filtros(self) -> FiltroQuestaoDTO:
        titulo = self.search_input.text().strip() or None
        tipo = self.tipo_combo.currentText() if "Todos" not in self.tipo_combo.currentText() else None
        fonte = self.fonte_input.text().strip() or None
        ano_inicio = self.ano_de_spin.value()
        ano_fim = self.ano_ate_spin.value()
        
        dificuldade_texto = self.dificuldade_combo.currentText() if "Todas" not in self.dificuldade_combo.currentText() else None
        
        tags = self.tag_tree_widget.get_selected_tag_ids()

        return FiltroQuestaoDTO(
            titulo=titulo,
            tipo=tipo,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
            fonte=fonte,
            dificuldade=dificuldade_texto,
            tags=tags,
            ativa=True
        )

from datetime import datetime
