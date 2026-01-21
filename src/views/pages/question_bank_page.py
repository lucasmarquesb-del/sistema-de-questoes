# src/views/pages/question_bank_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QScrollArea, QSizePolicy, QSpacerItem, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from typing import Dict, List, Any, Optional

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text, IconPath
from src.views.design.enums import DifficultyEnum
from src.views.components.common.inputs import SearchInput
from src.views.components.common.buttons import PrimaryButton, SecondaryButton
from src.views.components.common.cards import QuestionCard
from src.controllers.questao_controller_orm import QuestaoControllerORM


class FilterChip(QFrame):
    """A removable filter chip/badge."""
    removed = pyqtSignal(str)  # Emits the filter key when removed

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


class QuestionBankPage(QWidget):
    """
    Page displaying a bank of questions with search, filters, and pagination.
    Data is fetched from the database via controllers.
    """
    filter_changed = pyqtSignal(dict)
    page_changed = pyqtSignal(int)
    question_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("question_bank_page")

        # State
        self.current_filters: Dict[str, Any] = {}
        self.current_page = 1
        self.page_size = 12
        self.total_results = 0
        self.questions_data: List[Dict] = []
        self.selected_tag_path: str = ""

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # 1. Breadcrumb
        self.breadcrumb_label = QLabel("", self)
        self.breadcrumb_label.setObjectName("breadcrumb_label")
        self.breadcrumb_label.setStyleSheet(f"""
            color: {Color.GRAY_TEXT};
            font-size: {Typography.FONT_SIZE_MD};
        """)
        main_layout.addWidget(self.breadcrumb_label)

        # 2. Page Header
        header_layout = QHBoxLayout()

        page_title = QLabel(Text.QUESTION_BANK_TITLE, self)
        page_title.setObjectName("page_title")
        page_title.setStyleSheet(f"""
            QLabel#page_title {{
                font-size: {Typography.FONT_SIZE_PAGE_TITLE};
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                color: {Color.DARK_TEXT};
            }}
        """)
        header_layout.addWidget(page_title)
        header_layout.addStretch()

        self.results_count_label = QLabel("", self)
        self.results_count_label.setObjectName("results_count")
        self.results_count_label.setStyleSheet(f"""
            QLabel#results_count {{
                font-size: {Typography.FONT_SIZE_MD};
                color: {Color.GRAY_TEXT};
            }}
        """)
        header_layout.addWidget(self.results_count_label)
        main_layout.addLayout(header_layout)

        # 3. Filter Bar
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
        filter_layout = QHBoxLayout(filter_bar_frame)
        filter_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        filter_layout.setSpacing(Spacing.SM)

        # Search Input
        self.search_input = SearchInput(placeholder_text=Text.SEARCH_PLACEHOLDER, parent=self)
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_input)

        # Filter Chips Container
        self.chips_container = QHBoxLayout()
        self.chips_container.setSpacing(Spacing.XS)
        filter_layout.addLayout(self.chips_container)

        # Filter Dropdowns
        self.source_filter_btn = SecondaryButton("ENEM ▼", parent=self)
        self.source_filter_btn.clicked.connect(self._show_source_menu)
        filter_layout.addWidget(self.source_filter_btn)

        self.difficulty_filter_btn = SecondaryButton(f"{Text.FILTER_DIFFICULTY} ▼", parent=self)
        self.difficulty_filter_btn.clicked.connect(self._show_difficulty_menu)
        filter_layout.addWidget(self.difficulty_filter_btn)

        self.type_filter_btn = SecondaryButton(f"{Text.FILTER_TYPE} ▼", parent=self)
        self.type_filter_btn.clicked.connect(self._show_type_menu)
        filter_layout.addWidget(self.type_filter_btn)

        filter_layout.addStretch()

        filters_btn = SecondaryButton(f"≡ {Text.QUESTION_BANK_FILTERS}", parent=self)
        filter_layout.addWidget(filters_btn)

        main_layout.addWidget(filter_bar_frame)

        # 4. Question Grid (Scrollable)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("main_scroll")
        self.scroll_area.setStyleSheet(f"""
            QScrollArea#main_scroll {{
                border: none;
                background-color: transparent;
            }}
        """)

        self.questions_container = QWidget()
        self.questions_container.setObjectName("questions_container")
        self.questions_container.setStyleSheet("background-color: transparent;")

        self.grid_layout = QGridLayout(self.questions_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(Spacing.LG)

        self.scroll_area.setWidget(self.questions_container)
        main_layout.addWidget(self.scroll_area)

        # 5. Pagination
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
        main_layout.addLayout(pagination_layout)

    def _load_data(self, filters: Optional[Dict] = None):
        """Load questions from the database."""
        try:
            # Build filter dict for controller
            controller_filters = {}

            if filters:
                if 'search' in filters and filters['search']:
                    controller_filters['titulo'] = filters['search']
                if 'fonte' in filters:
                    controller_filters['fonte'] = filters['fonte']
                if 'dificuldade' in filters:
                    controller_filters['dificuldade'] = filters['dificuldade']
                if 'tipo' in filters:
                    controller_filters['tipo'] = filters['tipo']
                if 'tags' in filters:
                    controller_filters['tags'] = filters['tags']

            # Fetch questions
            self.questions_data = QuestaoControllerORM.listar_questoes(
                controller_filters if controller_filters else None
            )

            self.total_results = len(self.questions_data)
            self._update_ui()

        except Exception as e:
            print(f"Error loading questions: {e}")
            self.questions_data = []
            self._update_ui()

    def _update_ui(self):
        """Update the UI with loaded data."""
        self._update_breadcrumb()
        self._update_results_count()
        self._update_question_grid()
        self._update_pagination()

    def _update_breadcrumb(self):
        """Update breadcrumb based on selected tag path."""
        if self.selected_tag_path:
            self.breadcrumb_label.setText(self.selected_tag_path)
            self.breadcrumb_label.show()
        else:
            self.breadcrumb_label.hide()

    def _update_results_count(self):
        """Update the results count label."""
        start = (self.current_page - 1) * self.page_size + 1
        end = min(self.current_page * self.page_size, self.total_results)

        if self.total_results == 0:
            self.results_count_label.setText(Text.EMPTY_NO_QUESTIONS)
        else:
            text = Text.QUESTION_BANK_SHOWING.format(
                current=f"{start}-{end}",
                total=f"{self.total_results:,}"
            )
            self.results_count_label.setText(text)

    def _update_question_grid(self):
        """Update the question grid with current page data."""
        # Clear existing cards
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get current page questions
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_questions = self.questions_data[start_idx:end_idx]

        # Add question cards
        row = 0
        col = 0
        max_cols = 3

        for q_data in page_questions:
            card = self._create_question_card(q_data)
            card.mousePressEvent = lambda e, uuid=q_data.get('uuid'): self._on_question_clicked(uuid)
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

    def _create_question_card(self, q_data: Dict) -> QuestionCard:
        """Create a QuestionCard from question data."""
        codigo = q_data.get('codigo', 'N/A')
        titulo = q_data.get('titulo', q_data.get('enunciado', '')[:50] + '...')
        enunciado = q_data.get('enunciado', '')
        tags = q_data.get('tags', [])
        dificuldade_str = q_data.get('dificuldade', 'MEDIO')

        # Map difficulty string to enum
        difficulty_map = {
            'FACIL': DifficultyEnum.EASY,
            'MEDIO': DifficultyEnum.MEDIUM,
            'DIFICIL': DifficultyEnum.HARD,
            'MUITO_DIFICIL': DifficultyEnum.VERY_HARD,
        }
        difficulty = difficulty_map.get(dificuldade_str, DifficultyEnum.MEDIUM)

        # Extract LaTeX formula from enunciado if present
        formula = None
        if '$$' in enunciado:
            start = enunciado.find('$$')
            end = enunciado.find('$$', start + 2)
            if end > start:
                formula = enunciado[start:end+2]
        elif '$' in enunciado:
            start = enunciado.find('$')
            end = enunciado.find('$', start + 1)
            if end > start:
                formula = enunciado[start:end+1]

        return QuestionCard(
            question_id=f"#{codigo}",
            title=titulo if titulo else "Sem título",
            formula=formula,
            tags=tags[:3] if tags else [],  # Limit to 3 tags
            difficulty=difficulty,
            parent=self
        )

    def _update_pagination(self):
        """Update pagination controls."""
        total_pages = max(1, (self.total_results + self.page_size - 1) // self.page_size)

        self.page_label.setText(f"Página {self.current_page} de {total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)

    def _on_search_changed(self, text: str):
        """Handle search input changes."""
        self.current_filters['search'] = text
        self.current_page = 1
        self._load_data(self.current_filters)
        self.filter_changed.emit(self.current_filters)

    def _on_question_clicked(self, uuid: str):
        """Handle question card click."""
        if uuid:
            self.question_selected.emit(uuid)

    def _go_prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_ui()
            self.page_changed.emit(self.current_page)

    def _go_next_page(self):
        """Go to next page."""
        total_pages = (self.total_results + self.page_size - 1) // self.page_size
        if self.current_page < total_pages:
            self.current_page += 1
            self._update_ui()
            self.page_changed.emit(self.current_page)

    def _show_source_menu(self):
        """Show source filter menu."""
        # TODO: Implement dropdown menu with sources from database
        pass

    def _show_difficulty_menu(self):
        """Show difficulty filter menu."""
        # TODO: Implement dropdown menu
        pass

    def _show_type_menu(self):
        """Show type filter menu."""
        # TODO: Implement dropdown menu
        pass

    def _add_filter_chip(self, text: str, filter_key: str):
        """Add a filter chip to the filter bar."""
        chip = FilterChip(text, filter_key, self)
        chip.removed.connect(self._remove_filter)
        self.chips_container.addWidget(chip)

    def _remove_filter(self, filter_key: str):
        """Remove a filter and refresh data."""
        if filter_key in self.current_filters:
            del self.current_filters[filter_key]

        # Remove chip widget
        for i in range(self.chips_container.count()):
            item = self.chips_container.itemAt(i)
            if item and item.widget():
                chip = item.widget()
                if isinstance(chip, FilterChip) and chip.filter_key == filter_key:
                    chip.deleteLater()
                    break

        self.current_page = 1
        self._load_data(self.current_filters)

    def set_tag_filter(self, tag_uuid: str, tag_path: str):
        """Set tag filter from sidebar selection."""
        self.selected_tag_path = tag_path
        self.current_filters['tags'] = [tag_uuid]
        self.current_page = 1
        self._load_data(self.current_filters)

    def refresh_data(self):
        """Public method to refresh question list."""
        self._load_data(self.current_filters)


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
            self.setWindowTitle("Question Bank Page Test")
            self.setGeometry(100, 100, 1200, 800)

            self.question_bank_page = QuestionBankPage(self)
            self.setCentralWidget(self.question_bank_page)

            self.question_bank_page.filter_changed.connect(
                lambda filters: print(f"Filters applied: {filters}")
            )
            self.question_bank_page.page_changed.connect(
                lambda page_num: print(f"Page changed to: {page_num}")
            )
            self.question_bank_page.question_selected.connect(
                lambda q_uuid: print(f"Question selected: {q_uuid}")
            )

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
