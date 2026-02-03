# src/views/pages/question_bank_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QScrollArea, QSizePolicy, QSpacerItem, QFrame, QPushButton, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction
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
    edit_question_requested = pyqtSignal(object)  # Emite questao_data para edição
    create_variant_requested = pyqtSignal(object)  # Emite questao_data para criar variante

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
        self.selected_discipline_uuid: str = None  # UUID da disciplina selecionada
        self.selected_discipline_name: str = None  # Nome da disciplina selecionada

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
        filter_bar_layout = QVBoxLayout(filter_bar_frame)
        filter_bar_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        filter_bar_layout.setSpacing(Spacing.SM)

        # Primeira linha: Busca e botões de filtro
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
        self.tag_filter_btn.setEnabled(False)  # Desabilitado até selecionar disciplina
        filter_buttons_layout.addWidget(self.tag_filter_btn)

        filter_buttons_layout.addStretch()

        self.clear_filters_btn = SecondaryButton("Limpar Filtros", parent=self)
        self.clear_filters_btn.clicked.connect(self._clear_all_filters)
        filter_buttons_layout.addWidget(self.clear_filters_btn)

        filter_bar_layout.addLayout(filter_buttons_layout)

        # Segunda linha: Chips de filtros aplicados
        self.chips_frame = QFrame(self)
        self.chips_frame.setObjectName("chips_frame")
        self.chips_frame.setStyleSheet(f"""
            QFrame#chips_frame {{
                background-color: transparent;
            }}
        """)
        self.chips_container = QHBoxLayout(self.chips_frame)
        self.chips_container.setContentsMargins(0, 0, 0, 0)
        self.chips_container.setSpacing(Spacing.XS)
        self.chips_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.chips_container.addStretch()
        self.chips_frame.hide()  # Esconder quando não há filtros
        filter_bar_layout.addWidget(self.chips_frame)

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
        """Load questions from the database (only main questions, not variants)."""
        try:
            # Build filter dict for controller
            controller_filters = {}

            if filters:
                if 'search' in filters and filters['search']:
                    # Buscar por título ou enunciado
                    controller_filters['titulo'] = filters['search']
                if 'fonte' in filters and filters['fonte']:
                    controller_filters['fonte'] = filters['fonte']
                if 'dificuldade' in filters and filters['dificuldade']:
                    controller_filters['dificuldade'] = filters['dificuldade']
                if 'tipo' in filters and filters['tipo']:
                    controller_filters['tipo'] = filters['tipo']
                if 'tags' in filters and filters['tags']:
                    # Se tags é uma lista de UUIDs, converter para nomes se necessário
                    controller_filters['tags'] = filters['tags']

            # Fetch only main questions (not variants) from database
            # This method includes 'quantidade_variantes' in each question dict
            self.questions_data = QuestaoControllerORM.listar_questoes_principais(
                controller_filters if controller_filters else None
            )

            # Filtrar apenas questões ativas
            self.questions_data = [q for q in self.questions_data if q.get('ativo', True)]

            self.total_results = len(self.questions_data)
            self._update_ui()

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading questions: {e}", exc_info=True)
            self.questions_data = []
            self.total_results = 0
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
            elif item.spacerItem():
                self.grid_layout.removeItem(item)

        # Check if we have questions
        if not self.questions_data:
            # Show empty state message
            empty_label = QLabel(Text.EMPTY_NO_QUESTIONS, self)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                QLabel {{
                    font-size: {Typography.FONT_SIZE_LG};
                    color: {Color.GRAY_TEXT};
                    padding: {Spacing.XL}px;
                }}
            """)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 3)
            return

        # Get current page questions
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_questions = self.questions_data[start_idx:end_idx]

        if not page_questions:
            # No questions on this page
            empty_label = QLabel("Nenhuma questão nesta página.", self)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                QLabel {{
                    font-size: {Typography.FONT_SIZE_LG};
                    color: {Color.GRAY_TEXT};
                    padding: {Spacing.XL}px;
                }}
            """)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 3)
            return

        # Add question cards
        row = 0
        col = 0
        max_cols = 3

        for q_data in page_questions:
            card = self._create_question_card(q_data)
            # Store UUID for click handling
            question_uuid = q_data.get('uuid')
            if question_uuid:
                # Create a wrapper function to capture the UUID correctly
                def make_click_handler(uuid):
                    def click_handler(event):
                        self._on_question_clicked(uuid)
                    return click_handler
                card.mousePressEvent = make_click_handler(question_uuid)
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
        # Extract data from database response
        codigo = q_data.get('codigo', 'N/A')
        titulo = q_data.get('titulo')

        # Usar apenas o título - não mostrar enunciado no card
        if not titulo or not titulo.strip():
            titulo = "Sem título"

        # Get tags (list of tag names)
        tags = q_data.get('tags', [])
        if isinstance(tags, list):
            # Ensure tags are strings
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
        difficulty = difficulty_map.get(dificuldade_str.upper() if dificuldade_str else 'MEDIO', DifficultyEnum.MEDIUM)

        # Get variant count (available when using listar_questoes_principais)
        variant_count = q_data.get('quantidade_variantes', 0)

        return QuestionCard(
            question_id=f"#{codigo}",
            title=titulo,
            formula=None,  # Não mostrar fórmulas no card para padronizar
            tags=tags[:3] if tags else [],  # Limit to 3 tags for display
            difficulty=difficulty,
            variant_count=variant_count,
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
        if text and text.strip():
            self.current_filters['search'] = text.strip()
        else:
            self.current_filters.pop('search', None)
        self.current_page = 1
        self._load_data(self.current_filters)
        self.filter_changed.emit(self.current_filters)

    def _on_question_clicked(self, uuid: str):
        """Handle question card click."""
        if not uuid:
            return
        
        try:
            # Find the question data to get the code
            questao_data = None
            for q in self.questions_data:
                if q.get('uuid') == uuid:
                    questao_data = q
                    break
            
            if not questao_data:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Questão com UUID {uuid} não encontrada nos dados carregados")
                return
            
            # Get question code
            codigo = questao_data.get('codigo')
            if not codigo:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Questão com UUID {uuid} não possui código")
                return
            
            # Fetch complete question data from database
            complete_data = QuestaoControllerORM.buscar_questao(codigo)
            if not complete_data:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Questão {codigo} não encontrada no banco de dados")
                return
            
            # Format data for preview (adjust format if needed)
            preview_data = self._format_data_for_preview(complete_data)
            
            # Open preview dialog
            from src.views.pages.questao_preview_page import QuestaoPreview
            preview_dialog = QuestaoPreview(preview_data, parent=self)
            preview_dialog.edit_requested.connect(self._on_edit_question_requested)
            preview_dialog.create_variant_requested.connect(self._on_create_variant_requested)
            preview_dialog.exec()

            # Emit signal for other components
            self.question_selected.emit(uuid)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao abrir preview da questão: {e}", exc_info=True)
    
    def _format_data_for_preview(self, questao_data: Dict) -> Dict:
        """
        Format question data for preview dialog.
        Converts the format from service to what preview expects.
        """
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
            'tags': questao_data.get('tags', []),
            'niveis_escolares': questao_data.get('niveis_escolares', [])
        }
        
        # Extract resolucao from resposta dict
        resposta = questao_data.get('resposta')
        if resposta:
            # For objective questions, use resolucao
            if resposta.get('resolucao'):
                formatted['resolucao'] = resposta.get('resolucao')
            # For discursive questions, use gabarito_discursivo as resolucao
            elif resposta.get('gabarito_discursivo'):
                formatted['resolucao'] = resposta.get('gabarito_discursivo')
        
        # Convert tags to simple format (list of strings or dicts with 'nome')
        tags = questao_data.get('tags', [])
        if tags:
            formatted_tags = []
            for tag in tags:
                if isinstance(tag, dict):
                    # Keep dict format but ensure 'nome' exists
                    formatted_tags.append(tag)
                else:
                    formatted_tags.append({'nome': str(tag)})
            formatted['tags'] = formatted_tags
        
        return formatted

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
        menu = QMenu(self)
        menu.setStyleSheet(f"""
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
        """)

        # Opção para limpar filtro
        action_all = QAction("Todas as Fontes", self)
        action_all.triggered.connect(lambda: self._apply_source_filter(None))
        menu.addAction(action_all)
        menu.addSeparator()

        # Buscar fontes do banco de dados
        try:
            from src.controllers.adapters import listar_fontes_questao
            fontes = listar_fontes_questao()
            for fonte in fontes:
                sigla = fonte.get('sigla', '')
                action = QAction(sigla, self)
                action.triggered.connect(lambda checked, s=sigla: self._apply_source_filter(s))
                menu.addAction(action)
        except Exception as e:
            print(f"Erro ao carregar fontes: {e}")

        menu.exec(self.source_filter_btn.mapToGlobal(self.source_filter_btn.rect().bottomLeft()))

    def _show_difficulty_menu(self):
        """Show difficulty filter menu."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
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
        """)

        # Opção para limpar filtro
        action_all = QAction("Todas as Dificuldades", self)
        action_all.triggered.connect(lambda: self._apply_difficulty_filter(None))
        menu.addAction(action_all)
        menu.addSeparator()

        # Opções de dificuldade
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
        menu.setStyleSheet(f"""
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
        """)

        # Opção para limpar filtro
        action_all = QAction("Todos os Tipos", self)
        action_all.triggered.connect(lambda: self._apply_type_filter(None))
        menu.addAction(action_all)
        menu.addSeparator()

        # Opções de tipo
        types = [
            ("Objetiva", "OBJETIVA"),
            ("Discursiva", "DISCURSIVA")
        ]
        for label, value in types:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, v=value, l=label: self._apply_type_filter(v, l))
            menu.addAction(action)

        menu.exec(self.type_filter_btn.mapToGlobal(self.type_filter_btn.rect().bottomLeft()))

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

    def _show_discipline_menu(self):
        """Show discipline filter menu."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
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
        """)

        # Opção para limpar filtro
        action_all = QAction("Todas as Disciplinas", self)
        action_all.triggered.connect(lambda: self._apply_discipline_filter(None, None))
        menu.addAction(action_all)
        menu.addSeparator()

        # Buscar disciplinas do banco de dados
        try:
            from src.controllers.adapters import criar_tag_controller
            tag_controller = criar_tag_controller()
            disciplinas = tag_controller.listar_disciplinas()
            for disc in disciplinas:
                uuid = disc.get('uuid')
                nome = disc.get('texto', disc.get('nome', ''))
                action = QAction(nome, self)
                action.triggered.connect(lambda checked, u=uuid, n=nome: self._apply_discipline_filter(u, n))
                menu.addAction(action)
        except Exception as e:
            print(f"Erro ao carregar disciplinas: {e}")

        menu.exec(self.discipline_filter_btn.mapToGlobal(self.discipline_filter_btn.rect().bottomLeft()))

    def _show_tag_menu(self):
        """Show tag/content filter menu with multi-select."""
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

        # Container principal
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header com label e botão limpar
        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {Color.LIGHT_BACKGROUND};
                border-bottom: 1px solid {Color.BORDER_LIGHT};
            }}
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
                color: {Color.DARK_TEXT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #fee2e2;
                border-color: #f87171;
            }}
        """)
        header_layout.addWidget(btn_clear)
        container_layout.addWidget(header_widget)

        # Criar widget de lista scrollável com multi-seleção
        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        list_widget.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: {Color.WHITE};
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 16px;
                border-bottom: 1px solid {Color.BORDER_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {Color.LIGHT_BLUE_BG_1};
                color: {Color.PRIMARY_BLUE};
            }}
            QListWidget::item:hover {{
                background-color: {Color.LIGHT_BACKGROUND};
            }}
        """)
        list_widget.setFixedWidth(400)
        list_widget.setMaximumHeight(350)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Tags atualmente selecionadas
        current_tags = self.current_filters.get('tags', [])

        # Buscar tags da disciplina selecionada
        try:
            from src.controllers.adapters import criar_tag_controller
            tag_controller = criar_tag_controller()
            tags = tag_controller.listar_tags_por_disciplina(self.selected_discipline_uuid)
            for tag in tags:
                uuid = tag.get('uuid')
                nome = tag.get('caminho_completo', tag.get('nome', ''))
                nome_curto = tag.get('nome', '')
                item = QListWidgetItem(nome)
                item.setData(Qt.ItemDataRole.UserRole, uuid)
                item.setData(Qt.ItemDataRole.UserRole + 1, nome_curto)
                list_widget.addItem(item)
                # Marcar como selecionado se já estiver no filtro
                if uuid in current_tags:
                    item.setSelected(True)
        except Exception as e:
            print(f"Erro ao carregar tags: {e}")

        container_layout.addWidget(list_widget)

        # Função para aplicar filtro imediatamente
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

        # Handler para seleção - aplica filtro imediatamente
        list_widget.itemSelectionChanged.connect(apply_filter_now)

        # Handler para limpar
        def on_clear():
            list_widget.clearSelection()
            # apply_filter_now será chamado automaticamente via itemSelectionChanged

        btn_clear.clicked.connect(on_clear)

        # Adicionar container ao menu via QWidgetAction
        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(container)
        menu.addAction(widget_action)

        # Posicionar e mostrar o menu
        pos = self.tag_filter_btn.mapToGlobal(self.tag_filter_btn.rect().bottomLeft())
        menu.exec(pos)

    def _apply_discipline_filter(self, uuid: Optional[str], name: Optional[str]):
        """Apply discipline filter."""
        if uuid:
            self.selected_discipline_uuid = uuid
            self.selected_discipline_name = name
            self.discipline_filter_btn.setText(f"{name} ▼")
            self._add_filter_chip(f"Disciplina: {name}", "disciplina")
            # Habilitar botão de tags
            self.tag_filter_btn.setEnabled(True)
        else:
            self.selected_discipline_uuid = None
            self.selected_discipline_name = None
            self.discipline_filter_btn.setText("Disciplina ▼")
            self._remove_chip_by_key("disciplina")
            # Desabilitar e resetar botão de tags
            self.tag_filter_btn.setEnabled(False)
            self.tag_filter_btn.setText("Conteúdo ▼")
            # Remover filtro de tag também
            self.current_filters.pop('tags', None)
            self._remove_chip_by_key("tag")

        # Nota: disciplina não filtra diretamente, apenas habilita o filtro de tags
        self.current_page = 1
        self._load_data(self.current_filters)

    def _apply_tag_filter(self, uuid: Optional[str], name: Optional[str]):
        """Apply tag/content filter."""
        if uuid:
            self.current_filters['tags'] = [uuid]
            self.tag_filter_btn.setText(f"{name} ▼")
            self._add_filter_chip(f"Conteúdo: {name}", "tag")
        else:
            self.current_filters.pop('tags', None)
            self.tag_filter_btn.setText("Conteúdo ▼")
            self._remove_chip_by_key("tag")
        self.current_page = 1
        self._load_data(self.current_filters)

    def _apply_tag_filter_multi(self, uuids: List[str], names: List[str]):
        """Apply multiple tag/content filters with OR logic."""
        if uuids and len(uuids) > 0:
            self.current_filters['tags'] = uuids
            if len(names) == 1:
                self.tag_filter_btn.setText(f"{names[0]} ▼")
                self._add_filter_chip(f"Conteúdo: {names[0]}", "tag")
            else:
                self.tag_filter_btn.setText(f"{len(names)} conteúdos ▼")
                # Criar texto resumido para o chip
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

    def _remove_chip_by_key(self, filter_key: str):
        """Remove a chip by its filter key."""
        for i in range(self.chips_container.count()):
            item = self.chips_container.itemAt(i)
            if item and item.widget():
                chip = item.widget()
                if isinstance(chip, FilterChip) and chip.filter_key == filter_key:
                    chip.deleteLater()
                    break

    def _clear_all_filters(self):
        """Clear all filters and reset UI."""
        # Limpar filtros
        self.current_filters = {}
        self.selected_tag_path = ""
        self.selected_discipline_uuid = None
        self.selected_discipline_name = None

        # Limpar busca
        self.search_input.clear()

        # Resetar textos dos botões
        self.source_filter_btn.setText("Fonte ▼")
        self.difficulty_filter_btn.setText(f"{Text.FILTER_DIFFICULTY} ▼")
        self.type_filter_btn.setText(f"{Text.FILTER_TYPE} ▼")
        self.discipline_filter_btn.setText("Disciplina ▼")
        self.tag_filter_btn.setText("Conteúdo ▼")
        self.tag_filter_btn.setEnabled(False)

        # Remover todos os chips
        while self.chips_container.count():
            item = self.chips_container.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Esconder linha de chips
        self.chips_frame.hide()

        # Recarregar dados
        self.current_page = 1
        self._load_data()

    def _add_filter_chip(self, text: str, filter_key: str):
        """Add a filter chip to the filter bar."""
        # Primeiro verificar se já existe um chip com essa chave e removê-lo
        self._remove_chip_by_key(filter_key)

        chip = FilterChip(text, filter_key, self)
        chip.removed.connect(self._remove_filter)
        # Inserir antes do stretch
        self.chips_container.insertWidget(self.chips_container.count() - 1, chip)

        # Mostrar a linha de chips
        self.chips_frame.show()

    def _remove_filter(self, filter_key: str):
        """Remove a filter and refresh data."""
        if filter_key == 'tags' or filter_key == 'tag':
            self.current_filters.pop('tags', None)
        elif filter_key in self.current_filters:
            del self.current_filters[filter_key]

        # Reset button text based on filter key
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
            # Também limpar tag quando disciplina é removida
            self.tag_filter_btn.setText("Conteúdo ▼")
            self.tag_filter_btn.setEnabled(False)
            self.current_filters.pop('tags', None)
            self._remove_chip_by_key("tag")
        elif filter_key == 'tag':
            self.tag_filter_btn.setText("Conteúdo ▼")

        # Remove chip widget
        for i in range(self.chips_container.count()):
            item = self.chips_container.itemAt(i)
            if item and item.widget():
                chip = item.widget()
                if isinstance(chip, FilterChip) and chip.filter_key == filter_key:
                    chip.deleteLater()
                    break

        # Esconder linha de chips se não houver mais chips (apenas o stretch)
        self._update_chips_visibility()

        self.current_page = 1
        self._load_data(self.current_filters)

    def _update_chips_visibility(self):
        """Atualiza a visibilidade da linha de chips."""
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

    def set_tag_filter(self, tag_uuid: str, tag_path: str):
        """Set tag filter from sidebar selection."""
        self.selected_tag_path = tag_path
        if tag_uuid:
            self.current_filters['tags'] = [tag_uuid]
        else:
            self.current_filters.pop('tags', None)
            self.selected_tag_path = ""
        self.current_page = 1
        self._load_data(self.current_filters)

    def refresh_data(self):
        """Public method to refresh question list."""
        self._load_data(self.current_filters)

    def _on_edit_question_requested(self, questao_data: Dict):
        """Handler para abrir formulário de edição de questão."""
        # Emitir sinal para que a MainWindow abra o formulário de edição
        self.edit_question_requested.emit(questao_data)

    def _on_create_variant_requested(self, questao_data: Dict):
        """Handler para abrir formulário de criação de variante."""
        # Emitir sinal para que a MainWindow abra o formulário de variante
        self.create_variant_requested.emit(questao_data)


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
