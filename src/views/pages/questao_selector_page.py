# src/views/pages/questao_selector_page.py
"""
Dialog para selecionar questões para adicionar a uma lista.
Layout igual ao banco de questões, com checkboxes para seleção.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy, QSpacerItem, QGridLayout, QMenu,
    QCheckBox, QWidget, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from typing import Dict, List, Any, Optional, Set
import logging

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text
from src.views.design.enums import DifficultyEnum
from src.views.components.common.inputs import SearchInput
from src.views.components.common.buttons import PrimaryButton, SecondaryButton
from src.views.components.common.badges import Badge, DifficultyBadge
from src.controllers.questao_controller_orm import QuestaoControllerORM
from src.controllers.adapters import criar_questao_controller, criar_tag_controller, listar_fontes_questao

logger = logging.getLogger(__name__)


class SelectableQuestionCard(QFrame):
    """
    Card de questão com checkbox para seleção.
    Visualmente igual ao QuestionCard do banco de questões.
    """
    selection_changed = pyqtSignal(str, bool)  # codigo, is_selected
    preview_requested = pyqtSignal(str)  # codigo

    def __init__(
        self,
        question_id: str,
        codigo: str,
        title: str,
        tags: list = None,
        difficulty: DifficultyEnum = None,
        is_in_list: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self.codigo = codigo
        self.is_in_list = is_in_list
        self._setup_ui(question_id, title, tags, difficulty)

    def _setup_ui(self, question_id: str, title: str, tags: list, difficulty: DifficultyEnum):
        self.setObjectName("selectable_question_card")

        # Estilo diferente se já está na lista
        if self.is_in_list:
            border_color = Color.TAG_GREEN
            bg_color = "#e8f8f0"
        else:
            border_color = Color.BORDER_LIGHT
            bg_color = Color.WHITE

        self.setStyleSheet(f"""
            QFrame#selectable_question_card {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
            QFrame#selectable_question_card:hover {{
                border-color: {Color.PRIMARY_BLUE};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        main_layout.setSpacing(Spacing.SM)

        # Header: Checkbox + Question ID
        header_layout = QHBoxLayout()

        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {Color.BORDER_MEDIUM};
                border-radius: 4px;
                background-color: {Color.WHITE};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Color.PRIMARY_BLUE};
                border-color: {Color.PRIMARY_BLUE};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Color.PRIMARY_BLUE};
            }}
        """)

        if self.is_in_list:
            self.checkbox.setChecked(True)
            self.checkbox.setEnabled(False)

        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        header_layout.addWidget(self.checkbox)

        question_id_label = QLabel(question_id)
        question_id_label.setObjectName("card_id")
        question_id_label.setStyleSheet(f"""
            QLabel#card_id {{
                color: {Color.PRIMARY_BLUE};
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                letter-spacing: 0.5px;
            }}
        """)
        header_layout.addWidget(question_id_label)
        header_layout.addStretch()

        # Badge "Já na lista"
        if self.is_in_list:
            in_list_label = QLabel("NA LISTA")
            in_list_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {Color.TAG_GREEN};
                    color: white;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)
            header_layout.addWidget(in_list_label)

        main_layout.addLayout(header_layout)

        # Title
        title_label = QLabel(title if title and title.strip() else "Sem título")
        title_label.setObjectName("card_title")
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"""
            QLabel#card_title {{
                font-size: {Typography.FONT_SIZE_LG};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                color: {Color.DARK_TEXT};
            }}
        """)
        main_layout.addWidget(title_label)

        # Tags and Difficulty
        tag_difficulty_layout = QHBoxLayout()
        if tags:
            for tag_text in tags[:3]:
                tag_difficulty_layout.addWidget(Badge(str(tag_text)))
        if difficulty:
            tag_difficulty_layout.addWidget(DifficultyBadge(difficulty))
        tag_difficulty_layout.addStretch()

        # Botão de preview
        preview_btn = QPushButton("Ver")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.LIGHT_BLUE_BG_1};
                color: {Color.PRIMARY_BLUE};
                border: 1px solid {Color.PRIMARY_BLUE};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Color.PRIMARY_BLUE};
                color: {Color.WHITE};
            }}
        """)
        preview_btn.clicked.connect(self._on_preview_clicked)
        tag_difficulty_layout.addWidget(preview_btn)

        main_layout.addLayout(tag_difficulty_layout)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_checkbox_changed(self, state):
        if not self.is_in_list:
            is_checked = state == Qt.CheckState.Checked.value
            self.selection_changed.emit(self.codigo, is_checked)

    def _on_preview_clicked(self):
        self.preview_requested.emit(self.codigo)

    def mousePressEvent(self, event):
        # Não alternar checkbox se clicar no botão de preview
        if not self.is_in_list and event.button() == Qt.MouseButton.LeftButton:
            # Verificar se o clique foi no botão (deixar o botão tratar)
            child = self.childAt(event.pos())
            if not isinstance(child, QPushButton):
                self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def is_selected(self) -> bool:
        return self.checkbox.isChecked() and not self.is_in_list

    def set_selected(self, selected: bool):
        if not self.is_in_list:
            self.checkbox.setChecked(selected)


class FilterChip(QFrame):
    """A removable filter chip/badge."""
    removed = pyqtSignal(str)

    def __init__(self, text: str, filter_key: str, parent=None):
        super().__init__(parent)
        self.filter_key = filter_key
        self.setObjectName("filter_chip")
        self.setStyleSheet(f"""
            QFrame#filter_chip {{
                background-color: {Color.LIGHT_BLUE_BG_1};
                border: 1px solid {Color.LIGHT_BLUE_BORDER};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: {Spacing.XS}px {Spacing.SM}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(Spacing.XS)

        label = QLabel(text, self)
        label.setStyleSheet(f"""
            color: {Color.PRIMARY_BLUE};
            font-size: {Typography.FONT_SIZE_SM};
            font-weight: {Typography.FONT_WEIGHT_MEDIUM};
        """)
        layout.addWidget(label)

        remove_btn = QPushButton("×", self)
        remove_btn.setFixedSize(16, 16)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Color.PRIMARY_BLUE};
                font-size: 14px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{
                color: {Color.HOVER_BLUE};
            }}
        """)
        remove_btn.clicked.connect(lambda: self.removed.emit(self.filter_key))
        layout.addWidget(remove_btn)


class QuestaoSelectorDialog(QDialog):
    """
    Dialog para selecionar questões - layout igual ao banco de questões.
    """
    questoesAdicionadas = pyqtSignal(list)

    def __init__(self, questoes_ja_na_lista: List = None, parent=None):
        super().__init__(parent)
        self.questoes_ja_na_lista = questoes_ja_na_lista or []
        self.ids_na_lista: Set[str] = self._extrair_ids(self.questoes_ja_na_lista)
        self.questoes_selecionadas: Dict[str, Dict] = {}
        self.cards: List[SelectableQuestionCard] = []

        # State
        self.current_filters: Dict[str, Any] = {}
        self.current_page = 1
        self.page_size = 12
        self.total_results = 0
        self.questions_data: List[Dict] = []
        self.selected_discipline_uuid: str = None
        self.selected_discipline_name: str = None

        self.controller = criar_questao_controller()
        self.tag_controller = criar_tag_controller()

        self.setWindowTitle("Selecionar Questões")
        self.setMinimumSize(1100, 700)
        self._setup_ui()
        self._load_data()

        logger.info("QuestaoSelectorDialog inicializado")

    def _extrair_ids(self, questoes) -> Set[str]:
        """Extrai códigos das questões já na lista."""
        ids = set()
        for q in questoes:
            if isinstance(q, dict):
                qid = q.get('codigo') or q.get('uuid')
            else:
                qid = getattr(q, 'codigo', None) or getattr(q, 'uuid', None)
            if qid:
                ids.add(qid)
        return ids

    def _setup_ui(self):
        """Setup the UI layout similar to QuestionBankPage."""
        self.setStyleSheet(f"background-color: {Color.LIGHT_BACKGROUND};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.MD)

        # 1. Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Selecionar Questões", self)
        title_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_PAGE_TITLE};
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            color: {Color.DARK_TEXT};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.results_count_label = QLabel("", self)
        self.results_count_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            color: {Color.GRAY_TEXT};
        """)
        header_layout.addWidget(self.results_count_label)
        main_layout.addLayout(header_layout)

        # Hint
        hint_label = QLabel("Clique nos cards ou marque as checkboxes para selecionar questões. Questões já na lista aparecem em verde.")
        hint_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: {Typography.FONT_SIZE_SM};")
        main_layout.addWidget(hint_label)

        # 2. Filter Bar
        filter_bar_frame = self._create_filter_bar()
        main_layout.addWidget(filter_bar_frame)

        # 3. Selection bar
        selection_bar = self._create_selection_bar()
        main_layout.addLayout(selection_bar)

        # 4. Question Grid (Scrollable)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        self.questions_container = QWidget()
        self.questions_container.setStyleSheet("background-color: transparent;")

        self.grid_layout = QGridLayout(self.questions_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(Spacing.LG)

        self.scroll_area.setWidget(self.questions_container)
        main_layout.addWidget(self.scroll_area)

        # 5. Pagination
        pagination_layout = self._create_pagination()
        main_layout.addLayout(pagination_layout)

        # 6. Footer with buttons
        footer_layout = self._create_footer()
        main_layout.addLayout(footer_layout)

    def _create_filter_bar(self) -> QFrame:
        """Create the filter bar similar to QuestionBankPage."""
        filter_bar_frame = QFrame(self)
        filter_bar_frame.setObjectName("filters")
        filter_bar_frame.setStyleSheet(f"""
            QFrame#filters {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
                padding: {Spacing.SM}px;
            }}
        """)
        filter_bar_layout = QVBoxLayout(filter_bar_frame)
        filter_bar_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        filter_bar_layout.setSpacing(Spacing.SM)

        # First row: Search and filter buttons
        filter_buttons_layout = QHBoxLayout()
        filter_buttons_layout.setSpacing(Spacing.SM)

        # Search Input
        self.search_input = SearchInput(placeholder_text=Text.SEARCH_PLACEHOLDER, parent=self)
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_buttons_layout.addWidget(self.search_input)

        # Filter Dropdowns
        self.source_filter_btn = SecondaryButton("Fonte ▼", parent=self)
        self.source_filter_btn.clicked.connect(self._show_source_menu)
        filter_buttons_layout.addWidget(self.source_filter_btn)

        self.difficulty_filter_btn = SecondaryButton(f"{Text.FILTER_DIFFICULTY} ▼", parent=self)
        self.difficulty_filter_btn.clicked.connect(self._show_difficulty_menu)
        filter_buttons_layout.addWidget(self.difficulty_filter_btn)

        self.type_filter_btn = SecondaryButton(f"{Text.FILTER_TYPE} ▼", parent=self)
        self.type_filter_btn.clicked.connect(self._show_type_menu)
        filter_buttons_layout.addWidget(self.type_filter_btn)

        self.discipline_filter_btn = SecondaryButton("Disciplina ▼", parent=self)
        self.discipline_filter_btn.clicked.connect(self._show_discipline_menu)
        filter_buttons_layout.addWidget(self.discipline_filter_btn)

        self.tag_filter_btn = SecondaryButton("Conteúdo ▼", parent=self)
        self.tag_filter_btn.clicked.connect(self._show_tag_menu)
        self.tag_filter_btn.setEnabled(False)
        filter_buttons_layout.addWidget(self.tag_filter_btn)

        filter_buttons_layout.addStretch()

        self.clear_filters_btn = SecondaryButton("Limpar Filtros", parent=self)
        self.clear_filters_btn.clicked.connect(self._clear_all_filters)
        filter_buttons_layout.addWidget(self.clear_filters_btn)

        filter_bar_layout.addLayout(filter_buttons_layout)

        # Second row: Chips of applied filters
        self.chips_frame = QFrame(self)
        self.chips_frame.setStyleSheet("background-color: transparent;")
        self.chips_container = QHBoxLayout(self.chips_frame)
        self.chips_container.setContentsMargins(0, 0, 0, 0)
        self.chips_container.setSpacing(Spacing.XS)
        self.chips_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.chips_container.addStretch()
        self.chips_frame.hide()
        filter_bar_layout.addWidget(self.chips_frame)

        return filter_bar_frame

    def _create_selection_bar(self) -> QHBoxLayout:
        """Create selection control bar."""
        layout = QHBoxLayout()

        btn_select_all = SecondaryButton("Selecionar Todas", parent=self)
        btn_select_all.clicked.connect(self._select_all)
        layout.addWidget(btn_select_all)

        btn_deselect_all = SecondaryButton("Desmarcar Todas", parent=self)
        btn_deselect_all.clicked.connect(self._deselect_all)
        layout.addWidget(btn_deselect_all)

        layout.addStretch()

        self.selected_count_label = QLabel("0 selecionadas")
        self.selected_count_label.setStyleSheet(f"""
            color: {Color.PRIMARY_BLUE};
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_MD};
        """)
        layout.addWidget(self.selected_count_label)

        return layout

    def _create_pagination(self) -> QHBoxLayout:
        """Create pagination controls."""
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self.prev_page_btn = SecondaryButton("← Anterior", parent=self)
        self.prev_page_btn.clicked.connect(self._go_prev_page)
        pagination_layout.addWidget(self.prev_page_btn)

        self.page_label = QLabel("Página 1", self)
        self.page_label.setStyleSheet(f"""
            color: {Color.DARK_TEXT};
            font-size: {Typography.FONT_SIZE_MD};
            padding: 0 {Spacing.MD}px;
        """)
        pagination_layout.addWidget(self.page_label)

        self.next_page_btn = SecondaryButton("Próximo →", parent=self)
        self.next_page_btn.clicked.connect(self._go_next_page)
        pagination_layout.addWidget(self.next_page_btn)

        pagination_layout.addStretch()
        return pagination_layout

    def _create_footer(self) -> QHBoxLayout:
        """Create footer with action buttons."""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        btn_cancel = SecondaryButton("Cancelar", parent=self)
        btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(btn_cancel)

        # Botão primário com mesmo padrão do SecondaryButton mas com cores de destaque
        self.btn_add = SecondaryButton("Adicionar Selecionadas", parent=self)
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.PRIMARY_BLUE};
                color: {Color.WHITE};
                border: 2px solid {Color.PRIMARY_BLUE};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                padding: {Spacing.SM}px {Spacing.LG}px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {Color.HOVER_BLUE};
                border-color: {Color.HOVER_BLUE};
            }}
            QPushButton:disabled {{
                background-color: {Color.BORDER_LIGHT};
                border-color: {Color.BORDER_LIGHT};
                color: {Color.GRAY_TEXT};
            }}
        """)
        self.btn_add.clicked.connect(self._on_adicionar_clicked)
        self.btn_add.setEnabled(False)
        footer_layout.addWidget(self.btn_add)

        return footer_layout

    def _load_data(self, filters: Optional[Dict] = None):
        """Load questions from the database."""
        try:
            controller_filters = {}

            if filters:
                if 'search' in filters and filters['search']:
                    controller_filters['titulo'] = filters['search']
                if 'fonte' in filters and filters['fonte']:
                    controller_filters['fonte'] = filters['fonte']
                if 'dificuldade' in filters and filters['dificuldade']:
                    controller_filters['dificuldade'] = filters['dificuldade']
                if 'tipo' in filters and filters['tipo']:
                    controller_filters['tipo'] = filters['tipo']
                if 'tags' in filters and filters['tags']:
                    controller_filters['tags'] = filters['tags']

            self.questions_data = QuestaoControllerORM.listar_questoes(
                controller_filters if controller_filters else None
            )

            # Filter only active questions
            self.questions_data = [q for q in self.questions_data if q.get('ativo', True)]

            self.total_results = len(self.questions_data)
            self._update_ui()

        except Exception as e:
            logger.error(f"Error loading questions: {e}", exc_info=True)
            self.questions_data = []
            self.total_results = 0
            self._update_ui()

    def _update_ui(self):
        """Update the UI with loaded data."""
        self._update_results_count()
        self._update_question_grid()
        self._update_pagination()

    def _update_results_count(self):
        """Update the results count label."""
        start = (self.current_page - 1) * self.page_size + 1
        end = min(self.current_page * self.page_size, self.total_results)

        if self.total_results == 0:
            self.results_count_label.setText("Nenhuma questão encontrada")
        else:
            self.results_count_label.setText(f"Mostrando {start}-{end} de {self.total_results:,} questões")

    def _update_question_grid(self):
        """Update the question grid with current page data."""
        # Clear existing cards
        self.cards.clear()
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.grid_layout.removeItem(item)

        if not self.questions_data:
            empty_label = QLabel("Nenhuma questão encontrada", self)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                font-size: {Typography.FONT_SIZE_LG};
                color: {Color.GRAY_TEXT};
                padding: {Spacing.XL}px;
            """)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 3)
            return

        # Get current page questions
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_questions = self.questions_data[start_idx:end_idx]

        if not page_questions:
            empty_label = QLabel("Nenhuma questão nesta página.", self)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                font-size: {Typography.FONT_SIZE_LG};
                color: {Color.GRAY_TEXT};
                padding: {Spacing.XL}px;
            """)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 3)
            return

        # Add question cards
        row = 0
        col = 0
        max_cols = 3

        for q_data in page_questions:
            card = self._create_question_card(q_data)
            self.cards.append(card)
            self.grid_layout.addWidget(card, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Add spacers for empty cells
        while col > 0 and col < max_cols:
            self.grid_layout.addItem(
                QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
                row, col
            )
            col += 1

        # Add vertical spacer at the end
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
            row + 1, 0
        )

    def _create_question_card(self, q_data: Dict) -> SelectableQuestionCard:
        """Create a SelectableQuestionCard from question data."""
        codigo = q_data.get('codigo', 'N/A')
        titulo = q_data.get('titulo')

        if not titulo or not titulo.strip():
            titulo = "Sem título"

        tags = q_data.get('tags', [])
        if isinstance(tags, list):
            tags = [str(tag) for tag in tags if tag]
        else:
            tags = []

        # Map difficulty string to enum
        dificuldade_str = q_data.get('dificuldade', 'MEDIO')
        difficulty_map = {
            'FACIL': DifficultyEnum.EASY,
            'MEDIO': DifficultyEnum.MEDIUM,
            'DIFICIL': DifficultyEnum.HARD,
            'MUITO_DIFICIL': DifficultyEnum.VERY_HARD,
        }
        difficulty = difficulty_map.get(
            dificuldade_str.upper() if dificuldade_str else 'MEDIO',
            DifficultyEnum.MEDIUM
        )

        # Check if question is already in the list
        is_in_list = codigo in self.ids_na_lista

        card = SelectableQuestionCard(
            question_id=f"#{codigo}",
            codigo=codigo,
            title=titulo,
            tags=tags[:3] if tags else [],
            difficulty=difficulty,
            is_in_list=is_in_list,
            parent=self
        )

        card.selection_changed.connect(self._on_selection_changed)
        card.preview_requested.connect(self._on_preview_requested)

        # Restore selection state if was previously selected
        if codigo in self.questoes_selecionadas:
            card.set_selected(True)

        return card

    def _update_pagination(self):
        """Update pagination controls."""
        total_pages = max(1, (self.total_results + self.page_size - 1) // self.page_size)

        self.page_label.setText(f"Página {self.current_page} de {total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)

    def _on_search_changed(self, text: str):
        """Handle search input changes."""
        if text and text.strip():
            self.current_filters['search'] = text.strip()
        else:
            self.current_filters.pop('search', None)
        self.current_page = 1
        self._load_data(self.current_filters)

    def _on_selection_changed(self, codigo: str, is_selected: bool):
        """Handle selection changes from cards."""
        if is_selected:
            # Find the question data
            for q in self.questions_data:
                if q.get('codigo') == codigo:
                    self.questoes_selecionadas[codigo] = q
                    break
        else:
            self.questoes_selecionadas.pop(codigo, None)

        self._update_selection_count()

    def _update_selection_count(self):
        """Update selection count label."""
        count = len(self.questoes_selecionadas)
        self.selected_count_label.setText(f"{count} selecionada{'s' if count != 1 else ''}")
        self.btn_add.setEnabled(count > 0)

    def _on_preview_requested(self, codigo: str):
        """Handle preview request from card."""
        try:
            # Buscar dados completos da questão (mesmo método usado no banco de questões)
            complete_data = QuestaoControllerORM.buscar_questao(codigo)
            if not complete_data:
                logger.warning(f"Questão {codigo} não encontrada no banco de dados")
                return

            # Formatar dados para o preview
            preview_data = self._format_data_for_preview(complete_data)

            # Abrir diálogo de preview
            from src.views.pages.questao_preview_page import QuestaoPreview
            preview_dialog = QuestaoPreview(preview_data, parent=self)
            preview_dialog.exec()

        except Exception as e:
            logger.error(f"Erro ao abrir preview da questão {codigo}: {e}", exc_info=True)

    def _format_data_for_preview(self, questao_data: Dict) -> Dict:
        """Format question data for preview dialog."""
        formatted = {
            'id': questao_data.get('codigo'),
            'codigo': questao_data.get('codigo'),
            'uuid': questao_data.get('uuid'),
            'titulo': questao_data.get('titulo'),
            'tipo': questao_data.get('tipo'),
            'enunciado': questao_data.get('enunciado', ''),
            'ano': questao_data.get('ano'),
            'fonte': questao_data.get('fonte'),
            'dificuldade': questao_data.get('dificuldade'),
            'observacoes': questao_data.get('observacoes'),
            'alternativas': questao_data.get('alternativas', []),
            'tags': questao_data.get('tags', [])
        }

        # Extract resolucao from resposta dict
        resposta = questao_data.get('resposta')
        if resposta:
            if resposta.get('resolucao'):
                formatted['resolucao'] = resposta.get('resolucao')
            elif resposta.get('gabarito_discursivo'):
                formatted['resolucao'] = resposta.get('gabarito_discursivo')

        # Convert tags to simple format
        tags = questao_data.get('tags', [])
        if tags:
            formatted_tags = []
            for tag in tags:
                if isinstance(tag, dict):
                    formatted_tags.append(tag)
                else:
                    formatted_tags.append({'nome': str(tag)})
            formatted['tags'] = formatted_tags

        return formatted

    def _select_all(self):
        """Select all visible questions (not already in list)."""
        for card in self.cards:
            if not card.is_in_list:
                card.set_selected(True)

    def _deselect_all(self):
        """Deselect all questions."""
        for card in self.cards:
            card.set_selected(False)
        self.questoes_selecionadas.clear()
        self._update_selection_count()

    def _go_prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_ui()

    def _go_next_page(self):
        """Go to next page."""
        total_pages = (self.total_results + self.page_size - 1) // self.page_size
        if self.current_page < total_pages:
            self.current_page += 1
            self._update_ui()

    def _show_source_menu(self):
        """Show source filter menu."""
        menu = QMenu(self)
        menu.setStyleSheet(self._get_menu_style())

        action_all = QAction("Todas as Fontes", self)
        action_all.triggered.connect(lambda: self._apply_source_filter(None))
        menu.addAction(action_all)
        menu.addSeparator()

        try:
            fontes = listar_fontes_questao()
            for fonte in fontes:
                sigla = fonte.get('sigla', '')
                action = QAction(sigla, self)
                action.triggered.connect(lambda checked, s=sigla: self._apply_source_filter(s))
                menu.addAction(action)
        except Exception as e:
            logger.error(f"Erro ao carregar fontes: {e}")

        menu.exec(self.source_filter_btn.mapToGlobal(self.source_filter_btn.rect().bottomLeft()))

    def _show_difficulty_menu(self):
        """Show difficulty filter menu."""
        menu = QMenu(self)
        menu.setStyleSheet(self._get_menu_style())

        action_all = QAction("Todas as Dificuldades", self)
        action_all.triggered.connect(lambda: self._apply_difficulty_filter(None))
        menu.addAction(action_all)
        menu.addSeparator()

        difficulties = [
            ("Fácil", "FACIL"),
            ("Médio", "MEDIO"),
            ("Difícil", "DIFICIL")
        ]
        for label, value in difficulties:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, v=value, l=label: self._apply_difficulty_filter(v, l))
            menu.addAction(action)

        menu.exec(self.difficulty_filter_btn.mapToGlobal(self.difficulty_filter_btn.rect().bottomLeft()))

    def _show_type_menu(self):
        """Show type filter menu."""
        menu = QMenu(self)
        menu.setStyleSheet(self._get_menu_style())

        action_all = QAction("Todos os Tipos", self)
        action_all.triggered.connect(lambda: self._apply_type_filter(None))
        menu.addAction(action_all)
        menu.addSeparator()

        types = [
            ("Objetiva", "OBJETIVA"),
            ("Discursiva", "DISCURSIVA")
        ]
        for label, value in types:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, v=value, l=label: self._apply_type_filter(v, l))
            menu.addAction(action)

        menu.exec(self.type_filter_btn.mapToGlobal(self.type_filter_btn.rect().bottomLeft()))

    def _show_discipline_menu(self):
        """Show discipline filter menu."""
        menu = QMenu(self)
        menu.setStyleSheet(self._get_menu_style())

        action_all = QAction("Todas as Disciplinas", self)
        action_all.triggered.connect(lambda: self._apply_discipline_filter(None, None))
        menu.addAction(action_all)
        menu.addSeparator()

        try:
            disciplinas = self.tag_controller.listar_disciplinas()
            for disc in disciplinas:
                uuid = disc.get('uuid')
                nome = disc.get('texto', disc.get('nome', ''))
                action = QAction(nome, self)
                action.triggered.connect(lambda checked, u=uuid, n=nome: self._apply_discipline_filter(u, n))
                menu.addAction(action)
        except Exception as e:
            logger.error(f"Erro ao carregar disciplinas: {e}")

        menu.exec(self.discipline_filter_btn.mapToGlobal(self.discipline_filter_btn.rect().bottomLeft()))

    def _show_tag_menu(self):
        """Show tag/content filter menu."""
        if not self.selected_discipline_uuid:
            return

        from PyQt6.QtWidgets import QWidgetAction, QListWidget, QListWidgetItem, QAbstractItemView

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: 0px;
            }}
        """)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            background-color: {Color.LIGHT_BACKGROUND};
            border-bottom: 1px solid {Color.BORDER_LIGHT};
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 8, 8)

        label = QLabel("Clique para selecionar:")
        label.setStyleSheet(f"font-size: 12px; color: {Color.GRAY_TEXT};")
        header_layout.addWidget(label)
        header_layout.addStretch()

        btn_clear = QPushButton("Limpar")
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                padding: 4px 12px;
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #fee2e2;
                border-color: #f87171;
            }}
        """)
        header_layout.addWidget(btn_clear)
        container_layout.addWidget(header_widget)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        list_widget.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: {Color.WHITE};
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px 16px;
                border-bottom: 1px solid {Color.BORDER_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {Color.LIGHT_BLUE_BG_1};
                color: {Color.PRIMARY_BLUE};
            }}
        """)
        list_widget.setFixedWidth(400)
        list_widget.setMaximumHeight(350)

        current_tags = self.current_filters.get('tags', [])

        try:
            tags = self.tag_controller.listar_tags_por_disciplina(self.selected_discipline_uuid)
            for tag in tags:
                uuid = tag.get('uuid')
                nome = tag.get('caminho_completo', tag.get('nome', ''))
                nome_curto = tag.get('nome', '')
                item = QListWidgetItem(nome)
                item.setData(Qt.ItemDataRole.UserRole, uuid)
                item.setData(Qt.ItemDataRole.UserRole + 1, nome_curto)
                list_widget.addItem(item)
                if uuid in current_tags:
                    item.setSelected(True)
        except Exception as e:
            logger.error(f"Erro ao carregar tags: {e}")

        container_layout.addWidget(list_widget)

        def apply_filter_now():
            selected_items = list_widget.selectedItems()
            selected_tags = []
            selected_names = []
            for item in selected_items:
                uuid = item.data(Qt.ItemDataRole.UserRole)
                nome = item.data(Qt.ItemDataRole.UserRole + 1)
                if uuid:
                    selected_tags.append(uuid)
                    selected_names.append(nome)
            self._apply_tag_filter_multi(selected_tags, selected_names)

        list_widget.itemSelectionChanged.connect(apply_filter_now)

        def on_clear():
            list_widget.clearSelection()

        btn_clear.clicked.connect(on_clear)

        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(container)
        menu.addAction(widget_action)

        menu.exec(self.tag_filter_btn.mapToGlobal(self.tag_filter_btn.rect().bottomLeft()))

    def _get_menu_style(self) -> str:
        """Return common menu stylesheet."""
        return f"""
            QMenu {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: {Spacing.XS}px;
            }}
            QMenu::item {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Dimensions.BORDER_RADIUS_SM};
            }}
            QMenu::item:selected {{
                background-color: {Color.LIGHT_BLUE_BG_1};
                color: {Color.PRIMARY_BLUE};
            }}
        """

    def _apply_source_filter(self, source: Optional[str]):
        """Apply source filter."""
        if source:
            self.current_filters['fonte'] = source
            self.source_filter_btn.setText(f"{source} ▼")
            self._add_filter_chip(f"Fonte: {source}", "fonte")
        else:
            self.current_filters.pop('fonte', None)
            self.source_filter_btn.setText("Fonte ▼")
            self._remove_chip_by_key("fonte")
        self.current_page = 1
        self._load_data(self.current_filters)

    def _apply_difficulty_filter(self, difficulty: Optional[str], label: str = None):
        """Apply difficulty filter."""
        if difficulty:
            self.current_filters['dificuldade'] = difficulty
            self.difficulty_filter_btn.setText(f"{label} ▼")
            self._add_filter_chip(f"Dificuldade: {label}", "dificuldade")
        else:
            self.current_filters.pop('dificuldade', None)
            self.difficulty_filter_btn.setText(f"{Text.FILTER_DIFFICULTY} ▼")
            self._remove_chip_by_key("dificuldade")
        self.current_page = 1
        self._load_data(self.current_filters)

    def _apply_type_filter(self, type_value: Optional[str], label: str = None):
        """Apply type filter."""
        if type_value:
            self.current_filters['tipo'] = type_value
            self.type_filter_btn.setText(f"{label} ▼")
            self._add_filter_chip(f"Tipo: {label}", "tipo")
        else:
            self.current_filters.pop('tipo', None)
            self.type_filter_btn.setText(f"{Text.FILTER_TYPE} ▼")
            self._remove_chip_by_key("tipo")
        self.current_page = 1
        self._load_data(self.current_filters)

    def _apply_discipline_filter(self, uuid: Optional[str], name: Optional[str]):
        """Apply discipline filter."""
        if uuid:
            self.selected_discipline_uuid = uuid
            self.selected_discipline_name = name
            self.discipline_filter_btn.setText(f"{name} ▼")
            self._add_filter_chip(f"Disciplina: {name}", "disciplina")
            self.tag_filter_btn.setEnabled(True)
        else:
            self.selected_discipline_uuid = None
            self.selected_discipline_name = None
            self.discipline_filter_btn.setText("Disciplina ▼")
            self._remove_chip_by_key("disciplina")
            self.tag_filter_btn.setEnabled(False)
            self.tag_filter_btn.setText("Conteúdo ▼")
            self.current_filters.pop('tags', None)
            self._remove_chip_by_key("tag")

        self.current_page = 1
        self._load_data(self.current_filters)

    def _apply_tag_filter_multi(self, uuids: List[str], names: List[str]):
        """Apply multiple tag/content filters."""
        if uuids and len(uuids) > 0:
            self.current_filters['tags'] = uuids
            if len(names) == 1:
                self.tag_filter_btn.setText(f"{names[0]} ▼")
                self._add_filter_chip(f"Conteúdo: {names[0]}", "tag")
            else:
                self.tag_filter_btn.setText(f"{len(names)} conteúdos ▼")
                if len(names) <= 2:
                    chip_text = " ou ".join(names)
                else:
                    chip_text = f"{names[0]}, {names[1]} +{len(names)-2}"
                self._add_filter_chip(f"Conteúdos: {chip_text}", "tag")
        else:
            self.current_filters.pop('tags', None)
            self.tag_filter_btn.setText("Conteúdo ▼")
            self._remove_chip_by_key("tag")
        self.current_page = 1
        self._load_data(self.current_filters)

    def _add_filter_chip(self, text: str, filter_key: str):
        """Add a filter chip to the filter bar."""
        self._remove_chip_by_key(filter_key)

        chip = FilterChip(text, filter_key, self)
        chip.removed.connect(self._remove_filter)
        self.chips_container.insertWidget(self.chips_container.count() - 1, chip)
        self.chips_frame.show()

    def _remove_chip_by_key(self, filter_key: str):
        """Remove a chip by its filter key."""
        for i in range(self.chips_container.count()):
            item = self.chips_container.itemAt(i)
            if item and item.widget():
                chip = item.widget()
                if isinstance(chip, FilterChip) and chip.filter_key == filter_key:
                    chip.deleteLater()
                    break

    def _remove_filter(self, filter_key: str):
        """Remove a filter and refresh data."""
        if filter_key == 'tags' or filter_key == 'tag':
            self.current_filters.pop('tags', None)
        elif filter_key in self.current_filters:
            del self.current_filters[filter_key]

        if filter_key == 'fonte':
            self.source_filter_btn.setText("Fonte ▼")
        elif filter_key == 'dificuldade':
            self.difficulty_filter_btn.setText(f"{Text.FILTER_DIFFICULTY} ▼")
        elif filter_key == 'tipo':
            self.type_filter_btn.setText(f"{Text.FILTER_TYPE} ▼")
        elif filter_key == 'disciplina':
            self.discipline_filter_btn.setText("Disciplina ▼")
            self.selected_discipline_uuid = None
            self.selected_discipline_name = None
            self.tag_filter_btn.setText("Conteúdo ▼")
            self.tag_filter_btn.setEnabled(False)
            self.current_filters.pop('tags', None)
            self._remove_chip_by_key("tag")
        elif filter_key == 'tag':
            self.tag_filter_btn.setText("Conteúdo ▼")

        for i in range(self.chips_container.count()):
            item = self.chips_container.itemAt(i)
            if item and item.widget():
                chip = item.widget()
                if isinstance(chip, FilterChip) and chip.filter_key == filter_key:
                    chip.deleteLater()
                    break

        self._update_chips_visibility()
        self.current_page = 1
        self._load_data(self.current_filters)

    def _update_chips_visibility(self):
        """Update chips frame visibility."""
        has_chips = False
        for i in range(self.chips_container.count()):
            item = self.chips_container.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), FilterChip):
                has_chips = True
                break
        if has_chips:
            self.chips_frame.show()
        else:
            self.chips_frame.hide()

    def _clear_all_filters(self):
        """Clear all filters and reset UI."""
        self.current_filters = {}
        self.selected_discipline_uuid = None
        self.selected_discipline_name = None

        self.search_input.clear()

        self.source_filter_btn.setText("Fonte ▼")
        self.difficulty_filter_btn.setText(f"{Text.FILTER_DIFFICULTY} ▼")
        self.type_filter_btn.setText(f"{Text.FILTER_TYPE} ▼")
        self.discipline_filter_btn.setText("Disciplina ▼")
        self.tag_filter_btn.setText("Conteúdo ▼")
        self.tag_filter_btn.setEnabled(False)

        while self.chips_container.count():
            item = self.chips_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        self.chips_frame.hide()

        self.current_page = 1
        self._load_data()

    def _on_adicionar_clicked(self):
        """Add selected questions and close dialog."""
        if not self.questoes_selecionadas:
            return

        questoes_completas = []
        for codigo, q_data in self.questoes_selecionadas.items():
            questao_completa = self.controller.obter_questao_completa(codigo)
            if questao_completa:
                questoes_completas.append(questao_completa)

        if questoes_completas:
            self.questoesAdicionadas.emit(questoes_completas)
            logger.info(f"{len(questoes_completas)} questões adicionadas")

        self.accept()


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from src.views.design.theme import ThemeManager
    ThemeManager.apply_global_theme(app)

    dialog = QuestaoSelectorDialog(questoes_ja_na_lista=[])
    dialog.questoesAdicionadas.connect(lambda qs: print(f"Added: {len(qs)} questions"))
    dialog.exec()
