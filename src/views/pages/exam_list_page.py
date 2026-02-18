# src/views/pages/exam_list_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QCheckBox, QRadioButton,
    QButtonGroup, QScrollArea, QSizePolicy, QGridLayout, QMessageBox,
    QComboBox, QFileDialog, QLineEdit, QPushButton, QSpinBox, QApplication,
    QDialog, QDialogButtonBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QMimeData, QThread, QTimer, QElapsedTimer
from PyQt6.QtGui import QDrag
from typing import Dict, List, Any, Optional

from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text
from src.views.components.common.buttons import PrimaryButton, SecondaryButton
from src.controllers.lista_controller_orm import ListaControllerORM
from src.controllers.questao_controller_orm import QuestaoControllerORM
from src.controllers.adapters import criar_export_controller


class ExportWorker(QThread):
    """Thread para executar exportação sem bloquear a UI."""
    finished = pyqtSignal(object)  # Emite o resultado (Path ou lista de Paths)
    error = pyqtSignal(str)  # Emite mensagem de erro

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._func(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ExportProgressDialog(QDialog):
    """Dialog de progresso durante exportação."""

    def __init__(self, mensagem: str = "Gerando arquivo...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportando")
        self.setFixedSize(400, 130)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel(mensagem)
        self.label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.time_label = QLabel("Tempo: 0s")
        self.time_label.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(self.time_label)

        # Timer para atualizar tempo decorrido
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(500)

    def _update_time(self):
        elapsed_s = self._elapsed.elapsed() / 1000
        self.time_label.setText(f"Tempo: {elapsed_s:.0f}s")

    def close_dialog(self):
        self._timer.stop()
        self.accept()


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


class WallonQuestionConfigDialog(QDialog):
    """Dialog para configurar o formato de cada questão antes de exportar (wallon_av2)."""

    def __init__(self, questoes: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuração das Questões")
        self.setMinimumWidth(650)
        self.setMinimumHeight(400)
        self._combos: List[QComboBox] = []
        self._codigos: List[str] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.SM)

        # Header
        header = QLabel("Escolha o formato de resposta para cada questão:")
        header.setStyleSheet(f"font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; font-size: {Typography.FONT_SIZE_MD}; color: {Color.DARK_TEXT};")
        layout.addWidget(header)

        # Scrollable area for questions
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        grid = QGridLayout(scroll_widget)
        grid.setSpacing(Spacing.SM)

        grid.addWidget(QLabel("#"), 0, 0)
        grid.addWidget(QLabel("Questão"), 0, 1)
        grid.addWidget(QLabel("Formato"), 0, 2)

        for i, q in enumerate(questoes):
            codigo = q.get('codigo', f'Q{i+1}')
            titulo = q.get('titulo') or (q.get('enunciado', '')[:50])
            self._codigos.append(codigo)

            num_label = QLabel(f"{i+1}")
            num_label.setFixedWidth(30)
            grid.addWidget(num_label, i + 1, 0)

            desc = f"{codigo} - {titulo}"
            if len(desc) > 55:
                desc = desc[:55] + "..."
            q_label = QLabel(desc)
            q_label.setToolTip(q.get('enunciado', '')[:200])
            grid.addWidget(q_label, i + 1, 1)

            combo = QComboBox()
            combo.addItem("Normal", "normal")
            combo.addItem("5 Linhas", "5linhas")
            combo.addItem("Espaço com Borda", "espaco_borda")
            combo.setMinimumWidth(160)
            grid.addWidget(combo, i + 1, 2)
            self._combos.append(combo)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # Shortcut buttons
        shortcut_layout = QHBoxLayout()
        shortcut_layout.setSpacing(Spacing.SM)

        btn_all_normal = QPushButton("Todos Normal")
        btn_all_normal.clicked.connect(lambda: self._set_all("normal"))
        shortcut_layout.addWidget(btn_all_normal)

        btn_all_lines = QPushButton("Todos 5 Linhas")
        btn_all_lines.clicked.connect(lambda: self._set_all("5linhas"))
        shortcut_layout.addWidget(btn_all_lines)

        btn_all_box = QPushButton("Todos Espaço")
        btn_all_box.clicked.connect(lambda: self._set_all("espaco_borda"))
        shortcut_layout.addWidget(btn_all_box)

        shortcut_layout.addStretch()
        layout.addLayout(shortcut_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _set_all(self, value: str):
        for combo in self._combos:
            idx = combo.findData(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def get_config(self) -> Dict[str, str]:
        """Retorna dict {codigo_questao: formato}."""
        config = {}
        for codigo, combo in zip(self._codigos, self._combos):
            config[codigo] = combo.currentData()
        return config


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
        self._original_title: str = ""
        self._showing_inactive: bool = False

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
        main_layout.addWidget(editor_frame, 1)

        # 3. Right Panel - Export Config
        export_frame = self._create_export_panel()
        main_layout.addWidget(export_frame, 1)

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

        # Inactivate Button
        self.inactivate_btn = SecondaryButton("Inativar Lista", parent=frame)
        self.inactivate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.WHITE};
                color: #e74c3c;
                border: 1px solid #e74c3c;
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {Typography.FONT_SIZE_MD};
            }}
            QPushButton:hover {{
                background-color: #fdf2f2;
            }}
        """)
        self.inactivate_btn.clicked.connect(self._on_inactivate_exam)
        layout.addWidget(self.inactivate_btn)

        # Reactivate Button (hidden by default, shown in inactive view)
        self.reactivate_btn = SecondaryButton("Reativar Lista", parent=frame)
        self.reactivate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.WHITE};
                color: {Color.TAG_GREEN};
                border: 1px solid {Color.TAG_GREEN};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {Typography.FONT_SIZE_MD};
            }}
            QPushButton:hover {{
                background-color: #f0fdf4;
            }}
        """)
        self.reactivate_btn.clicked.connect(self._on_reactivate_exam)
        self.reactivate_btn.setVisible(False)
        layout.addWidget(self.reactivate_btn)

        # Toggle inactive lists button
        self.toggle_inactive_btn = QPushButton("Ver Inativadas", frame)
        self.toggle_inactive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_inactive_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Color.GRAY_TEXT};
                border: 1px solid {Color.BORDER_MEDIUM};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                padding: {Spacing.XS}px {Spacing.SM}px;
                font-size: {Typography.FONT_SIZE_SM};
            }}
            QPushButton:hover {{
                color: {Color.PRIMARY_BLUE};
                border-color: {Color.PRIMARY_BLUE};
            }}
        """)
        self.toggle_inactive_btn.clicked.connect(self._on_toggle_inactive)
        layout.addWidget(self.toggle_inactive_btn)

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

        # Título da lista selecionada (editável)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(Spacing.SM)

        self.selected_list_title = QLineEdit(frame)
        self.selected_list_title.setPlaceholderText("Selecione uma lista")
        self.selected_list_title.setReadOnly(True)
        self.selected_list_title.setMinimumHeight(36)
        self.selected_list_title.setStyleSheet(f"""
            QLineEdit {{
                font-size: {Typography.FONT_SIZE_LG};
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                color: {Color.DARK_TEXT};
                border: none;
                background-color: transparent;
                padding: 6px 0px;
            }}
            QLineEdit:focus {{
                border: 1px solid {Color.PRIMARY_BLUE};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                background-color: {Color.WHITE};
                padding: 6px 8px;
            }}
        """)
        self.selected_list_title.returnPressed.connect(self._on_save_title)
        title_layout.addWidget(self.selected_list_title)

        self.edit_title_btn = QPushButton("Editar", frame)
        self.edit_title_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_title_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.LIGHT_BLUE_BG_1};
                color: {Color.PRIMARY_BLUE};
                border: 1px solid {Color.PRIMARY_BLUE};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                font-size: {Typography.FONT_SIZE_SM};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Color.PRIMARY_BLUE};
                color: {Color.WHITE};
            }}
        """)
        self.edit_title_btn.clicked.connect(self._on_edit_title_clicked)
        self.edit_title_btn.setVisible(False)
        title_layout.addWidget(self.edit_title_btn)

        self.save_title_btn = QPushButton("Salvar", frame)
        self.save_title_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_title_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.TAG_GREEN};
                color: {Color.WHITE};
                border: none;
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                font-size: {Typography.FONT_SIZE_SM};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        self.save_title_btn.clicked.connect(self._on_save_title)
        self.save_title_btn.setVisible(False)
        title_layout.addWidget(self.save_title_btn)

        self.cancel_edit_btn = QPushButton("Cancelar", frame)
        self.cancel_edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Color.WHITE};
                color: {Color.GRAY_TEXT};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                font-size: {Typography.FONT_SIZE_SM};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Color.LIGHT_BACKGROUND};
            }}
        """)
        self.cancel_edit_btn.clicked.connect(self._on_cancel_edit_title)
        self.cancel_edit_btn.setVisible(False)
        title_layout.addWidget(self.cancel_edit_btn)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Questions Section
        self.questions_header = QLabel(Text.EXAM_QUESTIONS_TOTAL.format(count=0), frame)
        self.questions_header.setStyleSheet(f"""
            font-size: {Typography.FONT_SIZE_MD};
            font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            color: {Color.DARK_TEXT};
            margin-top: {Spacing.MD}px;
        """)
        layout.addWidget(self.questions_header)

        # Botões de ação
        btn_layout = QHBoxLayout()

        add_from_bank_btn = PrimaryButton(Text.BUTTON_ADD_FROM_BANK, parent=frame)
        add_from_bank_btn.clicked.connect(self._on_add_question_clicked)
        btn_layout.addWidget(add_from_bank_btn)

        remove_question_btn = SecondaryButton("Remover Selecionada", parent=frame)
        remove_question_btn.clicked.connect(self._on_remove_question_clicked)
        btn_layout.addWidget(remove_question_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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
        frame.setMinimumWidth(Dimensions.EXPORT_CONFIG_WIDTH)
        frame.setStyleSheet(f"""
            QFrame#export_config_panel {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_LG};
            }}
        """)

        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        main_layout.setSpacing(Spacing.SM)

        # Header
        title_label = QLabel(Text.EXAM_EXPORT_CONFIG, frame)
        title_label.setStyleSheet(f"""
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_MD};
            color: {Color.DARK_TEXT};
        """)
        main_layout.addWidget(title_label)

        # Scroll Area para o conteúdo
        scroll_area = QScrollArea(frame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)

        # Template Selection
        template_label = QLabel("Template:", scroll_content)
        template_label.setStyleSheet(f"color: {Color.GRAY_TEXT};")
        layout.addWidget(template_label)

        self.template_combo = QComboBox(scroll_content)
        self.template_combo.setStyleSheet(f"""
            QComboBox {{
                padding: {Spacing.SM}px;
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                background-color: {Color.WHITE};
            }}
            QComboBox:hover {{
                border-color: {Color.PRIMARY_BLUE};
            }}
        """)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        layout.addWidget(self.template_combo)

        # Campos específicos do template Wallon
        self.wallon_fields_frame = QFrame(scroll_content)
        self.wallon_fields_frame.setObjectName("wallon_fields")
        self.wallon_fields_frame.setStyleSheet(f"""
            QFrame#wallon_fields {{
                background-color: {Color.LIGHT_BLUE_BG_1};
                border: 1px solid {Color.LIGHT_BLUE_BORDER};
                border-radius: {Dimensions.BORDER_RADIUS_MD};
            }}
        """)
        wallon_layout = QVBoxLayout(self.wallon_fields_frame)
        wallon_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        wallon_layout.setSpacing(Spacing.XS)

        wallon_title = QLabel("Informações da Avaliação:", self.wallon_fields_frame)
        wallon_title.setStyleSheet(f"""
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_SM};
            color: {Color.PRIMARY_BLUE};
        """)
        wallon_layout.addWidget(wallon_title)

        # Campo Disciplina
        self.disciplina_input = QLineEdit(self.wallon_fields_frame)
        self.disciplina_input.setPlaceholderText("Disciplina (ex: Matemática)")
        self.disciplina_input.setStyleSheet(self._get_input_style())
        self.disciplina_input.setFixedHeight(28)
        wallon_layout.addWidget(self.disciplina_input)

        # Campo Professor
        self.professor_input = QLineEdit(self.wallon_fields_frame)
        self.professor_input.setPlaceholderText("Professor(a)")
        self.professor_input.setStyleSheet(self._get_input_style())
        self.professor_input.setFixedHeight(28)
        wallon_layout.addWidget(self.professor_input)

        # Campo Trimestre (para wallon_av2)
        self.trimestre_label = QLabel("Trimestre:", self.wallon_fields_frame)
        self.trimestre_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: 11px;")
        wallon_layout.addWidget(self.trimestre_label)

        self.trimestre_combo = QComboBox(self.wallon_fields_frame)
        self.trimestre_combo.addItem("Selecione o Trimestre", "")
        self.trimestre_combo.addItem("1º", "1º")
        self.trimestre_combo.addItem("2º", "2º")
        self.trimestre_combo.addItem("3º", "3º")
        self.trimestre_combo.setStyleSheet(self._get_combo_style())
        self.trimestre_combo.setFixedHeight(28)
        wallon_layout.addWidget(self.trimestre_combo)

        # Campo Unidade (para listaWallon)
        self.wallon_unidade_label = QLabel("Unidade:", self.wallon_fields_frame)
        self.wallon_unidade_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: 11px;")
        wallon_layout.addWidget(self.wallon_unidade_label)

        self.wallon_unidade_combo = QComboBox(self.wallon_fields_frame)
        self.wallon_unidade_combo.addItem("Selecione a Unidade", "")
        self.wallon_unidade_combo.addItem("I", "I")
        self.wallon_unidade_combo.addItem("II", "II")
        self.wallon_unidade_combo.addItem("III", "III")
        self.wallon_unidade_combo.setStyleSheet(self._get_combo_style())
        self.wallon_unidade_combo.setFixedHeight(28)
        wallon_layout.addWidget(self.wallon_unidade_combo)

        # Campo Ano
        self.ano_input = QLineEdit(self.wallon_fields_frame)
        self.ano_input.setPlaceholderText("Ano (ex: 2026)")
        self.ano_input.setStyleSheet(self._get_input_style())
        self.ano_input.setFixedHeight(28)
        wallon_layout.addWidget(self.ano_input)

        self.wallon_fields_frame.setVisible(False)
        layout.addWidget(self.wallon_fields_frame)

        # Campos específicos do template CEAB (simuladoCeab)
        self.ceab_fields_frame = QFrame(scroll_content)
        self.ceab_fields_frame.setObjectName("ceab_fields")
        self.ceab_fields_frame.setStyleSheet(f"""
            QFrame#ceab_fields {{
                background-color: #f0f8f0;
                border: 1px solid #90EE90;
                border-radius: {Dimensions.BORDER_RADIUS_MD};
            }}
        """)
        ceab_layout = QVBoxLayout(self.ceab_fields_frame)
        ceab_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        ceab_layout.setSpacing(Spacing.XS)

        ceab_title = QLabel("Informacoes do Simulado CEAB:", self.ceab_fields_frame)
        ceab_title.setStyleSheet(f"""
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_SM};
            color: #228B22;
        """)
        ceab_layout.addWidget(ceab_title)

        # Campo Data de Aplicacao
        self.data_aplicacao_input = QLineEdit(self.ceab_fields_frame)
        self.data_aplicacao_input.setPlaceholderText("Data da Aplicacao (ex: 02/12/2025)")
        self.data_aplicacao_input.setStyleSheet(self._get_input_style())
        self.data_aplicacao_input.setFixedHeight(28)
        ceab_layout.addWidget(self.data_aplicacao_input)

        # Campo Serie do Simulado
        self.serie_simulado_input = QLineEdit(self.ceab_fields_frame)
        self.serie_simulado_input.setPlaceholderText("Serie (ex: 3o ANO VESPERTINO)")
        self.serie_simulado_input.setStyleSheet(self._get_input_style())
        self.serie_simulado_input.setFixedHeight(28)
        ceab_layout.addWidget(self.serie_simulado_input)

        # Campo Unidade (dropdown)
        unidade_label = QLabel("Unidade:", self.ceab_fields_frame)
        unidade_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: 11px;")
        ceab_layout.addWidget(unidade_label)

        self.unidade_combo = QComboBox(self.ceab_fields_frame)
        self.unidade_combo.addItem("Selecione a Unidade", "")
        self.unidade_combo.addItem("I", "I")
        self.unidade_combo.addItem("II", "II")
        self.unidade_combo.addItem("III", "III")
        self.unidade_combo.setStyleSheet(self._get_combo_style())
        self.unidade_combo.setFixedHeight(28)
        ceab_layout.addWidget(self.unidade_combo)

        # Campo Tipo de Simulado (dropdown)
        tipo_label = QLabel("Tipo de Simulado:", self.ceab_fields_frame)
        tipo_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: 11px;")
        ceab_layout.addWidget(tipo_label)

        self.tipo_simulado_combo = QComboBox(self.ceab_fields_frame)
        self.tipo_simulado_combo.addItem("Selecione o Tipo", "")
        self.tipo_simulado_combo.addItem("LINGUAGENS, CODIGOS E SUAS TECNOLOGIAS", "LINGUAGENS, CODIGOS E SUAS TECNOLOGIAS")
        self.tipo_simulado_combo.addItem("LINGUAGENS, CODIGOS, CIENCIAS HUMANAS E SUAS TECNOLOGIAS", "LINGUAGENS, CODIGOS, CIENCIAS HUMANAS E SUAS TECNOLOGIAS")
        self.tipo_simulado_combo.addItem("CIENCIAS HUMANAS E SUAS TECNOLOGIAS", "CIENCIAS HUMANAS E SUAS TECNOLOGIAS")
        self.tipo_simulado_combo.addItem("MATEMATICA, CIENCIAS DA NATUREZA E SUAS TECNOLOGIAS", "MATEMATICA, CIENCIAS DA NATUREZA E SUAS TECNOLOGIAS")
        self.tipo_simulado_combo.addItem("AREA TECNICA", "AREA TECNICA")
        self.tipo_simulado_combo.setStyleSheet(self._get_combo_style())
        self.tipo_simulado_combo.setFixedHeight(28)
        ceab_layout.addWidget(self.tipo_simulado_combo)

        self.ceab_fields_frame.setVisible(False)
        layout.addWidget(self.ceab_fields_frame)

        radio_style = """
            QRadioButton::indicator {
                border: 1px solid black;
                border-radius: 7px;
                width: 14px;
                height: 14px;
            }
            QRadioButton::indicator:checked {
                background-color: #2980b9;
                border: 1px solid black;
            }
        """
        checkbox_style = """
            QCheckBox::indicator {
                border: 1px solid black;
                border-radius: 3px;
                width: 14px;
                height: 14px;
            }
            QCheckBox::indicator:checked {
                background-color: #2980b9;
                border: 1px solid black;
            }
        """

        # Column Layout Options
        self.columns_label = QLabel("Layout:", scroll_content)
        self.columns_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; margin-top: {Spacing.SM}px;")
        layout.addWidget(self.columns_label)

        self.column_button_group = QButtonGroup(self)
        self.single_column_radio = QRadioButton(Text.EXAM_SINGLE_COLUMN, scroll_content)
        self.single_column_radio.setStyleSheet(radio_style)
        self.two_columns_radio = QRadioButton(Text.EXAM_TWO_COLUMNS, scroll_content)
        self.two_columns_radio.setStyleSheet(radio_style)
        self.two_columns_radio.setChecked(True)
        self.column_button_group.addButton(self.single_column_radio)
        self.column_button_group.addButton(self.two_columns_radio)
        layout.addWidget(self.single_column_radio)
        layout.addWidget(self.two_columns_radio)

        # Options
        options_label = QLabel("Opções:", scroll_content)
        options_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; margin-top: {Spacing.SM}px;")
        layout.addWidget(options_label)

        self.answer_key_checkbox = QCheckBox(Text.EXAM_INCLUDE_ANSWER_KEY, scroll_content)
        self.answer_key_checkbox.setStyleSheet(checkbox_style)
        layout.addWidget(self.answer_key_checkbox)

        self.point_values_checkbox = QCheckBox(Text.EXAM_INCLUDE_POINTS, scroll_content)
        self.point_values_checkbox.setStyleSheet(checkbox_style)
        layout.addWidget(self.point_values_checkbox)

        self.work_space_checkbox = QCheckBox(Text.EXAM_INCLUDE_WORKSPACE, scroll_content)
        self.work_space_checkbox.setStyleSheet(checkbox_style)
        layout.addWidget(self.work_space_checkbox)

        # Opção de Versões Randomizadas
        randomize_label = QLabel("Versões Randomizadas:", scroll_content)
        randomize_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; margin-top: {Spacing.SM}px;")
        layout.addWidget(randomize_label)

        self.randomize_checkbox = QCheckBox("Gerar versões randomizadas", scroll_content)
        self.randomize_checkbox.setStyleSheet(checkbox_style)
        self.randomize_checkbox.stateChanged.connect(self._on_randomize_changed)
        layout.addWidget(self.randomize_checkbox)

        # Container para opções de randomização (inicialmente oculto)
        self.randomize_options_frame = QFrame(scroll_content)
        self.randomize_options_frame.setStyleSheet("QFrame { border: none; margin-left: 20px; }")
        randomize_options_layout = QVBoxLayout(self.randomize_options_frame)
        randomize_options_layout.setContentsMargins(0, 0, 0, 0)
        randomize_options_layout.setSpacing(Spacing.XS)

        # Quantidade de versões
        qty_layout = QHBoxLayout()
        qty_label = QLabel("Quantidade:", self.randomize_options_frame)
        qty_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: {Typography.FONT_SIZE_SM};")
        qty_layout.addWidget(qty_label)

        self.versoes_spinbox = QSpinBox(self.randomize_options_frame)
        self.versoes_spinbox.setRange(1, 4)
        self.versoes_spinbox.setValue(2)
        self.versoes_spinbox.setFixedWidth(60)
        self.versoes_spinbox.valueChanged.connect(self._update_tipos_preview)
        self.versoes_spinbox.setStyleSheet(f"""
            QSpinBox {{
                padding: 4px;
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
            }}
        """)
        qty_layout.addWidget(self.versoes_spinbox)
        qty_layout.addStretch()
        randomize_options_layout.addLayout(qty_layout)

        # Preview dos tipos
        self.tipos_preview_label = QLabel("Tipos: A, B", self.randomize_options_frame)
        self.tipos_preview_label.setStyleSheet(f"""
            color: {Color.PRIMARY_BLUE};
            font-weight: {Typography.FONT_WEIGHT_BOLD};
            font-size: {Typography.FONT_SIZE_SM};
        """)
        randomize_options_layout.addWidget(self.tipos_preview_label)

        # Info sobre randomização
        info_label = QLabel("Usa variantes das questões ou\nrandomiza alternativas.", self.randomize_options_frame)
        info_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: 10px;")
        info_label.setWordWrap(True)
        randomize_options_layout.addWidget(info_label)

        self.randomize_options_frame.setVisible(False)
        layout.addWidget(self.randomize_options_frame)

        layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # Summary (fora do scroll)
        summary_frame = QFrame(frame)
        summary_frame.setStyleSheet(f"""
            background-color: {Color.LIGHT_BACKGROUND};
            border-radius: {Dimensions.BORDER_RADIUS_MD};
            padding: {Spacing.SM}px;
        """)
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setSpacing(Spacing.XS)

        self.total_questions_label = QLabel("Total: 0 questões", summary_frame)
        summary_layout.addWidget(self.total_questions_label)

        self.total_points_label = QLabel("Pontos: 0/100", summary_frame)
        summary_layout.addWidget(self.total_points_label)

        self.pages_estimate_label = QLabel("Páginas: ~0", summary_frame)
        summary_layout.addWidget(self.pages_estimate_label)

        main_layout.addWidget(summary_frame)

        # Action Buttons (fora do scroll)
        generate_pdf_btn = PrimaryButton(Text.BUTTON_GENERATE_PDF, parent=frame)
        generate_pdf_btn.clicked.connect(self._on_generate_pdf)
        main_layout.addWidget(generate_pdf_btn)

        export_latex_btn = SecondaryButton(Text.BUTTON_EXPORT_LATEX, parent=frame)
        export_latex_btn.clicked.connect(self._on_export_latex)
        main_layout.addWidget(export_latex_btn)

        # Carregar templates após criar todos os elementos da UI
        self._load_templates()

        return frame

    def _load_templates(self):
        """Load available LaTeX templates."""
        try:
            export_controller = criar_export_controller()
            templates = export_controller.listar_templates_disponiveis()
            self.template_combo.clear()
            for template in templates:
                # Remove .tex extension for display
                display_name = template.replace('.tex', '').replace('_', ' ').title()
                self.template_combo.addItem(display_name, template)

            if not templates:
                self.template_combo.addItem("Nenhum template encontrado", None)

            # Verificar template inicial
            self._on_template_changed(0)
        except Exception as e:
            print(f"Erro ao carregar templates: {e}")
            self.template_combo.addItem("Erro ao carregar", None)

    def _get_input_style(self) -> str:
        """Return common input style for template fields."""
        return f"""
            QLineEdit {{
                padding: 6px 8px;
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                background-color: {Color.WHITE};
                font-size: {Typography.FONT_SIZE_SM};
                min-height: 28px;
                max-height: 28px;
            }}
            QLineEdit:focus {{
                border-color: {Color.PRIMARY_BLUE};
            }}
        """

    def _get_combo_style(self) -> str:
        """Return common combo box style for template fields."""
        return f"""
            QComboBox {{
                padding: 6px 8px;
                border: 1px solid {Color.BORDER_LIGHT};
                border-radius: {Dimensions.BORDER_RADIUS_SM};
                background-color: {Color.WHITE};
                font-size: {Typography.FONT_SIZE_SM};
                min-height: 28px;
                max-height: 28px;
                color: {Color.DARK_TEXT};
            }}
            QComboBox:hover {{
                border-color: {Color.PRIMARY_BLUE};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {Color.GRAY_TEXT};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                selection-background-color: {Color.LIGHT_BLUE_BG_1};
                selection-color: {Color.DARK_TEXT};
                color: {Color.DARK_TEXT};
            }}
        """

    def _on_template_changed(self, index: int):
        """Handle template selection change."""
        template = self.template_combo.currentData()

        # Ocultar todos os campos específicos primeiro
        self.wallon_fields_frame.setVisible(False)
        self.ceab_fields_frame.setVisible(False)

        # Mostrar opções de colunas por padrão
        self.columns_label.setVisible(True)
        self.single_column_radio.setVisible(True)
        self.two_columns_radio.setVisible(True)

        if template:
            if 'wallon' in template.lower():
                self.wallon_fields_frame.setVisible(True)
                # Diferenciar entre listaWallon (usa Unidade) e wallon_av2 (usa Trimestre)
                is_lista_wallon = 'listawallon' in template.lower()
                is_wallon_av2 = 'wallon_av2' in template.lower()
                # Mostrar/ocultar campos específicos
                self.trimestre_label.setVisible(is_wallon_av2)
                self.trimestre_combo.setVisible(is_wallon_av2)
                self.wallon_unidade_label.setVisible(is_lista_wallon)
                self.wallon_unidade_combo.setVisible(is_lista_wallon)
            elif 'ceab' in template.lower() or 'simulado' in template.lower():
                self.ceab_fields_frame.setVisible(True)
                # Template CEAB já tem duas colunas, ocultar opção e definir para 1 coluna
                # (o template internamente já aplica 2 colunas)
                self.columns_label.setVisible(False)
                self.single_column_radio.setVisible(False)
                self.two_columns_radio.setVisible(False)
                self.single_column_radio.setChecked(True)  # Evita duplicar multicols

    def _on_randomize_changed(self, state):
        """Handle randomize checkbox state change."""
        is_checked = state == Qt.CheckState.Checked.value
        self.randomize_options_frame.setVisible(is_checked)

    def _update_tipos_preview(self, quantidade: int):
        """Update the preview of version types."""
        tipos = ['A', 'B', 'C', 'D'][:quantidade]
        self.tipos_preview_label.setText(f"Tipos: {', '.join(tipos)}")

    def _load_data(self):
        """Load data from database."""
        try:
            if self._showing_inactive:
                all_lists = ListaControllerORM.listar_listas(apenas_ativos=False)
                active_codes = {l['codigo'] for l in ListaControllerORM.listar_listas(apenas_ativos=True)}
                self.exams_list = [l for l in all_lists if l['codigo'] not in active_codes]
            else:
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
            empty_text = "Nenhuma lista inativada" if self._showing_inactive else Text.EMPTY_NO_EXAMS
            empty_item = QListWidgetItem(empty_text)
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

            # Atualizar título da lista selecionada
            titulo = exam_data.get('titulo', 'Sem título')
            self.selected_list_title.setText(titulo)
            self.selected_list_title.setReadOnly(True)
            self._original_title = titulo

            # Mostrar botão de edição
            self.edit_title_btn.setVisible(True)
            self.save_title_btn.setVisible(False)
            self.cancel_edit_btn.setVisible(False)

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
        self.total_questions_label.setText(f"Total: {count} questões")
        self.total_points_label.setText(f"Pontos: {count * 10}/100")
        pages = max(1, count // 3)
        self.pages_estimate_label.setText(f"Páginas: ~{pages}")

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

    def _on_inactivate_exam(self):
        """Handle inactivate exam button."""
        current_item = self.exam_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione uma lista para inativar.")
            return

        codigo = current_item.data(Qt.ItemDataRole.UserRole)
        if not codigo:
            QMessageBox.warning(self, "Aviso", "Lista inválida selecionada.")
            return

        titulo = current_item.text().replace("• ", "")

        reply = QMessageBox.question(
            self,
            "Confirmar Inativação",
            f"Tem certeza que deseja inativar a lista '{titulo}'?\n\n"
            "A lista ficará oculta mas poderá ser reativada posteriormente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = ListaControllerORM.deletar_lista(codigo)
                if result:
                    QMessageBox.information(self, "Sucesso", "Lista inativada com sucesso.")
                    # Limpar seleção atual
                    self.current_exam_codigo = None
                    self.current_exam_data = None
                    self.selected_list_title.setText("")
                    self.selected_list_title.setPlaceholderText("Selecione uma lista")
                    self.questions_list_widget.clear()
                    self.edit_title_btn.setVisible(False)
                    # Recarregar dados
                    self._load_data()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível inativar a lista.")
            except Exception as e:
                print(f"Error inactivating exam: {e}")
                QMessageBox.warning(self, "Erro", f"Erro ao inativar: {str(e)}")

    def _on_toggle_inactive(self):
        """Toggle between active and inactive lists."""
        self._showing_inactive = not self._showing_inactive

        if self._showing_inactive:
            self.toggle_inactive_btn.setText("Ver Ativas")
            self.reactivate_btn.setVisible(True)
            self.inactivate_btn.setVisible(False)
        else:
            self.toggle_inactive_btn.setText("Ver Inativadas")
            self.reactivate_btn.setVisible(False)
            self.inactivate_btn.setVisible(True)

        # Clear current selection
        self.current_exam_codigo = None
        self.current_exam_data = None
        self.selected_list_title.setText("")
        self.selected_list_title.setPlaceholderText("Selecione uma lista")
        self.questions_list_widget.clear()
        self.edit_title_btn.setVisible(False)

        self._load_data()

    def _on_reactivate_exam(self):
        """Handle reactivate exam button."""
        current_item = self.exam_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione uma lista para reativar.")
            return

        codigo = current_item.data(Qt.ItemDataRole.UserRole)
        if not codigo:
            QMessageBox.warning(self, "Aviso", "Lista inválida selecionada.")
            return

        titulo = current_item.text().replace("• ", "")

        reply = QMessageBox.question(
            self,
            "Confirmar Reativação",
            f"Deseja reativar a lista '{titulo}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = ListaControllerORM.reativar_lista(codigo)
                if result:
                    QMessageBox.information(self, "Sucesso", "Lista reativada com sucesso.")
                    self.current_exam_codigo = None
                    self.current_exam_data = None
                    self.selected_list_title.setText("")
                    self.questions_list_widget.clear()
                    self.edit_title_btn.setVisible(False)
                    self._load_data()
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível reativar a lista.")
            except Exception as e:
                print(f"Error reactivating exam: {e}")
                QMessageBox.warning(self, "Erro", f"Erro ao reativar: {str(e)}")

    def _on_edit_title_clicked(self):
        """Enable title editing."""
        self.selected_list_title.setReadOnly(False)
        self.selected_list_title.setFocus()
        self.selected_list_title.selectAll()

        # Alternar botões
        self.edit_title_btn.setVisible(False)
        self.save_title_btn.setVisible(True)
        self.cancel_edit_btn.setVisible(True)

    def _on_save_title(self):
        """Save the edited title."""
        if not self.current_exam_codigo:
            return

        new_title = self.selected_list_title.text().strip()
        if not new_title:
            QMessageBox.warning(self, "Aviso", "O título não pode estar vazio.")
            return

        try:
            result = ListaControllerORM.atualizar_lista(
                codigo=self.current_exam_codigo,
                titulo=new_title
            )

            if result:
                self._original_title = new_title
                self.selected_list_title.setReadOnly(True)

                # Alternar botões
                self.edit_title_btn.setVisible(True)
                self.save_title_btn.setVisible(False)
                self.cancel_edit_btn.setVisible(False)

                # Atualizar lista lateral
                self._load_data()

                # Reselecionar o item atual
                for i in range(self.exam_list_widget.count()):
                    item = self.exam_list_widget.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == self.current_exam_codigo:
                        self.exam_list_widget.setCurrentItem(item)
                        break
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível atualizar o título.")

        except Exception as e:
            print(f"Error updating title: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao atualizar: {str(e)}")

    def _on_cancel_edit_title(self):
        """Cancel title editing."""
        self.selected_list_title.setText(self._original_title)
        self.selected_list_title.setReadOnly(True)

        # Alternar botões
        self.edit_title_btn.setVisible(True)
        self.save_title_btn.setVisible(False)
        self.cancel_edit_btn.setVisible(False)

    def _on_add_question_clicked(self):
        """Handle add question button - opens question selector dialog."""
        if not self.current_exam_codigo:
            QMessageBox.warning(self, "Aviso", "Selecione uma lista primeiro.")
            return

        from src.views.pages.questao_selector_page import QuestaoSelectorDialog

        # Obter questões já na lista
        questoes_na_lista = self.current_exam_data.get('questoes', []) if self.current_exam_data else []

        dialog = QuestaoSelectorDialog(
            questoes_ja_na_lista=questoes_na_lista,
            parent=self
        )
        dialog.questoesAdicionadas.connect(self._on_questions_added)
        dialog.exec()

    def _on_questions_added(self, questoes_list):
        """Callback when questions are added from selector dialog."""
        if not self.current_exam_codigo:
            return

        try:
            added_count = 0
            for questao in questoes_list:
                codigo_questao = questao.get('codigo') if isinstance(questao, dict) else getattr(questao, 'codigo', None)
                if codigo_questao:
                    result = ListaControllerORM.adicionar_questao(
                        self.current_exam_codigo,
                        codigo_questao
                    )
                    if result:
                        added_count += 1

            if added_count > 0:
                QMessageBox.information(
                    self, "Sucesso",
                    f"{added_count} questão(ões) adicionada(s) à lista."
                )
                # Recarregar detalhes da lista
                self._load_exam_details(self.current_exam_codigo)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao adicionar questões: {str(e)}")

    def _on_remove_question_clicked(self):
        """Handle remove question button."""
        if not self.current_exam_codigo:
            QMessageBox.warning(self, "Aviso", "Selecione uma lista primeiro.")
            return

        current_item = self.questions_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione uma questão para remover.")
            return

        if not isinstance(current_item, QuestionListItem):
            return

        codigo_questao = current_item.codigo

        reply = QMessageBox.question(
            self, "Confirmar",
            f"Remover a questão {codigo_questao} da lista?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = ListaControllerORM.remover_questao(
                    self.current_exam_codigo,
                    codigo_questao
                )
                if result:
                    self._load_exam_details(self.current_exam_codigo)
                else:
                    QMessageBox.warning(self, "Erro", "Não foi possível remover a questão.")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao remover: {str(e)}")

    def _get_wallon_questoes_config(self, template: str) -> Optional[Dict[str, str]]:
        """Abre dialog de configuração de questões para wallon_av2. Retorna config ou None se cancelou."""
        if 'wallon_av2' not in template.lower():
            return {}  # Dict vazio = sem config especial, prosseguir normalmente

        lista_dados = ListaControllerORM.buscar_lista(self.current_exam_codigo)
        if not lista_dados or not lista_dados.get('questoes'):
            return {}

        dialog = WallonQuestionConfigDialog(lista_dados['questoes'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_config()
        return None  # Cancelou

    def _on_generate_pdf(self):
        """Handle generate PDF button."""
        if not self.current_exam_codigo:
            QMessageBox.warning(self, "Aviso", "Selecione uma lista primeiro.")
            return

        template = self.template_combo.currentData()
        if not template:
            QMessageBox.warning(self, "Aviso", "Selecione um template válido.")
            return

        # Validar campos do template Wallon se necessário
        if 'wallon' in template.lower():
            if not self._validate_wallon_fields():
                return

        # Validar campos do template CEAB se necessário
        if 'ceab' in template.lower() or 'simulado' in template.lower():
            if not self._validate_ceab_fields():
                return

        # Dialog de configuração de questões (wallon_av2)
        questoes_config = self._get_wallon_questoes_config(template)
        if questoes_config is None:
            return  # Cancelou o dialog

        # Escolher diretório de saída
        output_dir = QFileDialog.getExistingDirectory(
            self, "Escolher pasta de saída",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not output_dir:
            return

        # Verificar se é exportação randomizada
        if self.randomize_checkbox.isChecked():
            self._perform_randomized_export(output_dir, template, 'direta', questoes_config)
            return

        from src.application.dtos.export_dto import ExportOptionsDTO

        opcoes = ExportOptionsDTO(
            id_lista=self.current_exam_codigo,
            template_latex=template,
            tipo_exportacao='direta',  # PDF
            output_dir=output_dir,
            layout_colunas=1 if self.single_column_radio.isChecked() else 2,
            incluir_gabarito=self.answer_key_checkbox.isChecked(),
            disciplina=self.disciplina_input.text().strip() or None,
            professor=self.professor_input.text().strip() or None,
            trimestre=self.trimestre_combo.currentData() or None,
            ano=self.ano_input.text().strip() or None,
            data_aplicacao=self.data_aplicacao_input.text().strip() or None,
            serie_simulado=self.serie_simulado_input.text().strip() or None,
            unidade=self.wallon_unidade_combo.currentData() or self.unidade_combo.currentData() or None,
            tipo_simulado=self.tipo_simulado_combo.currentData() or None,
            questoes_config=questoes_config if questoes_config else None
        )

        export_controller = criar_export_controller()

        # Dialog de progresso
        progress = ExportProgressDialog("Gerando PDF, aguarde...", parent=self)

        def on_finished(pdf_path):
            progress.close_dialog()
            reply = QMessageBox.question(
                self, "PDF Gerado",
                f"PDF gerado com sucesso!\n\n{pdf_path}\n\nDeseja abrir o arquivo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                export_controller.abrir_arquivo(pdf_path)

        def on_error(msg):
            progress.close_dialog()
            QMessageBox.critical(self, "Erro", f"Erro ao gerar PDF: {msg}")

        self._export_worker = ExportWorker(export_controller.exportar_lista, opcoes)
        self._export_worker.finished.connect(on_finished)
        self._export_worker.error.connect(on_error)
        self._export_worker.start()
        progress.exec()

    def _validate_wallon_fields(self) -> bool:
        """Validate Wallon template fields."""
        template = self.template_combo.currentData() or ""
        is_lista_wallon = 'listawallon' in template.lower()
        is_wallon_av2 = 'wallon_av2' in template.lower()

        missing = []
        if not self.disciplina_input.text().strip():
            missing.append("Disciplina")
        if not self.professor_input.text().strip():
            missing.append("Professor")
        # Validar Trimestre para wallon_av2
        if is_wallon_av2 and not self.trimestre_combo.currentData():
            missing.append("Trimestre")
        # Validar Unidade para listaWallon
        if is_lista_wallon and not self.wallon_unidade_combo.currentData():
            missing.append("Unidade")
        if not self.ano_input.text().strip():
            missing.append("Ano")

        if missing:
            QMessageBox.warning(
                self, "Campos obrigatórios",
                f"Preencha os seguintes campos para o template Wallon:\n• " + "\n• ".join(missing)
            )
            return False
        return True

    def _validate_ceab_fields(self) -> bool:
        """Validate CEAB template fields."""
        missing = []
        if not self.data_aplicacao_input.text().strip():
            missing.append("Data da Aplicacao")
        if not self.serie_simulado_input.text().strip():
            missing.append("Serie do Simulado")
        if not self.unidade_combo.currentData():
            missing.append("Unidade")
        if not self.tipo_simulado_combo.currentData():
            missing.append("Tipo de Simulado")

        if missing:
            QMessageBox.warning(
                self, "Campos obrigatorios",
                f"Preencha os seguintes campos para o template CEAB:\n- " + "\n- ".join(missing)
            )
            return False
        return True

    def _on_export_latex(self):
        """Handle export LaTeX button."""
        if not self.current_exam_codigo:
            QMessageBox.warning(self, "Aviso", "Selecione uma lista primeiro.")
            return

        template = self.template_combo.currentData()
        if not template:
            QMessageBox.warning(self, "Aviso", "Selecione um template válido.")
            return

        # Validar campos do template Wallon se necessário
        if 'wallon' in template.lower():
            if not self._validate_wallon_fields():
                return

        # Validar campos do template CEAB se necessário
        if 'ceab' in template.lower() or 'simulado' in template.lower():
            if not self._validate_ceab_fields():
                return

        # Dialog de configuração de questões (wallon_av2)
        questoes_config = self._get_wallon_questoes_config(template)
        if questoes_config is None:
            return  # Cancelou o dialog

        # Escolher diretório de saída
        output_dir = QFileDialog.getExistingDirectory(
            self, "Escolher pasta de saída",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not output_dir:
            return

        # Verificar se é exportação randomizada
        if self.randomize_checkbox.isChecked():
            self._perform_randomized_export(output_dir, template, 'manual', questoes_config)
            return

        from src.application.dtos.export_dto import ExportOptionsDTO

        opcoes = ExportOptionsDTO(
            id_lista=self.current_exam_codigo,
            template_latex=template,
            tipo_exportacao='manual',  # LaTeX
            output_dir=output_dir,
            layout_colunas=1 if self.single_column_radio.isChecked() else 2,
            incluir_gabarito=self.answer_key_checkbox.isChecked(),
            disciplina=self.disciplina_input.text().strip() or None,
            professor=self.professor_input.text().strip() or None,
            trimestre=self.trimestre_combo.currentData() or None,
            ano=self.ano_input.text().strip() or None,
            data_aplicacao=self.data_aplicacao_input.text().strip() or None,
            serie_simulado=self.serie_simulado_input.text().strip() or None,
            unidade=self.wallon_unidade_combo.currentData() or self.unidade_combo.currentData() or None,
            tipo_simulado=self.tipo_simulado_combo.currentData() or None,
            questoes_config=questoes_config if questoes_config else None
        )

        export_controller = criar_export_controller()

        progress = ExportProgressDialog("Exportando LaTeX, aguarde...", parent=self)

        def on_finished(tex_path):
            progress.close_dialog()
            QMessageBox.information(
                self, "Sucesso",
                f"Arquivo LaTeX exportado com sucesso!\n\n{tex_path}"
            )

        def on_error(msg):
            progress.close_dialog()
            QMessageBox.critical(self, "Erro", f"Erro ao exportar LaTeX: {msg}")

        self._export_worker = ExportWorker(export_controller.exportar_lista, opcoes)
        self._export_worker.finished.connect(on_finished)
        self._export_worker.error.connect(on_error)
        self._export_worker.start()
        progress.exec()

    def _perform_randomized_export(self, output_dir: str, template: str, tipo_exportacao: str, questoes_config: Optional[Dict[str, str]] = None):
        """Perform randomized export generating multiple versions."""
        from src.application.dtos.export_dto import ExportOptionsDTO

        # Validar campos do template CEAB se necessário
        if 'ceab' in template.lower() or 'simulado' in template.lower():
            if not self._validate_ceab_fields():
                return

        tipos = ['A', 'B', 'C', 'D']
        quantidade = self.versoes_spinbox.value()

        export_controller = criar_export_controller()

        # Construir lista de opções para cada versão
        opcoes_list = []
        for i in range(quantidade):
            tipo = tipos[i]
            opcoes = ExportOptionsDTO(
                id_lista=self.current_exam_codigo,
                template_latex=template,
                tipo_exportacao=tipo_exportacao,
                output_dir=output_dir,
                layout_colunas=1 if self.single_column_radio.isChecked() else 2,
                incluir_gabarito=self.answer_key_checkbox.isChecked(),
                disciplina=self.disciplina_input.text().strip() or None,
                professor=self.professor_input.text().strip() or None,
                trimestre=self.trimestre_combo.currentData() or None,
                ano=self.ano_input.text().strip() or None,
                data_aplicacao=self.data_aplicacao_input.text().strip() or None,
                serie_simulado=self.serie_simulado_input.text().strip() or None,
                unidade=self.wallon_unidade_combo.currentData() or self.unidade_combo.currentData() or None,
                tipo_simulado=self.tipo_simulado_combo.currentData() or None,
                gerar_versoes_randomizadas=True,
                quantidade_versoes=quantidade,
                sufixo_versao=f"TIPO {tipo}",
                questoes_config=questoes_config if questoes_config else None
            )
            opcoes_list.append((opcoes, i))

        def run_randomized():
            arquivos = []
            for opcoes, indice in opcoes_list:
                result_path = export_controller.exportar_lista_randomizada(opcoes, indice_versao=indice)
                if result_path:
                    arquivos.append(result_path)
            return arquivos

        extensao = "PDF" if tipo_exportacao == 'direta' else "LaTeX"
        progress = ExportProgressDialog(f"Gerando {quantidade} versões {extensao}, aguarde...", parent=self)

        def on_finished(arquivos_gerados):
            progress.close_dialog()
            if arquivos_gerados:
                msg = f"Versões {extensao} geradas com sucesso!\n\nArquivos criados em:\n{output_dir}\n\n"
                msg += "Arquivos:\n" + "\n".join([f"• {p.name}" for p in arquivos_gerados])

                if tipo_exportacao == 'direta':
                    msg += "\n\nDeseja abrir os arquivos?"
                    reply = QMessageBox.question(
                        self, "Sucesso", msg,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        for pdf_path in arquivos_gerados:
                            export_controller.abrir_arquivo(pdf_path)
                else:
                    QMessageBox.information(self, "Sucesso", msg)
            else:
                QMessageBox.warning(self, "Erro", "Nenhum arquivo foi gerado.")

        def on_error(msg):
            progress.close_dialog()
            QMessageBox.critical(self, "Erro", f"Erro ao gerar versões randomizadas: {msg}")

        self._export_worker = ExportWorker(run_randomized)
        self._export_worker.finished.connect(on_finished)
        self._export_worker.error.connect(on_error)
        self._export_worker.start()
        progress.exec()

    def _get_export_config(self) -> Dict:
        """Get current export configuration."""
        return {
            "codigo_lista": self.current_exam_codigo,
            "template": self.template_combo.currentData(),
            "columns": 1 if self.single_column_radio.isChecked() else 2,
            "include_answer_key": self.answer_key_checkbox.isChecked(),
            "include_point_values": self.point_values_checkbox.isChecked(),
            "include_work_space": self.work_space_checkbox.isChecked(),
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
