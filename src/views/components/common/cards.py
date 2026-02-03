# src/views/components/common/cards.py
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from src.views.design.constants import Color, Spacing, Typography, Dimensions
from src.views.design.enums import DifficultyEnum
from src.views.components.common.badges import Badge, DifficultyBadge

class BaseCard(QFrame):
    """
    A customizable base card with shadow and rounded borders.
    """
    def __init__(self, parent=None, object_name="base_card"):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 20))  # rgba(0, 0, 0, 0.08) ≈ 20/255
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.setStyleSheet(f"""
            QFrame#{object_name} {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

class StatCard(BaseCard):
    """
    Card to display statistics (number + label + variation).
    """
    def __init__(self, label: str, value: str, variation: str = None, parent=None):
        super().__init__(parent, object_name="stat_card")
        self.setObjectName("stat_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("stat_value")
        self._value_label.setStyleSheet(f"""
            QLabel#stat_value {{
                font-size: {Typography.FONT_SIZE_PAGE_TITLE};
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                color: {Color.DARK_TEXT};
            }}
        """)
        layout.addWidget(self._value_label)

        self._label_widget = QLabel(label)
        self._label_widget.setObjectName("stat_label")
        self._label_widget.setStyleSheet(f"""
            QLabel#stat_label {{
                font-size: {Typography.FONT_SIZE_MD};
                color: {Color.GRAY_TEXT};
            }}
        """)
        layout.addWidget(self._label_widget)

        self._variation_label = QLabel(variation if variation else "")
        self._variation_label.setObjectName("stat_variation")
        self._update_variation_style(variation)
        layout.addWidget(self._variation_label)
        if not variation:
            self._variation_label.hide()

        self.setLayout(layout)
        self.setMinimumSize(150, 100)
        self.setMaximumWidth(250)

    def set_value(self, value: str):
        """Update the displayed value."""
        self._value_label.setText(value)

    def set_variation(self, variation: str = None):
        """Update the variation indicator."""
        if variation:
            self._variation_label.setText(variation)
            self._update_variation_style(variation)
            self._variation_label.show()
        else:
            self._variation_label.hide()

    def _update_variation_style(self, variation: str = None):
        """Update variation label style based on positive/negative."""
        if variation and variation.startswith('-'):
            color = Color.TAG_RED
        else:
            color = Color.TAG_GREEN

        self._variation_label.setStyleSheet(f"""
            QLabel#stat_variation {{
                font-size: {Typography.FONT_SIZE_SM};
                color: {color};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
            }}
        """)

class QuestionCard(BaseCard):
    """
    Card to display a question summary (code, title, formula, tags).
    """
    def __init__(self, question_id: str, title: str, formula: str = None, tags: list = None, difficulty: DifficultyEnum = None, variant_count: int = 0, parent=None):
        super().__init__(parent, object_name="question_card")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        main_layout.setSpacing(Spacing.SM)

        # Header: Question ID, Variant Badge and Options
        header_layout = QHBoxLayout()
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

        # Variant count badge
        if variant_count > 0:
            variant_text = f"({variant_count} variante{'s' if variant_count > 1 else ''})"
            variant_label = QLabel(variant_text)
            variant_label.setObjectName("variant_badge")
            variant_label.setStyleSheet(f"""
                QLabel#variant_badge {{
                    color: {Color.GRAY_TEXT};
                    font-size: {Typography.FONT_SIZE_SM};
                    font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                    padding-left: {Spacing.XS}px;
                }}
            """)
            header_layout.addWidget(variant_label)

        header_layout.addStretch()
        # Add placeholders for card_type and card_menu if needed, e.g., icon buttons
        # header_layout.addWidget(QLabel("Type")) # Placeholder
        # header_layout.addWidget(QLabel("Menu")) # Placeholder
        main_layout.addLayout(header_layout)

        # Title
        title_label = QLabel(title)
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

        # Formula Box
        if formula:
            formula_box = QFrame()
            formula_box.setObjectName("formula_box")
            formula_box.setStyleSheet(f"""
                QFrame#formula_box {{
                    background-color: {Color.LIGHT_GRAY_BACKGROUND};
                    border: 1px dashed {Color.BORDER_MEDIUM};
                    border-radius: {Dimensions.BORDER_RADIUS_MD};
                    padding: {Spacing.LG}px;
                }}
            """)
            formula_layout = QVBoxLayout(formula_box)
            formula_text = QLabel(formula)
            formula_text.setObjectName("formula_text")
            formula_text.setWordWrap(True)
            formula_text.setStyleSheet(f"""
                QLabel#formula_text {{
                    font-family: "Times New Roman", serif;
                    font-style: italic;
                    font-size: {Typography.FONT_SIZE_LG};
                    color: {Color.DARK_TEXT};
                }}
            """)
            formula_layout.addWidget(formula_text)
            formula_box.setLayout(formula_layout)
            main_layout.addWidget(formula_box)

        # Tags and Difficulty
        tag_difficulty_layout = QHBoxLayout()
        if tags:
            for tag_text in tags:
                tag_difficulty_layout.addWidget(Badge(tag_text)) # Default gray for tags
        if difficulty:
            tag_difficulty_layout.addWidget(DifficultyBadge(difficulty))
        tag_difficulty_layout.addStretch()
        main_layout.addLayout(tag_difficulty_layout)

        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(180) # Example minimum height, will adjust based on content

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QGridLayout

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from src.views.design.theme import ThemeManager
    ThemeManager.apply_global_theme(app)

    window = QWidget()
    main_layout = QVBoxLayout()

    # Stat Cards
    main_layout.addWidget(QLabel("<h3>Stat Cards:</h3>"))
    stat_card_layout = QHBoxLayout()
    stat_card_layout.addWidget(StatCard("Total Questions", "1,234", "+87"))
    stat_card_layout.addWidget(StatCard("Avg Success Rate", "68.5%", "-2%"))
    stat_card_layout.addWidget(StatCard("Average Time", "4m 32s"))
    stat_card_layout.addStretch()
    main_layout.addLayout(stat_card_layout)

    # Question Cards
    main_layout.addWidget(QLabel("<h3>Question Cards:</h3>"))
    question_grid_layout = QGridLayout()
    question_grid_layout.addWidget(QuestionCard(
        question_id="#Q-1042",
        title="Integral definida de funções trigonométricas",
        formula="$$\\int_{0}^{\\pi/2} \\sin^2(x) dx$$",
        tags=["Cálculo", "Integrais"],
        difficulty=DifficultyEnum.MEDIUM
    ), 0, 0)
    question_grid_layout.addWidget(QuestionCard(
        question_id="#Q-2051",
        title="Problema de otimização com derivadas",
        tags=["Otimização", "Derivadas"],
        difficulty=DifficultyEnum.HARD
    ), 0, 1)
    question_grid_layout.addWidget(QuestionCard(
        question_id="#Q-4592",
        title="Equações lineares e sistemas",
        formula="$A\\mathbf{x} = \\mathbf{b}$",
        tags=["Álgebra", "Sistemas Lineares"],
        difficulty=DifficultyEnum.EASY
    ), 1, 0)
    question_grid_layout.addWidget(QuestionCard(
        question_id="#Q-5000",
        title="Geometria analítica: distância entre pontos",
        tags=["Geometria", "Distância"],
        difficulty=DifficultyEnum.EASY
    ), 1, 1)
    question_grid_layout.setColumnStretch(2, 1) # Make third column stretchable
    main_layout.addLayout(question_grid_layout)
    main_layout.addStretch()


    container = QWidget()
    container.setLayout(main_layout)
    container.setWindowTitle("Card Test")
    container.show()
    sys.exit(app.exec())