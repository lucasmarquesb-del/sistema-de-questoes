# src/views/pages/exam_list_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QCheckBox, QRadioButton,
    QButtonGroup, QScrollArea, QSizePolicy, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QMimeData
from PyQt6.QtGui import QDrag
from typing import Dict, List, Any, Optional

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text, IconPath
from src.views.components.common.inputs import TextInput, LatexTextArea
from src.views.components.common.buttons import PrimaryButton, SecondaryButton
from src.controllers.lista_controller_orm import ListaControllerORM
from src.controllers.questao_controller_orm import QuestaoControllerORM


class QuestionListItem(QListWidgetItem):
    """Custom QListWidgetItem for questions with drag and drop support."""

    def __init__(self, codigo: str, titulo: str, tags: List[str] = None):
        display_text = f"{codigo} • {titulo[:40]}..." if len(titulo) > 40 else f"{codigo} • {titulo}"
        if tags:
            display_text += f" [{', '.join(tags[:2])}]"
        super().__init__(display_text)

        self.codigo = codigo
        self.titulo = titulo
        self.tags = tags or []
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsDragEnabled)


class ExamListPage(QWidget):
    """
    Page for managing exam lists, including creating, editing, and exporting exams.
    Data is loaded from the database via controllers.
    """
    exam_selected = pyqtSignal(str)
    add_question_requested = pyqtSignal()
    generate_pdf_requested = pyqtSignal(dict)
    export_latex_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("exam_list_page")

        # State
        self.current_exam_codigo: Optional[str] = None
        self.current_exam_data: Optional[Dict] = None
        self.exams_list: List[Dict] = []

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the UI layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # 1. Left Panel - Exam List Sidebar
        exam_list_frame = self._create_exam_list_panel()
        main_layout.addWidget(exam_list_frame)

        # 2. Center Panel - Exam Editor
        editor_frame = self._create_editor_panel()
        main_layout.addWidget(editor_frame, 2)

        # 3. Right Panel - Export Config
        export_frame = self._create_export_panel()
        main_layout.addWidget(export_frame)

    def _create_exam_list_panel(self) -> QFrame:
        """Create the exam list sidebar panel."""
        frame = QFrame(self)
        frame.setObjectName("exam_list_sidebar")
        frame.setFixedWidth(Dimensions.EXAM_LIST_WIDTH)
        frame.setStyleSheet(f"""
            QFrame#exam_list_sidebar {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Header
        title_label = QLabel(Text.EXAM_MY_EXAMS, frame)
        title_label.setStyleSheet(f"""
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_MD};
            color: {Color.DARK_TEXT};
        """)
        layout.addWidget(title_label)

        # Create New Button
        create_btn = PrimaryButton(Text.EXAM_CREATE_NEW, parent=frame)
        create_btn.clicked.connect(self._on_create_new_exam)
        layout.addWidget(create_btn)

        # Exam List
        self.exam_list_widget = QListWidget(frame)
        self.exam_list_widget.setObjectName("exam_list_widget")
        self.exam_list_widget.itemClicked.connect(self._on_exam_clicked)
        self.exam_list_widget.setStyleSheet(f"""
            QListWidget#exam_list_widget {{
                border: none;
                background-color: transparent;
                font-size: {Typography.FONT_SIZE_MD};
                color: {Color.DARK_TEXT};
            }}
            QListWidget#exam_list_widget::item {{
                padding: {Spacing.SM}px;
                border-radius: {Dimensions.BORDER_RADIUS_SM};
            }}
            QListWidget#exam_list_widget::item:selected {{
                background-color: {Color.LIGHT_BLUE_BG_2};
                color: {Color.PRIMARY_BLUE};
            }}
            QListWidget#exam_list_widget::item:hover {{
                background-color: {Color.BORDER_LIGHT};
            }}
        """)
        layout.addWidget(self.exam_list_widget)

        return frame

    def _create_editor_panel(self) -> QFrame:
        """Create the exam editor panel."""
        frame = QFrame(self)
        frame.setObjectName("exam_editor_area")
        frame.setStyleSheet(f"""
            QFrame#exam_editor_area {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.LG)

        # Section: Header & Instructions
        section_label = QLabel(Text.EXAM_HEADER_INSTRUCTIONS, frame)
        section_label.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
        """)
        layout.addWidget(section_label)

        # Form fields
        form_grid = QGridLayout()
        form_grid.setSpacing(Spacing.SM)

        form_grid.addWidget(QLabel(f"{Text.LABEL_SCHOOL_NAME}:", frame), 0, 0)
        self.school_name_input = TextInput(parent=frame)
        form_grid.addWidget(self.school_name_input, 0, 1)

        form_grid.addWidget(QLabel(f"{Text.LABEL_PROFESSOR}:", frame), 1, 0)
        self.professor_input = TextInput(parent=frame)
        form_grid.addWidget(self.professor_input, 1, 1)

        form_grid.addWidget(QLabel(f"{Text.LABEL_EXAM_DATE}:", frame), 2, 0)
        self.exam_date_input = TextInput(parent=frame)
        form_grid.addWidget(self.exam_date_input, 2, 1)

        form_grid.addWidget(QLabel(f"{Text.LABEL_DEPARTMENT}:", frame), 3, 0)
        self.department_input = TextInput(parent=frame)
        form_grid.addWidget(self.department_input, 3, 1)

        layout.addLayout(form_grid)

        # Instructions
        instructions_label = QLabel(f"{Text.LABEL_INSTRUCTIONS}:", frame)
        layout.addWidget(instructions_label)

        self.instructions_input = LatexTextArea(parent=frame)
        self.instructions_input.setMinimumHeight(100)
        layout.addWidget(self.instructions_input)

        # Questions Section
        self.questions_header = QLabel(Text.EXAM_QUESTIONS_TOTAL.format(count=0), frame)
        self.questions_header.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
            margin-top: {Spacing.MD}px;
        """)
        layout.addWidget(self.questions_header)

        add_from_bank_btn = PrimaryButton(Text.BUTTON_ADD_FROM_BANK, parent=frame)
        add_from_bank_btn.clicked.connect(self.add_question_requested.emit)
        layout.addWidget(add_from_bank_btn)

        # Questions List
        self.questions_list_widget = QListWidget(frame)
        self.questions_list_widget.setObjectName("exam_questions_list")
        self.questions_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.questions_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.questions_list_widget.setAcceptDrops(True)
        self.questions_list_widget.setDropIndicatorShown(True)
        self.questions_list_widget.setStyleSheet(f"""
            QListWidget#exam_questions_list {{
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                background-color: {Color.LIGHT_BACKGROUND};
            }}
            QListWidget#exam_questions_list::item {{
                padding: {Spacing.SM}px;
                border-bottom: 1px solid {Color.BORDER_LIGHT};
            }}
            QListWidget#exam_questions_list::item:selected {{
                background-color: {Color.LIGHT_BLUE_BG_2};
            }}
        """)
        layout.addWidget(self.questions_list_widget)

        return frame

    def _create_export_panel(self) -> QFrame:
        """Create the export configuration panel."""
        frame = QFrame(self)
        frame.setObjectName("export_config_panel")
        frame.setFixedWidth(Dimensions.EXPORT_CONFIG_WIDTH)
        frame.setStyleSheet(f"""
            QFrame#export_config_panel {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.LG)

        # Header
        title_label = QLabel(Text.EXAM_EXPORT_CONFIG, frame)
        title_label.setStyleSheet(f"""
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_MD};
            color: {Color.DARK_TEXT};
        """)
        layout.addWidget(title_label)

        # Column Layout Options
        columns_label = QLabel("Layout:", frame)
        columns_label.setStyleSheet(f"color: {Color.GRAY_TEXT};")
        layout.addWidget(columns_label)

        self.column_button_group = QButtonGroup(self)
        self.single_column_radio = QRadioButton(Text.EXAM_SINGLE_COLUMN, frame)
        self.two_columns_radio = QRadioButton(Text.EXAM_TWO_COLUMNS, frame)
        self.two_columns_radio.setChecked(True)
        self.column_button_group.addButton(self.single_column_radio)
        self.column_button_group.addButton(self.two_columns_radio)
        layout.addWidget(self.single_column_radio)
        layout.addWidget(self.two_columns_radio)

        # Options
        options_label = QLabel("Options:", frame)
        options_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; margin-top: {Spacing.SM}px;")
        layout.addWidget(options_label)

        self.answer_key_checkbox = QCheckBox(Text.EXAM_INCLUDE_ANSWER_KEY, frame)
        layout.addWidget(self.answer_key_checkbox)

        self.point_values_checkbox = QCheckBox(Text.EXAM_INCLUDE_POINTS, frame)
        layout.addWidget(self.point_values_checkbox)

        self.work_space_checkbox = QCheckBox(Text.EXAM_INCLUDE_WORKSPACE, frame)
        layout.addWidget(self.work_space_checkbox)

        layout.addStretch()

        # Summary
        summary_frame = QFrame(frame)
        summary_frame.setStyleSheet(f"""
            background-color: {Color.LIGHT_BACKGROUND};
            border-radius: {Dimensions.BORDER_RADIUS_MD};
            padding: {Spacing.SM}px;
        """)
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setSpacing(Spacing.XS)

        self.total_questions_label = QLabel("Total: 0 Q", summary_frame)
        summary_layout.addWidget(self.total_questions_label)

        self.total_points_label = QLabel("Points: 0/100", summary_frame)
        summary_layout.addWidget(self.total_points_label)

        self.pages_estimate_label = QLabel("Pages: ~0", summary_frame)
        summary_layout.addWidget(self.pages_estimate_label)

        layout.addWidget(summary_frame)

        # Action Buttons
        generate_pdf_btn = PrimaryButton(Text.BUTTON_GENERATE_PDF, parent=frame)
        generate_pdf_btn.clicked.connect(self._on_generate_pdf)
        layout.addWidget(generate_pdf_btn)

        export_latex_btn = SecondaryButton(Text.BUTTON_EXPORT_LATEX, parent=frame)
        export_latex_btn.clicked.connect(self._on_export_latex)
        layout.addWidget(export_latex_btn)

        return frame

    def _load_data(self):
        """Load data from database."""
        try:
            self.exams_list = ListaControllerORM.listar_listas()
            self._populate_exam_list()
        except Exception as e:
            print(f"Error loading exam list: {e}")
            self.exams_list = []

    def _populate_exam_list(self):
        """Populate the exam list widget."""
        self.exam_list_widget.clear()

        for lista in self.exams_list:
            codigo = lista.get('codigo', '')
            titulo = lista.get('titulo', 'Sem título')
            tipo = lista.get('tipo', 'LISTA')
            total = lista.get('total_questoes', 0)

            item = QListWidgetItem(f"• {titulo}")
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            item.setToolTip(f"{codigo} | {tipo} | {total} questões")
            self.exam_list_widget.addItem(item)

        if not self.exams_list:
            empty_item = QListWidgetItem(Text.EMPTY_NO_EXAMS)
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.exam_list_widget.addItem(empty_item)

    def _on_exam_clicked(self, item: QListWidgetItem):
        """Handle exam selection."""
        codigo = item.data(Qt.ItemDataRole.UserRole)
        if codigo:
            self.current_exam_codigo = codigo
            self._load_exam_details(codigo)
            self.exam_selected.emit(codigo)

    def _load_exam_details(self, codigo: str):
        """Load exam details for editing."""
        try:
            exam_data = ListaControllerORM.buscar_lista(codigo)
            if not exam_data:
                return

            self.current_exam_data = exam_data

            # Update form (these fields aren't stored in current model)
            # Placeholders - would need to extend the Lista model
            self.school_name_input.setText("")
            self.professor_input.setText("")
            self.exam_date_input.setText("")
            self.department_input.setText("")
            self.instructions_input.setText(exam_data.get('formulas', '') or "")

            # Load questions
            self._load_exam_questions(exam_data.get('questoes', []))

            # Update summary
            self._update_summary()

        except Exception as e:
            print(f"Error loading exam details: {e}")

    def _load_exam_questions(self, questoes: List[Dict]):
        """Load questions into the list widget."""
        self.questions_list_widget.clear()

        for idx, q in enumerate(questoes):
            codigo = q.get('codigo', f'Q{idx+1}')
            titulo = q.get('titulo', q.get('enunciado', '')[:50])
            tags = q.get('tags', [])

            item = QuestionListItem(codigo, titulo, tags)
            self.questions_list_widget.addItem(item)

        self.questions_header.setText(
            Text.EXAM_QUESTIONS_TOTAL.format(count=len(questoes))
        )

    def _update_summary(self):
        """Update the export summary."""
        count = self.questions_list_widget.count()
        self.total_questions_label.setText(f"Total: {count} Q")
        self.total_points_label.setText(f"Points: {count * 10}/100")
        pages = max(1, count // 3)
        self.pages_estimate_label.setText(f"Pages: ~{pages}")

    def _on_create_new_exam(self):
        """Handle create new exam button."""
        try:
            result = ListaControllerORM.criar_lista(
                titulo="Nova Lista",
                tipo="PROVA"
            )

            if result:
                QMessageBox.information(
                    self, "Sucesso",
                    f"Lista criada: {result.get('codigo')}"
                )
                self._load_data()
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível criar a lista.")

        except Exception as e:
            print(f"Error creating exam: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao criar: {str(e)}")

    def _on_generate_pdf(self):
        """Handle generate PDF button."""
        config = self._get_export_config()
        self.generate_pdf_requested.emit(config)

    def _on_export_latex(self):
        """Handle export LaTeX button."""
        config = self._get_export_config()
        self.export_latex_requested.emit(config)

    def _get_export_config(self) -> Dict:
        """Get current export configuration."""
        return {
            "codigo_lista": self.current_exam_codigo,
            "columns": "single" if self.single_column_radio.isChecked() else "two",
            "include_answer_key": self.answer_key_checkbox.isChecked(),
            "include_point_values": self.point_values_checkbox.isChecked(),
            "include_work_space": self.work_space_checkbox.isChecked(),
            "school_name": self.school_name_input.text(),
            "professor": self.professor_input.text(),
            "exam_date": self.exam_date_input.text(),
            "department": self.department_input.text(),
            "instructions": self.instructions_input.toPlainText(),
        }

    def add_question_to_exam(self, codigo_questao: str):
        """Add a question to the current exam."""
        if not self.current_exam_codigo:
            QMessageBox.warning(self, "Aviso", "Selecione uma lista primeiro.")
            return

        try:
            result = ListaControllerORM.adicionar_questao(
                self.current_exam_codigo,
                codigo_questao
            )

            if result:
                self._load_exam_details(self.current_exam_codigo)
            else:
                QMessageBox.warning(
                    self, "Erro",
                    "Não foi possível adicionar a questão."
                )

        except Exception as e:
            print(f"Error adding question: {e}")
            QMessageBox.warning(self, "Erro", f"Erro: {str(e)}")

    def refresh_data(self):
        """Public method to refresh data."""
        self._load_data()


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
            self.setWindowTitle("Exam List Page Test")
            self.setGeometry(100, 100, 1200, 800)

            self.exam_list_page = ExamListPage(self)
            self.setCentralWidget(self.exam_list_page)

            self.exam_list_page.exam_selected.connect(
                lambda codigo: print(f"Exam selected: {codigo}")
            )
            self.exam_list_page.add_question_requested.connect(
                lambda: print("Add question requested!")
            )
            self.exam_list_page.generate_pdf_requested.connect(
                lambda config: print(f"Generate PDF: {config}")
            )
            self.exam_list_page.export_latex_requested.connect(
                lambda config: print(f"Export LaTeX: {config}")
            )

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())
