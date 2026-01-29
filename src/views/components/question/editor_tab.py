# src/views/components/question/editor_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QRadioButton, QButtonGroup, QScrollArea, QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QIntValidator
from src.views.design.constants import Color, Spacing, Typography, Dimensions
from src.views.components.common.inputs import TextInput, LatexTextArea

class EditorTab(QWidget):
    """
    Tab for editing question details, including statement, alternatives, and metadata.
    Supports toggling between objective and discursive question types.
    """
    question_type_changed = pyqtSignal(str) # 'objective' or 'discursive'
    content_changed = pyqtSignal() # Emitted when any editable field changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editor_tab")
        self.current_question_type = "objective" # Default

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setObjectName("editor_scroll_area")
        scroll_area_content = QWidget()
        scroll_area_content.setObjectName("editor_scroll_area_content")
        self.scroll_layout = QVBoxLayout(scroll_area_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(Spacing.LG)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Metadata & Mode ---
        metadata_frame = QFrame(self)
        metadata_frame.setObjectName("metadata_frame")
        metadata_frame.setStyleSheet(f"QFrame#metadata_frame {{ border: 1px solid {Color.BORDER_LIGHT}; border-radius: {Dimensions.BORDER_RADIUS_MD}; padding: {Spacing.MD}px; }}")
        metadata_layout = QVBoxLayout(metadata_frame)
        metadata_layout.setSpacing(Spacing.MD)

        # Question Type Toggle
        type_toggle_layout = QHBoxLayout()
        type_toggle_layout.addWidget(QLabel("Tipo de Questão:", metadata_frame))
        self.question_type_group = QButtonGroup(self)
        self.objective_radio = QRadioButton("Objetiva", metadata_frame)
        self.objective_radio.setChecked(True)
        self.question_type_group.addButton(self.objective_radio)
        self.discursive_radio = QRadioButton("Discursiva", metadata_frame)
        self.question_type_group.addButton(self.discursive_radio)
        type_toggle_layout.addWidget(self.objective_radio)
        type_toggle_layout.addWidget(self.discursive_radio)
        type_toggle_layout.addStretch()
        metadata_layout.addLayout(type_toggle_layout)
        self.question_type_group.buttonClicked.connect(self._on_question_type_toggled)

        # Academic Year & Origin/Source
        info_layout = QHBoxLayout()
        self.academic_year_input = TextInput(placeholder_text="Ano Acadêmico", parent=metadata_frame)
        self.academic_year_input.setValidator(self.get_year_validator()) # Requires QIntValidator
        info_layout.addWidget(self.academic_year_input)
        self.origin_input = TextInput(placeholder_text="Origem/Fonte", parent=metadata_frame)
        info_layout.addWidget(self.origin_input)
        metadata_layout.addLayout(info_layout)
        self.scroll_layout.addWidget(metadata_frame)

        # --- Question Statement ---
        self.scroll_layout.addWidget(QLabel("Enunciado da Questão:", self))
        self.statement_input = LatexTextArea(placeholder_text="Digite o enunciado da questão (suporta LaTeX)", parent=self)
        self.scroll_layout.addWidget(self.statement_input)
        self.add_image_statement_button = QPushButton("+ Imagem", self)
        self.add_image_statement_button.setToolTip("Adicionar imagem ao enunciado")
        self.add_image_statement_button.setFixedSize(QSize(100, 30))
        self.add_image_statement_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.LIGHT_BLUE_BG_2};
                color: {Color.PRIMARY_BLUE};
                border: 1px solid {Color.LIGHT_BLUE_BORDER};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: {Spacing.SM}px;
                font-size: {Typography.FONT_SIZE_MD};
            }}
            QPushButton:hover {{
                background-color: {Color.LIGHT_BLUE_BG_1};
            }}
        """)
        self.scroll_layout.addWidget(self.add_image_statement_button, alignment=Qt.AlignmentFlag.AlignRight)


        # --- Alternatives (Objective) ---
        self.alternatives_section = QFrame(self)
        self.alternatives_section.setObjectName("alternatives_section")
        self.alternatives_layout = QVBoxLayout(self.alternatives_section)
        self.alternatives_layout.setSpacing(Spacing.SM)
        self.alternatives_widgets = []
        self.alternatives_button_group = QButtonGroup(self)  # Grupo para exclusão mútua

        self.scroll_layout.addWidget(QLabel("Alternativas (para questões objetivas):", self))
        for i, char in enumerate("ABCDE"):
            alternative_widget = self._create_alternative_input(char)
            self.alternatives_layout.addWidget(alternative_widget)
            self.alternatives_widgets.append(alternative_widget)
            # Adicionar radio button ao grupo para exclusão mútua
            self.alternatives_button_group.addButton(alternative_widget.radio_button, i)
        self.scroll_layout.addWidget(self.alternatives_section)

        # --- Answer Key (Discursive) ---
        self.answer_key_section = QFrame(self)
        self.answer_key_section.setObjectName("answer_key_section")
        self.answer_key_layout = QVBoxLayout(self.answer_key_section)
        self.answer_key_layout.setSpacing(Spacing.SM)
        self.scroll_layout.addWidget(QLabel("Chave de Resposta (para questões discursivas):", self))
        self.answer_key_input = LatexTextArea(placeholder_text="Digite a chave de resposta (suporta LaTeX)", parent=self)
        self.answer_key_layout.addWidget(self.answer_key_input)
        self.add_image_answer_button = QPushButton("+ Imagem", self)
        self.add_image_answer_button.setToolTip("Adicionar imagem à resposta")
        self.add_image_answer_button.setFixedSize(QSize(100, 30))
        self.add_image_answer_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.LIGHT_BLUE_BG_2};
                color: {Color.PRIMARY_BLUE};
                border: 1px solid {Color.LIGHT_BLUE_BORDER};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: {Spacing.SM}px;
                font-size: {Typography.FONT_SIZE_MD};
            }}
            QPushButton:hover {{
                background-color: {Color.LIGHT_BLUE_BG_1};
            }}
        """)
        self.answer_key_layout.addWidget(self.add_image_answer_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.scroll_layout.addWidget(self.answer_key_section)


        self._update_visibility_by_question_type() # Set initial visibility

        scroll_area.setWidget(scroll_area_content)
        main_layout.addWidget(scroll_area)

        self._connect_content_signals()

    def _create_alternative_input(self, char: str):
        container = QWidget(self)
        container.setObjectName(f"alternative_container_{char}")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(Spacing.SM)

        # Estilo inicial do container
        container.setStyleSheet(f"""
            QWidget#alternative_container_{char} {{
                background-color: {Color.WHITE};
                border: 2px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
            }}
        """)

        radio_button = QRadioButton(char, container)
        radio_button.setObjectName(f"alternative_radio_{char}")
        radio_button.setMinimumWidth(30)
        # Estilo do radio button com indicador visível
        radio_button.setStyleSheet(f"""
            QRadioButton {{
                font-size: {Typography.FONT_SIZE_LG};
                font-weight: bold;
                color: {Color.DARK_TEXT};
                padding: 4px;
            }}
            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid {Color.GRAY_TEXT};
                background-color: {Color.WHITE};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid #22c55e;
                background-color: #22c55e;
            }}
            QRadioButton::indicator:hover {{
                border: 2px solid {Color.PRIMARY_BLUE};
            }}
        """)
        # Conectar sinal para atualizar estilo visual quando selecionado
        radio_button.toggled.connect(lambda checked, c=container, ch=char: self._on_alternative_toggled(c, ch, checked))
        layout.addWidget(radio_button)

        text_input = TextInput(placeholder_text=f"Alternativa {char}", parent=container)
        layout.addWidget(text_input)

        add_image_button = QPushButton("IMG", container)
        add_image_button.setToolTip(f"Adicionar imagem à alternativa {char}")
        add_image_button.setMaximumWidth(40)
        add_image_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.LIGHT_BLUE_BG_2};
                color: {Color.PRIMARY_BLUE};
                border: 1px solid {Color.LIGHT_BLUE_BORDER};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                padding: 2px;
                font-size: {Typography.FONT_SIZE_SM};
            }}
            QPushButton:hover {{
                background-color: {Color.LIGHT_BLUE_BG_1};
            }}
        """)
        layout.addWidget(add_image_button)

        container.text_input = text_input # Attach for easier access
        container.radio_button = radio_button # Attach for easier access
        container.add_image_button = add_image_button # Attach for easier access
        return container

    def _on_alternative_toggled(self, container, char: str, checked: bool):
        """Atualiza o estilo visual do container quando a alternativa é selecionada."""
        if checked:
            # Estilo quando selecionada (verde)
            container.setStyleSheet(f"""
                QWidget#alternative_container_{char} {{
                    background-color: #dcfce7;
                    border: 2px solid #22c55e;
                    border-radius: {Dimensions.BORDER_RADIUS_MD};
                }}
            """)
        else:
            # Estilo padrão
            container.setStyleSheet(f"""
                QWidget#alternative_container_{char} {{
                    background-color: {Color.WHITE};
                    border: 2px solid {Color.BORDER_LIGHT};
                    border-radius: {Dimensions.BORDER_RADIUS_MD};
                }}
            """)

    def _on_question_type_toggled(self, radio_button):
        if radio_button.text() == "Objetiva":
            self.current_question_type = "objective"
        else:
            self.current_question_type = "discursive"
        self._update_visibility_by_question_type()
        self.question_type_changed.emit(self.current_question_type)
        self.content_changed.emit() # Type change is also a content change

    def _update_visibility_by_question_type(self):
        is_objective = (self.current_question_type == "objective")
        self.alternatives_section.setVisible(is_objective)
        self.answer_key_section.setVisible(not is_objective)

    def _connect_content_signals(self):
        # Connect signals for content changes to emit content_changed
        self.academic_year_input.textChanged.connect(self.content_changed.emit)
        self.origin_input.textChanged.connect(self.content_changed.emit)
        self.statement_input.textChanged.connect(self.content_changed.emit)
        self.answer_key_input.textChanged.connect(self.content_changed.emit)
        for alt_widget in self.alternatives_widgets:
            alt_widget.text_input.textChanged.connect(self.content_changed.emit)
            alt_widget.radio_button.toggled.connect(self.content_changed.emit)

    def get_year_validator(self):
        # Using QIntValidator
        validator = QIntValidator(1900, 2100, self)
        return validator


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
            self.setWindowTitle("Editor Tab Test")
            self.setGeometry(100, 100, 800, 700)

            self.editor_tab = EditorTab(self)
            self.setCentralWidget(self.editor_tab)

            self.editor_tab.question_type_changed.connect(lambda q_type: print(f"Question type changed to: {q_type}"))
            self.editor_tab.content_changed.connect(lambda: print("Content changed in editor tab."))

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())