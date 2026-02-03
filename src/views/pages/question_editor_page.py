# src/views/pages/question_editor_page.py
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QStackedWidget, QSpacerItem, QSizePolicy, QFrame,
    QCompleter, QMessageBox, QInputDialog
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
        self.editing_question_id = None  # ID da questão em edição (None = criação)
        self.is_editing = False  # Modo de edição
        self.is_variant = False  # Modo de criação de variante
        self.original_data = None  # Dados da questão original (para variante)
        self.original_codigo = None  # Código da questão original

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

        self.title_label = QLabel(f"MathBank / Criar Questão", top_bar_frame)
        self.title_label.setObjectName("editor_title")
        self.title_label.setStyleSheet(f"font-size: {Typography.FONT_SIZE_XL}; font-weight: {Typography.FONT_WEIGHT_BOLD}; color: {Color.DARK_TEXT};")
        top_bar_layout.addWidget(self.title_label)
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
        self.question_data['school_level_uuid'] = self.editor_tab.get_selected_school_level_uuid()
        self.question_data['statement'] = self.editor_tab.statement_input.toPlainText()
        self.question_data['question_type'] = self.editor_tab.current_question_type
        self.question_data['difficulty'] = self.editor_tab.difficulty_group.checkedId()

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
        # Atualizar dados antes de gerar preview
        self._update_question_data()

        # HTML generation for preview with table and list support
        difficulty_map = {1: 'Fácil', 2: 'Médio', 3: 'Difícil'}
        difficulty_id = self.question_data.get('difficulty', -1)
        difficulty_name = difficulty_map.get(difficulty_id, 'Não selecionada')

        # Obter nome do nível escolar
        school_level_name = '-'
        school_level_uuid = self.question_data.get('school_level_uuid')
        if school_level_uuid:
            combo = self.editor_tab.school_level_combo
            idx = combo.currentIndex()
            if idx > 0:
                school_level_name = combo.currentText()

        # Processar enunciado com formatações
        statement_raw = self.question_data.get('statement', '')
        statement_formatted = self._format_text_for_preview(statement_raw)

        # Tipo de questão formatado
        tipo_display = 'Objetiva' if self.question_data.get('question_type') == 'objective' else 'Discursiva'

        question_html = f"<h2 style='margin-bottom:10px;'>Pré-visualização da Questão</h2>"
        question_html += f"<p style='margin:3px 0;'><b>Ano:</b> {self.question_data.get('academic_year', '') or '-'}</p>"
        question_html += f"<p style='margin:3px 0;'><b>Origem:</b> {self.question_data.get('origin', '') or '-'}</p>"
        question_html += f"<p style='margin:3px 0;'><b>Nível Escolar:</b> {school_level_name}</p>"
        question_html += f"<p style='margin:3px 0;'><b>Tipo:</b> {tipo_display}</p>"
        question_html += f"<p style='margin:3px 0;'><b>Dificuldade:</b> {difficulty_name}</p>"
        question_html += f"<h3 style='margin-top:15px; margin-bottom:8px;'>Enunciado:</h3>"
        question_html += f"<div style='line-height:1.5;'>{statement_formatted}</div>"

        resolution_html = None
        if self.question_data.get('question_type') == 'objective':
            question_html += "<h3 style='margin-top:15px; margin-bottom:8px;'>Alternativas:</h3><ol type='A' style='margin:5px 0; padding-left:25px;'>"
            for alt in self.question_data.get('alternatives', []):
                checked = " <span style='color: green;'>✓ (Correta)</span>" if alt.get('is_correct') else ""
                alt_text = self._format_text_for_preview(alt.get('text', ''))
                question_html += f"<li style='margin:3px 0;'>{alt_text}{checked}</li>"
            question_html += "</ol>"
        else:  # discursive
            answer_key_raw = self.question_data.get('answer_key', '')
            if answer_key_raw:
                answer_key_formatted = self._format_text_for_preview(answer_key_raw)
                resolution_html = f"<h3 style='margin-bottom:8px;'>Chave de Resposta:</h3><div style='line-height:1.5;'>{answer_key_formatted}</div>"

        self.preview_tab.set_question_data(question_html, resolution_html)

    def _format_text_for_preview(self, texto: str) -> str:
        """Formata texto para preview, processando tabelas, listas e formatações."""
        if not texto:
            return ""

        # Processar tabelas primeiro (antes de converter newlines)
        texto = self._processar_tabelas_para_html(texto)

        # Processar listas
        texto = self._processar_listas_para_html(texto)

        # Processar formatações de texto
        texto = self._processar_formatacoes_texto(texto)

        # Converter múltiplas quebras de linha em uma única <br>
        texto = re.sub(r'\n{2,}', '<br><br>', texto)
        texto = texto.replace('\n', '<br>')

        # Remover <br> redundantes ao redor de tabelas
        texto = re.sub(r'(<br>)+(<table)', r'\2', texto)
        texto = re.sub(r'(</table>)(<br>)+', r'\1', texto)

        return texto

    def _processar_tabelas_para_html(self, texto: str) -> str:
        """Converte tabelas no formato [TABELA]...[/TABELA] para HTML."""
        table_pattern = re.compile(
            r'\[TABELA\]\s*\n(.*?)\[/TABELA\]',
            re.DOTALL
        )

        def convert_table(match):
            table_content = match.group(1).strip()
            lines = table_content.split('\n')

            if not lines:
                return ''

            html_lines = []
            html_lines.append('<table style="width:80%; border-collapse:collapse; margin:10px auto; font-size:11px;">')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                is_header = '[CABECALHO]' in line
                if is_header:
                    line = line.replace('[CABECALHO]', '').replace('[/CABECALHO]', '')

                cells = [cell.strip() for cell in line.split('|')]

                html_lines.append('<tr>')
                for cell in cells:
                    cell_html = self._processar_formatacao_celula_html(cell)
                    if is_header:
                        html_lines.append(f'<th style="border:1px solid #333; padding:2px 6px; background:#e0e0e0;">{cell_html}</th>')
                    else:
                        html_lines.append(f'<td style="border:1px solid #333; padding:2px 6px; text-align:center;">{cell_html}</td>')
                html_lines.append('</tr>')

            html_lines.append('</table>')
            # Usar espaço vazio para juntar, evitando <br> extras após conversão
            return ''.join(html_lines)

        return table_pattern.sub(convert_table, texto)

    def _processar_formatacao_celula_html(self, cell_text: str) -> str:
        """Processa formatações de uma célula de tabela para HTML."""
        result = cell_text

        # Processar cor de fundo
        color_pattern = re.compile(r'\[COR:#([a-fA-F0-9]{6})\](.*?)\[/COR\]', re.DOTALL)
        color_match = color_pattern.search(result)
        cell_style = ''
        if color_match:
            cell_color = color_match.group(1)
            cell_style = f' style="background-color: #{cell_color};"'
            result = color_pattern.sub(r'\2', result)

        if cell_style:
            result = f'<span{cell_style}>{result}</span>'

        return result

    def _processar_listas_para_html(self, texto: str) -> str:
        """Converte listas visuais para HTML."""
        lines = texto.split('\n')
        result = []
        in_list = False
        list_type = None

        itemize_symbols = r'[•○■□▸✓★–]'
        itemize_pattern = re.compile(rf'^[ ]{{2,4}}({itemize_symbols})\s+(.+)$')
        arabic_pattern = re.compile(r'^[ ]{2,4}(\d+)\.\s+(.+)$')
        alpha_lower_pattern = re.compile(r'^[ ]{2,4}([a-z])\)\s+(.+)$')
        alpha_upper_pattern = re.compile(r'^[ ]{2,4}([A-Z])\)\s+(.+)$')
        roman_lower_pattern = re.compile(r'^[ ]{2,4}(i{1,3}|iv|vi{0,3}|ix|xi{0,3})\.\s+(.+)$')
        roman_upper_pattern = re.compile(r'^[ ]{2,4}(I{1,3}|IV|VI{0,3}|IX|XI{0,3})\.\s+(.+)$')

        def close_list():
            nonlocal in_list, list_type
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
                list_type = None

        for line in lines:
            itemize_match = itemize_pattern.match(line)
            if itemize_match:
                if not in_list or list_type != 'ul':
                    close_list()
                    result.append('<ul style="margin:5px 0;padding-left:25px;">')
                    in_list = True
                    list_type = 'ul'
                result.append(f'<li style="margin:2px 0;">{itemize_match.group(2)}</li>')
                continue

            arabic_match = arabic_pattern.match(line)
            if arabic_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="margin:5px 0;padding-left:25px;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li style="margin:2px 0;">{arabic_match.group(2)}</li>')
                continue

            alpha_lower_match = alpha_lower_pattern.match(line)
            if alpha_lower_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="margin:5px 0;padding-left:25px;list-style-type:lower-alpha;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li style="margin:2px 0;">{alpha_lower_match.group(2)}</li>')
                continue

            alpha_upper_match = alpha_upper_pattern.match(line)
            if alpha_upper_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="margin:5px 0;padding-left:25px;list-style-type:upper-alpha;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li style="margin:2px 0;">{alpha_upper_match.group(2)}</li>')
                continue

            roman_lower_match = roman_lower_pattern.match(line)
            if roman_lower_match and roman_lower_match.group(1).islower():
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="margin:5px 0;padding-left:25px;list-style-type:lower-roman;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li style="margin:2px 0;">{roman_lower_match.group(2)}</li>')
                continue

            roman_upper_match = roman_upper_pattern.match(line)
            if roman_upper_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="margin:5px 0;padding-left:25px;list-style-type:upper-roman;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li style="margin:2px 0;">{roman_upper_match.group(2)}</li>')
                continue

            if line.strip() and in_list:
                close_list()

            result.append(line)

        close_list()
        # Juntar sem newlines para evitar <br> extras
        return ''.join(result)

    def _processar_formatacoes_texto(self, texto: str) -> str:
        """Processa formatações de texto (negrito, itálico, etc.) para HTML."""
        # Tags HTML simples já estão em HTML
        # Processar comandos LaTeX
        texto = re.sub(r'\\textbf\{([^}]*)\}', r'<b>\1</b>', texto)
        texto = re.sub(r'\\textit\{([^}]*)\}', r'<i>\1</i>', texto)
        texto = re.sub(r'\\underline\{([^}]*)\}', r'<u>\1</u>', texto)
        texto = re.sub(r'\\textsuperscript\{([^}]*)\}', r'<sup>\1</sup>', texto)
        texto = re.sub(r'\\textsubscript\{([^}]*)\}', r'<sub>\1</sub>', texto)

        # Letras gregas
        gregas = {
            r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
            r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
            r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
            r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
            r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
            r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
            r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
            r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Upsilon': 'Υ',
            r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
        }
        texto = re.sub(r'\$([^$]+)\$', r'\1', texto)
        for latex, unicode_char in gregas.items():
            texto = texto.replace(latex, unicode_char)

        return texto

    def _update_save_button_state(self):
        # Validacao completa para habilitar o botao de salvar
        statement_ok = bool(self.editor_tab.statement_input.toPlainText().strip())

        # No modo variante, campos herdados já estão preenchidos e desabilitados
        if self.is_variant:
            origin_ok = True
            school_level_ok = True
            tags_ok = True
        else:
            origin_ok = bool(self.editor_tab.origin_input.text().strip())
            school_level_ok = bool(self.editor_tab.get_selected_school_level_uuid())
            tags_ok = bool(self.question_data.get('tags'))

        # Verificar alternativa correta se for objetiva
        correct_alt_ok = True
        if self.editor_tab.current_question_type == "objective":
            has_correct = any(
                alt_widget.radio_button.isChecked()
                for alt_widget in self.editor_tab.alternatives_widgets
            )
            correct_alt_ok = has_correct

        self.save_button.setEnabled(statement_ok and origin_ok and school_level_ok and tags_ok and correct_alt_ok)

    def _validate_question(self) -> tuple:
        """Valida os dados da questao antes de salvar. Retorna (valido, mensagem_erro)."""
        errors = []

        # Verificar enunciado
        if not self.editor_tab.statement_input.toPlainText().strip():
            errors.append("O enunciado da questao e obrigatorio.")

        # Verificar origem/fonte
        if not self.editor_tab.origin_input.text().strip():
            errors.append("A origem/fonte da questao e obrigatoria.")

        # Verificar nível escolar
        if not self.editor_tab.get_selected_school_level_uuid():
            errors.append("O nivel escolar e obrigatorio.")

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

        # Se é modo variante, usar fluxo específico
        if self.is_variant:
            self._save_variant()
            return

        # Validar questao
        valido, erro = self._validate_question()
        if not valido:
            QMessageBox.warning(self, "Validacao", erro)
            return

        # Gerar titulo automaticamente: FONTE - TAG PRINCIPAL - ANO
        tags_with_names = self.tags_tab.get_selected_content_tags_with_names()
        tag_principal_nome = None

        if len(tags_with_names) > 1:
            # Perguntar qual tag e a principal
            nomes = [nome for _, nome in tags_with_names]
            escolhido, ok = QInputDialog.getItem(
                self,
                "Tag Principal",
                "A questao possui multiplas tags.\nSelecione a tag principal para o titulo:",
                nomes,
                0,
                False
            )
            if not ok:
                return
            tag_principal_nome = escolhido

            # Reordenar tags para colocar a principal primeiro
            idx_principal = nomes.index(escolhido)
            uuid_principal = tags_with_names[idx_principal][0]
            tags = self.question_data.get('tags', [])
            if uuid_principal in tags:
                tags.remove(uuid_principal)
                tags.insert(0, uuid_principal)
                self.question_data['tags'] = tags
        elif len(tags_with_names) == 1:
            tag_principal_nome = tags_with_names[0][1]

        # Montar titulo: FONTE - TAG - ANO
        fonte = self.editor_tab.origin_input.text().strip().upper()
        ano = self.editor_tab.academic_year_input.text().strip()
        titulo_partes = []
        if fonte:
            titulo_partes.append(fonte)
        if tag_principal_nome:
            titulo_partes.append(tag_principal_nome)
        if ano:
            titulo_partes.append(ano)

        self.question_data['titulo'] = ' - '.join(titulo_partes) if titulo_partes else None

        self.save_requested.emit(self.question_data)
        self.status_label.setText("Questão salva com sucesso!")

    def _save_variant(self):
        """Salva a questão como variante (criação ou edição)."""
        from src.controllers.questao_controller_orm import QuestaoControllerORM

        # Validar apenas campos editáveis
        if not self.editor_tab.statement_input.toPlainText().strip():
            QMessageBox.warning(self, "Validacao", "O enunciado da questao e obrigatorio.")
            return

        # Verificar alternativa correta (apenas para objetivas)
        tipo = self.original_data.get('tipo', 'OBJETIVA') if self.original_data else 'OBJETIVA'
        if tipo == 'OBJETIVA':
            has_correct = any(
                alt_widget.radio_button.isChecked()
                for alt_widget in self.editor_tab.alternatives_widgets
            )
            if not has_correct:
                QMessageBox.warning(self, "Validacao", "E necessario marcar uma alternativa como correta.")
                return

            # Verificar se todas as alternativas tem texto
            empty_alts = []
            for alt_widget in self.editor_tab.alternatives_widgets:
                if not alt_widget.text_input.text().strip():
                    letra = alt_widget.radio_button.text()
                    empty_alts.append(letra)
            if empty_alts:
                QMessageBox.warning(self, "Validacao", f"As alternativas {', '.join(empty_alts)} estao vazias.")
                return

        # Coletar dados editáveis
        enunciado = self.editor_tab.statement_input.toPlainText()

        # Coletar alternativas
        alternativas = []
        if tipo == 'OBJETIVA':
            for i, alt_widget in enumerate(self.editor_tab.alternatives_widgets):
                letra = chr(ord('A') + i)
                alternativas.append({
                    'letra': letra,
                    'texto': alt_widget.text_input.text().strip(),
                    'correta': alt_widget.radio_button.isChecked()
                })

        # Resolução (gabarito discursivo)
        resolucao = self.editor_tab.answer_key_input.toPlainText() or None

        try:
            if self.is_editing:
                # Edição de variante existente - atualizar apenas campos editáveis
                resultado = QuestaoControllerORM.atualizar_questao(
                    self.editing_question_id,
                    enunciado=enunciado,
                    alternativas=alternativas if tipo == 'OBJETIVA' else None
                )

                if resultado:
                    self.status_label.setText(f"Variante {self.editing_question_id} atualizada com sucesso!")
                    self.question_data['codigo_variante'] = self.editing_question_id
                    self.question_data['is_variant'] = True
                    self.question_data['is_editing'] = True
                    self.save_requested.emit(self.question_data)
                else:
                    QMessageBox.warning(self, "Falha", "Nao foi possivel atualizar a variante.")
            else:
                # Criação de nova variante
                resultado = QuestaoControllerORM.criar_variante(
                    codigo_original=self.original_codigo,
                    enunciado=enunciado,
                    alternativas=alternativas if tipo == 'OBJETIVA' else None,
                    resolucao=resolucao,
                    observacoes=None
                )

                if resultado:
                    codigo_variante = resultado.get('codigo', 'N/A')
                    self.status_label.setText(f"Variante {codigo_variante} criada com sucesso!")
                    self.question_data['codigo_variante'] = codigo_variante
                    self.question_data['is_variant'] = True
                    self.save_requested.emit(self.question_data)
                else:
                    QMessageBox.warning(
                        self,
                        "Falha",
                        "Nao foi possivel criar a variante.\nVerifique se a questao original ja possui 3 variantes."
                    )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar variante: {str(e)}")

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

    def load_question_for_editing(self, questao_data: dict):
        """Carrega dados de uma questão para edição."""
        from src.controllers.questao_controller_orm import QuestaoControllerORM

        self.is_editing = True
        self.editing_question_id = questao_data.get('codigo') or questao_data.get('id')

        # Verificar se esta questão é uma variante
        self.is_variant = QuestaoControllerORM.eh_variante(self.editing_question_id)
        if self.is_variant:
            original = QuestaoControllerORM.obter_questao_original(self.editing_question_id)
            self.original_codigo = original.get('codigo') if original else None
            self.original_data = questao_data  # Usar os dados atuais como referência
            self.title_label.setText(f"MathBank / Editar Variante #{self.editing_question_id}")
        else:
            self.is_variant = False
            self.original_codigo = None
            self.original_data = None
            self.title_label.setText(f"MathBank / Editar Questão #{self.editing_question_id}")

        # Preencher campos do editor
        self.editor_tab.academic_year_input.setText(str(questao_data.get('ano', '')))
        self.editor_tab.origin_input.setText(questao_data.get('fonte', '') or '')
        self.editor_tab.statement_input.setPlainText(questao_data.get('enunciado', '') or '')

        # Carregar nível escolar
        niveis = questao_data.get('niveis_escolares', [])
        if niveis:
            # Pegar o primeiro nível (pode ser adaptado para múltiplos níveis)
            nivel = niveis[0] if isinstance(niveis, list) else niveis
            nivel_uuid = nivel.get('uuid') if isinstance(nivel, dict) else nivel
            self.editor_tab.set_school_level_by_uuid(nivel_uuid)
        else:
            self.editor_tab.school_level_combo.setCurrentIndex(0)

        # Tipo de questão
        tipo = questao_data.get('tipo', 'OBJETIVA')
        if tipo == 'OBJETIVA':
            self.editor_tab.objective_radio.setChecked(True)
            self.editor_tab.current_question_type = "objective"
        else:
            self.editor_tab.discursive_radio.setChecked(True)
            self.editor_tab.current_question_type = "discursive"
        self.editor_tab._update_visibility_by_question_type()

        # Dificuldade
        dificuldade = questao_data.get('dificuldade', '')
        if dificuldade:
            dif_map = {'FACIL': 1, 'MEDIO': 2, 'DIFICIL': 3}
            dif_id = dif_map.get(dificuldade.upper(), 0)
            if dif_id == 1:
                self.editor_tab.difficulty_easy.setChecked(True)
            elif dif_id == 2:
                self.editor_tab.difficulty_medium.setChecked(True)
            elif dif_id == 3:
                self.editor_tab.difficulty_hard.setChecked(True)

        # Alternativas (se objetiva)
        if tipo == 'OBJETIVA':
            alternativas = questao_data.get('alternativas', [])
            for i, alt in enumerate(alternativas):
                if i < len(self.editor_tab.alternatives_widgets):
                    widget = self.editor_tab.alternatives_widgets[i]
                    texto = alt.get('texto', '') if isinstance(alt, dict) else ''
                    correta = alt.get('correta', False) if isinstance(alt, dict) else False
                    widget.text_input.setText(texto)
                    if correta:
                        widget.radio_button.setChecked(True)

        # Resposta discursiva
        resposta = questao_data.get('resposta', {})
        if resposta and resposta.get('gabarito_discursivo'):
            self.editor_tab.answer_key_input.setPlainText(resposta.get('gabarito_discursivo', ''))

        # Tags - extrair UUIDs das tags
        tags = questao_data.get('tags', [])
        tag_uuids = []
        for tag in tags:
            if isinstance(tag, dict):
                uuid = tag.get('uuid')
                if uuid:
                    tag_uuids.append(uuid)
            elif isinstance(tag, str):
                tag_uuids.append(tag)

        if tag_uuids:
            self.tags_tab.set_selected_tags(tag_uuids)
            self.question_data['tags'] = tag_uuids

        # Se é variante, desabilitar campos herdados
        if self.is_variant:
            self._disable_inherited_fields()

        # Atualizar dados internos
        self._update_question_data()
        self._update_save_button_state()

    def _disable_inherited_fields(self):
        """Desabilita campos herdados quando editando/criando variante."""
        # Ano
        self.editor_tab.academic_year_input.setEnabled(False)
        self.editor_tab.academic_year_input.setStyleSheet("background-color: #e9ecef; color: #6c757d;")

        # Fonte/Origem
        self.editor_tab.origin_input.setEnabled(False)
        self.editor_tab.origin_input.setStyleSheet("background-color: #e9ecef; color: #6c757d;")

        # Nível escolar
        self.editor_tab.school_level_combo.setEnabled(False)
        self.editor_tab.school_level_combo.setStyleSheet("background-color: #e9ecef; color: #6c757d;")

        # Tipo de questão
        self.editor_tab.objective_radio.setEnabled(False)
        self.editor_tab.discursive_radio.setEnabled(False)

        # Dificuldade
        self.editor_tab.difficulty_easy.setEnabled(False)
        self.editor_tab.difficulty_medium.setEnabled(False)
        self.editor_tab.difficulty_hard.setEnabled(False)

        # Tags
        self.tags_tab.setEnabled(False)

    def clear_form(self):
        """Limpa o formulário para criação de nova questão."""
        self.is_editing = False
        self.editing_question_id = None
        self.is_variant = False
        self.original_data = None
        self.original_codigo = None
        self.title_label.setText("MathBank / Criar Questão")
        self.question_data = {}

        # Reabilitar campos que podem ter sido desabilitados no modo variante
        self.editor_tab.academic_year_input.setEnabled(True)
        self.editor_tab.academic_year_input.setStyleSheet("")
        self.editor_tab.origin_input.setEnabled(True)
        self.editor_tab.origin_input.setStyleSheet("")
        self.editor_tab.school_level_combo.setEnabled(True)
        self.editor_tab.school_level_combo.setStyleSheet("")
        self.editor_tab.objective_radio.setEnabled(True)
        self.editor_tab.discursive_radio.setEnabled(True)
        self.editor_tab.difficulty_easy.setEnabled(True)
        self.editor_tab.difficulty_medium.setEnabled(True)
        self.editor_tab.difficulty_hard.setEnabled(True)
        self.tags_tab.setEnabled(True)

        # Limpar campos do editor
        self.editor_tab.academic_year_input.clear()
        self.editor_tab.origin_input.clear()
        self.editor_tab.statement_input.clear()
        self.editor_tab.answer_key_input.clear()

        # Resetar nível escolar
        self.editor_tab.school_level_combo.setCurrentIndex(0)

        # Resetar tipo para objetiva
        self.editor_tab.objective_radio.setChecked(True)
        self.editor_tab.current_question_type = "objective"
        self.editor_tab._update_visibility_by_question_type()

        # Limpar dificuldade
        self.editor_tab.difficulty_group.setExclusive(False)
        self.editor_tab.difficulty_easy.setChecked(False)
        self.editor_tab.difficulty_medium.setChecked(False)
        self.editor_tab.difficulty_hard.setChecked(False)
        self.editor_tab.difficulty_group.setExclusive(True)

        # Limpar alternativas
        for widget in self.editor_tab.alternatives_widgets:
            widget.text_input.clear()
            widget.radio_button.setChecked(False)

        # Limpar tags
        self.tags_tab.clear_selection()

        # Atualizar estado do botão salvar
        self._update_save_button_state()

    def load_question_for_variant(self, questao_data: dict):
        """Carrega dados de uma questão para criar variante."""
        self.is_variant = True
        self.is_editing = False
        self.editing_question_id = None
        self.original_data = questao_data
        self.original_codigo = questao_data.get('codigo') or questao_data.get('id')
        self.title_label.setText(f"MathBank / Criar Variante de {self.original_codigo}")

        # Preencher campos herdados
        self.editor_tab.academic_year_input.setText(str(questao_data.get('ano', '')))
        self.editor_tab.origin_input.setText(questao_data.get('fonte', '') or '')

        # Carregar nível escolar
        niveis = questao_data.get('niveis_escolares', [])
        if niveis:
            nivel = niveis[0] if isinstance(niveis, list) else niveis
            nivel_uuid = nivel.get('uuid') if isinstance(nivel, dict) else nivel
            self.editor_tab.set_school_level_by_uuid(nivel_uuid)

        # Tipo de questão
        tipo = questao_data.get('tipo', 'OBJETIVA')
        if tipo == 'OBJETIVA':
            self.editor_tab.objective_radio.setChecked(True)
            self.editor_tab.current_question_type = "objective"
        else:
            self.editor_tab.discursive_radio.setChecked(True)
            self.editor_tab.current_question_type = "discursive"
        self.editor_tab._update_visibility_by_question_type()

        # Dificuldade
        dificuldade = questao_data.get('dificuldade', '')
        if dificuldade:
            dif_map = {'FACIL': 1, 'MEDIO': 2, 'DIFICIL': 3}
            dif_id = dif_map.get(dificuldade.upper(), 0)
            if dif_id == 1:
                self.editor_tab.difficulty_easy.setChecked(True)
            elif dif_id == 2:
                self.editor_tab.difficulty_medium.setChecked(True)
            elif dif_id == 3:
                self.editor_tab.difficulty_hard.setChecked(True)

        # Campos EDITÁVEIS - pré-preencher com dados da original
        # Enunciado
        self.editor_tab.statement_input.setPlainText(questao_data.get('enunciado', '') or '')

        # Alternativas (se objetiva) - EDITÁVEIS
        if tipo == 'OBJETIVA':
            alternativas = questao_data.get('alternativas', [])
            for i, alt in enumerate(alternativas):
                if i < len(self.editor_tab.alternatives_widgets):
                    widget = self.editor_tab.alternatives_widgets[i]
                    texto = alt.get('texto', '') if isinstance(alt, dict) else ''
                    correta = alt.get('correta', False) if isinstance(alt, dict) else False
                    widget.text_input.setText(texto)
                    if correta:
                        widget.radio_button.setChecked(True)

        # Resposta discursiva - EDITÁVEL
        resposta = questao_data.get('resposta', {})
        if resposta and resposta.get('gabarito_discursivo'):
            self.editor_tab.answer_key_input.setPlainText(resposta.get('gabarito_discursivo', ''))

        # Tags - herdadas (NÃO editáveis)
        tags = questao_data.get('tags', [])
        tag_uuids = []
        for tag in tags:
            if isinstance(tag, dict):
                uuid = tag.get('uuid')
                if uuid:
                    tag_uuids.append(uuid)
            elif isinstance(tag, str):
                tag_uuids.append(tag)

        if tag_uuids:
            self.tags_tab.set_selected_tags(tag_uuids)
            self.question_data['tags'] = tag_uuids

        # Desabilitar campos herdados
        self._disable_inherited_fields()

        # Atualizar dados internos
        self._update_question_data()
        self._update_save_button_state()


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