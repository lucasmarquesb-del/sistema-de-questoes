# src/views/pages/question_editor_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QStackedWidget, QSpacerItem, QSizePolicy, QFrame,
    QCompleter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from src.controllers.adapters import criar_tag_controller
from src.views.design.constants import Color, Spacing, Typography, Dimensions, Text
from src.views.design.enums import ActionEnum, PageEnum
from src.views.components.common.buttons import PrimaryButton, SecondaryButton, IconButton
from src.views.components.question.editor_tab import EditorTab
from src.views.components.question.preview_tab import PreviewTab
from src.views.components.question.tags_tab import TagsTab

class QuestionEditorPage(QWidget):
    """
    Main page for creating and editing questions.
    Combines Editor, Preview, and Tags tabs.
    """
    back_to_questions_requested = pyqtSignal() # To navigate back to question bank
    save_requested = pyqtSignal(dict) # Emits question data
    cancel_requested = pyqtSignal() # Emits cancellation signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("question_editor_page")

        self.question_data = {} # Dictionary to hold all question data

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar: Back, Title, View Options, Cancel, Save
        top_bar_frame = QFrame(self)
        top_bar_frame.setObjectName("editor_top_bar")
        top_bar_frame.setStyleSheet(f"""
            QFrame#editor_top_bar {{
                background-color: {Color.WHITE};
                border-bottom: 1px solid {Color.BORDER_LIGHT};
                min-height: {Dimensions.NAVBAR_HEIGHT}px;
            }}
        """)
        top_bar_layout = QHBoxLayout(top_bar_frame)
        top_bar_layout.setContentsMargins(Spacing.XL, 0, Spacing.XL, 0)
        top_bar_layout.setSpacing(Spacing.LG)
        top_bar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.back_button = IconButton(icon_path="images/icons/arrow_left.png", size=QSize(20,20), parent=top_bar_frame)
        self.back_button.setToolTip("Voltar para o Banco de Questões")
        self.back_button.clicked.connect(self.back_to_questions_requested.emit)
        top_bar_layout.addWidget(self.back_button)

        title_label = QLabel(f"MathBank / Criar Questão", top_bar_frame)
        title_label.setObjectName("editor_title")
        title_label.setStyleSheet(f"font-size: {Typography.FONT_SIZE_XL}; font-weight: {Typography.FONT_WEIGHT_BOLD}; color: {Color.DARK_TEXT};")
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()

        # View Options (Editor View / Dual Pane) - Placeholder
        view_options_label = QLabel("[Editor View] [Dual Pane]", top_bar_frame)
        view_options_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: {Typography.FONT_SIZE_MD};")
        top_bar_layout.addWidget(view_options_label)

        self.cancel_button = SecondaryButton("Cancelar", parent=top_bar_frame)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        top_bar_layout.addWidget(self.cancel_button)

        self.save_button = PrimaryButton("Salvar Questão", parent=top_bar_frame)
        self.save_button.setEnabled(False) # Disabled by default, enabled on valid content + tags
        self.save_button.clicked.connect(self._on_save_clicked)
        top_bar_layout.addWidget(self.save_button)
        main_layout.addWidget(top_bar_frame)

        # Tab Widget for Editor, Preview, Tags
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("question_editor_tabs")
        self.tab_widget.setStyleSheet(f"""
            QTabWidget#question_editor_tabs {{
                background-color: {Color.LIGHT_BACKGROUND};
            }}
            QTabWidget#question_editor_tabs::pane {{
                border: 1px solid {Color.BORDER_LIGHT};
                background-color: {Color.LIGHT_BACKGROUND};
            }}
            QTabBar::tab {{
                background-color: {Color.WHITE};
                border: 1px solid {Color.BORDER_LIGHT};
                border-bottom-color: {Color.BORDER_LIGHT}; /* Same as pane border */
                border-top-left-radius: {Dimensions.BORDER_RADIUS_MD};
                border-top-right-radius: {Dimensions.BORDER_RADIUS_MD};
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                color: {Color.GRAY_TEXT};
            }}
            QTabBar::tab:selected {{
                background-color: {Color.LIGHT_BACKGROUND};
                border-bottom-color: {Color.LIGHT_BACKGROUND}; /* Selected tab blends with content */
                color: {Color.PRIMARY_BLUE};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            }}
            QTabBar::tab:hover {{
                background-color: {Color.BORDER_LIGHT};
            }}
        """)

        self.editor_tab = EditorTab(self)
        self.preview_tab = PreviewTab(self)
        self.tags_tab = TagsTab(self)

        self.tab_widget.addTab(self.editor_tab, QIcon("images/icons/edit.png"), "Editor") # Placeholder icons
        self.tab_widget.addTab(self.preview_tab, QIcon("images/icons/preview.png"), "Preview")
        self.tab_widget.addTab(self.tags_tab, QIcon("images/icons/tags.png"), "Tags")

        main_layout.addWidget(self.tab_widget)

        # Bottom Bar: Status and Language
        bottom_bar_frame = QFrame(self)
        bottom_bar_frame.setObjectName("editor_bottom_bar")
        bottom_bar_frame.setStyleSheet(f"""
            QFrame#editor_bottom_bar {{
                background-color: {Color.WHITE};
                border-top: 1px solid {Color.BORDER_LIGHT};
                min-height: 30px;
            }}
        """)
        bottom_bar_layout = QHBoxLayout(bottom_bar_frame)
        bottom_bar_layout.setContentsMargins(Spacing.XL, Spacing.XS, Spacing.XL, Spacing.XS)
        bottom_bar_layout.setSpacing(Spacing.LG)
        bottom_bar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(Spacing.SM)
        status_icon = QLabel(bottom_bar_frame)
        status_icon.setPixmap(QIcon.fromTheme("document-save").pixmap(12, 12))
        self.status_label = QLabel("Auto-saved 2 mins ago", bottom_bar_frame)
        self.status_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: {Typography.FONT_SIZE_XS};")
        status_layout.addWidget(status_icon)
        status_layout.addWidget(self.status_label)
        bottom_bar_layout.addLayout(status_layout)
        bottom_bar_layout.addStretch()

        language_label = QLabel("QUESTION LANGUAGE: EN-US", bottom_bar_frame)
        language_label.setStyleSheet(f"color: {Color.GRAY_TEXT}; font-size: {Typography.FONT_SIZE_XS};")
        bottom_bar_layout.addWidget(language_label)
        main_layout.addWidget(bottom_bar_frame)

        self.setLayout(main_layout)

        self._connect_signals()
        self._update_save_button_state() # Initial state check
        self._setup_origin_autocomplete()

    def _connect_signals(self):
        self.editor_tab.content_changed.connect(self._update_question_data)
        self.editor_tab.content_changed.connect(self._update_save_button_state)
        self.editor_tab.content_changed.connect(self._update_preview)
        self.tags_tab.tags_changed.connect(self._on_tags_changed)
        self.tags_tab.tags_changed.connect(self._update_save_button_state)
        self.tab_widget.currentChanged.connect(self._on_tab_changed) # Update preview when switching to preview tab

        # Conectar botões de adicionar imagem
        self.editor_tab.add_image_statement_button.clicked.connect(
            lambda: self._insert_image(self.editor_tab.statement_input)
        )
        self.editor_tab.add_image_answer_button.clicked.connect(
            lambda: self._insert_image(self.editor_tab.answer_key_input)
        )
        # Conectar botões de imagem nas alternativas
        for alt_widget in self.editor_tab.alternatives_widgets:
            if hasattr(alt_widget, 'add_image_button'):
                alt_widget.add_image_button.clicked.connect(
                    lambda checked, ti=alt_widget.text_input: self._insert_image_to_line_edit(ti)
                )

    def _update_question_data(self):
        # Gather data from editor tab
        self.question_data['academic_year'] = self.editor_tab.academic_year_input.text()
        self.question_data['origin'] = self.editor_tab.origin_input.text()
        self.question_data['statement'] = self.editor_tab.statement_input.toPlainText()
        self.question_data['question_type'] = self.editor_tab.current_question_type

        if self.question_data['question_type'] == "objective":
            self.question_data['alternatives'] = []
            for alt_widget in self.editor_tab.alternatives_widgets:
                self.question_data['alternatives'].append({
                    'text': alt_widget.text_input.text(),
                    'is_correct': alt_widget.radio_button.isChecked()
                })
            self.question_data.pop('answer_key', None) # Remove answer_key if it exists
        else: # discursive
            self.question_data['answer_key'] = self.editor_tab.answer_key_input.toPlainText()
            self.question_data.pop('alternatives', None) # Remove alternatives if it exists

    def _on_tags_changed(self, selected_tag_uuids: list):
        self.question_data['tags'] = selected_tag_uuids

    def _update_preview(self):
        # Simple HTML generation for preview (will be more sophisticated with LaTeX rendering)
        question_html = f"<h2>Pré-visualização da Questão</h2>"
        question_html += f"<p><b>Ano:</b> {self.question_data.get('academic_year', '')}</p>"
        question_html += f"<p><b>Origem:</b> {self.question_data.get('origin', '')}</p>"
        question_html += f"<p><b>Tipo:</b> {self.question_data.get('question_type', '')}</p>"
        question_html += f"<h3>Enunciado:</h3><p>{self.question_data.get('statement', '')}</p>"

        resolution_html = None
        if self.question_data.get('question_type') == 'objective':
            question_html += "<h3>Alternativas:</h3><ol type='A'>"
            for alt in self.question_data.get('alternatives', []):
                checked = " (Correta)" if alt['is_correct'] else ""
                question_html += f"<li>{alt['text']}{checked}</li>"
            question_html += "</ol>"
        else: # discursive
            resolution_html = f"<h3>Chave de Resposta:</h3><p>{self.question_data.get('answer_key', '')}</p>"

        self.preview_tab.set_question_data(question_html, resolution_html)

    def _update_save_button_state(self):
        # Validacao completa para habilitar o botao de salvar
        statement_ok = bool(self.editor_tab.statement_input.toPlainText().strip())
        origin_ok = bool(self.editor_tab.origin_input.text().strip())
        tags_ok = bool(self.question_data.get('tags'))

        # Verificar alternativa correta se for objetiva
        correct_alt_ok = True
        if self.editor_tab.current_question_type == "objective":
            has_correct = any(
                alt_widget.radio_button.isChecked()
                for alt_widget in self.editor_tab.alternatives_widgets
            )
            correct_alt_ok = has_correct

        self.save_button.setEnabled(statement_ok and origin_ok and tags_ok and correct_alt_ok)

    def _validate_question(self) -> tuple:
        """Valida os dados da questao antes de salvar. Retorna (valido, mensagem_erro)."""
        errors = []

        # Verificar enunciado
        if not self.editor_tab.statement_input.toPlainText().strip():
            errors.append("O enunciado da questao e obrigatorio.")

        # Verificar origem/fonte
        if not self.editor_tab.origin_input.text().strip():
            errors.append("A origem/fonte da questao e obrigatoria.")

        # Verificar tags
        if not self.question_data.get('tags'):
            errors.append("E necessario selecionar pelo menos uma tag de conteudo.")

        # Verificar alternativa correta (apenas para objetivas)
        if self.editor_tab.current_question_type == "objective":
            has_correct = any(
                alt_widget.radio_button.isChecked()
                for alt_widget in self.editor_tab.alternatives_widgets
            )
            if not has_correct:
                errors.append("E necessario marcar uma alternativa como correta.")

            # Verificar se todas as alternativas tem texto
            empty_alts = []
            for alt_widget in self.editor_tab.alternatives_widgets:
                if not alt_widget.text_input.text().strip():
                    letra = alt_widget.radio_button.text()
                    empty_alts.append(letra)
            if empty_alts:
                errors.append(f"As alternativas {', '.join(empty_alts)} estao vazias.")

        if errors:
            return False, "\n".join(errors)
        return True, ""

    def _on_save_clicked(self):
        # Atualizar dados antes de validar
        self._update_question_data()

        # Validar questao
        valido, erro = self._validate_question()
        if not valido:
            QMessageBox.warning(self, "Validacao", erro)
            return

        self.save_requested.emit(self.question_data)
        self.status_label.setText("Questão salva com sucesso!")

    def _on_tab_changed(self, index: int):
        if self.tab_widget.widget(index) == self.preview_tab:
            self._update_preview()

    def _setup_origin_autocomplete(self):
        """Configura auto-complete para o campo de origem/fonte."""
        try:
            from src.controllers.adapters import listar_fontes_questao
            fontes = listar_fontes_questao()
            # Usar siglas para o autocomplete (ENEM, FUVEST, etc)
            siglas = [f['sigla'] for f in fontes]
            completer = QCompleter(siglas, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.editor_tab.origin_input.setCompleter(completer)
        except Exception as e:
            print(f"Erro ao configurar auto-complete de origem: {e}")

    def _insert_image(self, text_area):
        """Insere uma imagem em um QTextEdit/LatexTextArea."""
        from src.views.components.dialogs.image_insert_dialog import ImageInsertDialog
        dialog = ImageInsertDialog(self)
        if dialog.exec():
            caminho = dialog.get_image_path()
            escala = dialog.get_scale()
            if caminho:
                placeholder = f"[IMG:{caminho}:{escala}]"
                cursor = text_area.textCursor()
                cursor.insertText(placeholder)
                text_area.setTextCursor(cursor)

    def _insert_image_to_line_edit(self, line_edit):
        """Insere uma imagem em um QLineEdit/TextInput."""
        from src.views.components.dialogs.image_insert_dialog import ImageInsertDialog
        dialog = ImageInsertDialog(self)
        if dialog.exec():
            caminho = dialog.get_image_path()
            escala = dialog.get_scale()
            if caminho:
                placeholder = f"[IMG:{caminho}:{escala}]"
                texto_atual = line_edit.text()
                cursor_pos = line_edit.cursorPosition()
                novo_texto = texto_atual[:cursor_pos] + placeholder + texto_atual[cursor_pos:]
                line_edit.setText(novo_texto)


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
            self.setWindowTitle("Question Editor Page Test")
            self.setGeometry(100, 100, 1200, 900)

            self.editor_page = QuestionEditorPage(self)
            self.setCentralWidget(self.editor_page)

            self.editor_page.back_to_questions_requested.connect(lambda: print("Back to questions requested!"))
            self.editor_page.save_requested.connect(lambda data: print(f"Save requested: {data}"))
            self.editor_page.cancel_requested.connect(lambda: print("Cancel requested!"))

    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())