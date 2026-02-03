"""
Page: Questão Preview
Janela modal de visualização da questão no formato PDF
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
import logging
import re
import os

from src.utils import ErrorHandler

logger = logging.getLogger(__name__)


class QuestaoPreview(QDialog):
    """Janela de preview da questão no formato PDF"""
    edit_requested = pyqtSignal(object)  # Emite questao_data quando editar é clicado
    create_variant_requested = pyqtSignal(object)  # Emite questao_data para criar variante

    def __init__(self, questao_data, parent=None):
        super().__init__(parent)
        self.questao_data = questao_data
        self.setWindowTitle("Preview - Formato PDF")
        self.setMinimumSize(850, 650)
        self.resize(900, 750)

        # Carregar informações de variantes
        self._load_variant_info()

        try:
            self.init_ui()
            logger.info(f"QuestaoPreview inicializado (ID: {questao_data.get('id')})")
        except Exception as e:
            ErrorHandler.handle_exception(
                self,
                e,
                "Erro ao carregar preview"
            )
            self.close()

    def _load_variant_info(self):
        """Carrega informações sobre variantes da questão."""
        from src.controllers.questao_controller_orm import QuestaoControllerORM

        codigo = self.questao_data.get('codigo') or self.questao_data.get('id')
        if not codigo:
            self.is_variant = False
            self.original_question = None
            self.variants = []
            self.variant_count = 0
            return

        # Verificar se é variante
        self.is_variant = QuestaoControllerORM.eh_variante(codigo)

        if self.is_variant:
            # Buscar questão original
            self.original_question = QuestaoControllerORM.obter_questao_original(codigo)
            self.variants = []
            self.variant_count = 0
        else:
            # Buscar variantes desta questão
            self.original_question = None
            self.variants = QuestaoControllerORM.listar_variantes(codigo)
            self.variant_count = len(self.variants)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header com info do preview
        header_widget = QFrame(self)
        header_widget.setFixedHeight(30)
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        header_label = QLabel("Preview - Visualização no formato PDF")
        header_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #555; background: transparent;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Badge de tipo
        tipo = self.questao_data.get('tipo', 'N/A')
        tipo_label = QLabel(tipo)
        tipo_label.setFixedSize(80, 22)
        color = "#2196f3" if tipo == 'OBJETIVA' else "#9c27b0"
        tipo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        header_layout.addWidget(tipo_label)
        layout.addWidget(header_widget)

        # Indicador se é variante de outra questão
        if self.is_variant and self.original_question:
            variant_banner = QFrame(self)
            variant_banner.setStyleSheet("""
                QFrame {
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            variant_banner_layout = QHBoxLayout(variant_banner)
            variant_banner_layout.setContentsMargins(10, 5, 10, 5)
            variant_icon = QLabel("📋")
            variant_banner_layout.addWidget(variant_icon)
            original_codigo = self.original_question.get('codigo', 'N/A')
            variant_info = QLabel(f"Esta é uma <b>variante</b> da questão <b>{original_codigo}</b>")
            variant_info.setStyleSheet("color: #856404; font-size: 12px;")
            variant_banner_layout.addWidget(variant_info)
            variant_banner_layout.addStretch()
            layout.addWidget(variant_banner)

        # Área de preview usando QWebEngineView
        self.web_view = QWebEngineView(self)
        self.web_view.setMinimumHeight(400)
        self.web_view.setStyleSheet("border: 1px solid #ccc; background-color: white;")

        # Gerar HTML da questão
        html_content = self._gerar_html_questao()
        self.web_view.setHtml(html_content)

        layout.addWidget(self.web_view, 1)  # stretch factor 1

        # Seção de variantes (se não for variante e tiver variantes ou puder criar)
        if not self.is_variant:
            variants_frame = QFrame(self)
            variants_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
            """)
            variants_layout = QVBoxLayout(variants_frame)
            variants_layout.setContentsMargins(10, 10, 10, 10)
            variants_layout.setSpacing(8)

            # Título da seção
            variants_header = QHBoxLayout()
            variants_title = QLabel(f"📋 Variantes desta questão ({self.variant_count}/3)")
            variants_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #495057;")
            variants_header.addWidget(variants_title)
            variants_header.addStretch()
            variants_layout.addLayout(variants_header)

            # Lista de variantes existentes
            if self.variants:
                for idx, variant in enumerate(self.variants, start=1):
                    variant_row = QHBoxLayout()
                    variant_codigo = variant.get('codigo') or 'N/A'
                    variant_label = QLabel(f"• <b>{variant_codigo}</b> - Variante {idx}")
                    variant_label.setStyleSheet("color: #495057; font-size: 11px;")
                    variant_row.addWidget(variant_label)
                    variant_row.addStretch()

                    # Botão Ver variante
                    btn_view_variant = QPushButton("Ver")
                    btn_view_variant.setFixedSize(50, 22)
                    btn_view_variant.setStyleSheet("""
                        QPushButton {
                            background-color: #6c757d;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            font-size: 10px;
                        }
                        QPushButton:hover {
                            background-color: #5a6268;
                        }
                    """)
                    btn_view_variant.clicked.connect(lambda checked, c=variant_codigo: self._on_view_variant(c))
                    variant_row.addWidget(btn_view_variant)
                    variants_layout.addLayout(variant_row)
            else:
                no_variants_label = QLabel("Nenhuma variante criada ainda.")
                no_variants_label.setStyleSheet("color: #6c757d; font-size: 11px; font-style: italic;")
                variants_layout.addWidget(no_variants_label)

            layout.addWidget(variants_frame)

        # Botões
        btn_frame = QFrame(self)
        btn_frame.setFixedHeight(45)
        btn_frame.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 5, 0, 5)
        btn_layout.addStretch()

        # Botão Criar Variante (somente se NÃO for variante e tiver menos de 3 variantes)
        if not self.is_variant and self.variant_count < 3:
            btn_create_variant = QPushButton("+ Criar Variante")
            btn_create_variant.setFixedSize(130, 35)
            btn_create_variant.setStyleSheet("""
                QPushButton {
                    padding: 8px 20px;
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            btn_create_variant.clicked.connect(self._on_create_variant_clicked)
            btn_layout.addWidget(btn_create_variant)

        btn_edit = QPushButton("Editar Questão")
        btn_edit.setFixedSize(130, 35)
        btn_edit.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_edit.clicked.connect(self._on_edit_clicked)
        btn_layout.addWidget(btn_edit)

        btn_close = QPushButton("Fechar")
        btn_close.setFixedSize(100, 35)
        btn_close.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addWidget(btn_frame)

    def _gerar_html_questao(self) -> str:
        """Gera HTML completo da questão para renderização."""
        tipo = self.questao_data.get('tipo', 'N/A')
        fonte = self.questao_data.get('fonte') or ''
        ano = self.questao_data.get('ano') or ''
        enunciado = self.questao_data.get('enunciado', '')

        # Processar enunciado
        enunciado_html = self._formatar_texto(enunciado)

        # Cabeçalho da questão
        questao_header = "1."
        if fonte and ano:
            questao_header += f" <b>({fonte} - {ano})</b>"
        elif fonte:
            questao_header += f" <b>({fonte})</b>"
        elif ano:
            questao_header += f" <b>({ano})</b>"

        # Construir HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{
    font-family: 'Times New Roman', serif;
    font-size: 14px;
    padding: 30px 40px;
    margin: 0;
    color: #333;
    background-color: white;
}}
.header {{ margin-bottom: 10px; }}
.enunciado {{ margin-bottom: 15px; line-height: 1.5; }}
table {{
    border-collapse: collapse;
    margin: 8px auto;
    width: 80%;
}}
td, th {{
    border: 1px solid #333;
    padding: 2px 6px;
    text-align: center;
    font-size: 11px;
    line-height: 1.2;
}}
th {{
    background-color: #e0e0e0;
    font-weight: bold;
}}
ul, ol {{
    margin: 5px 0;
    padding-left: 25px;
}}
li {{
    margin: 2px 0;
}}
.alternativas {{
    margin-top: 15px;
}}
.alternativa {{
    margin: 5px 0 5px 20px;
    line-height: 1.4;
}}
.alternativa-correta {{
    color: green;
}}
.tags {{
    margin-top: 20px;
    font-size: 12px;
    color: #666;
}}
.tag {{
    display: inline-block;
    background-color: #e8e8e8;
    color: #555;
    padding: 2px 8px;
    border-radius: 2px;
    margin-right: 5px;
    font-size: 10px;
}}
.resolucao {{
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #ccc;
}}
</style>
</head>
<body>
<div class="header">{questao_header}</div>
<div class="enunciado">{enunciado_html}</div>
"""

        # Alternativas (se objetiva)
        if tipo == 'OBJETIVA' and 'alternativas' in self.questao_data:
            html += '<div class="alternativas">'
            for alt in self.questao_data['alternativas']:
                letra = alt.get('letra', '')
                texto = alt.get('texto', '')
                correta = alt.get('correta', False)

                texto_html = self._formatar_texto(texto)

                if correta:
                    html += f'<div class="alternativa alternativa-correta"><b>{letra})</b> {texto_html} ✓</div>'
                else:
                    html += f'<div class="alternativa"><b>{letra})</b> {texto_html}</div>'
            html += '</div>'

        # Resolução (se houver)
        resolucao = self.questao_data.get('resolucao')
        if resolucao and resolucao.strip():
            resolucao_html = self._formatar_texto(resolucao)
            html += f'<div class="resolucao"><b>Resolução:</b><br>{resolucao_html}</div>'

        # Tags
        tags = self.questao_data.get('tags', [])
        if tags:
            html += '<div class="tags"><i>Tags:</i> '
            for tag in tags:
                tag_nome = tag.get('nome') if isinstance(tag, dict) else tag
                html += f'<span class="tag">{tag_nome}</span>'
            html += '</div>'

        html += '</body></html>'
        return html

    def _formatar_texto(self, texto: str) -> str:
        """Formata texto com suporte a tabelas, listas e formatações."""
        if not texto:
            return ""

        # Processar tabelas
        texto = self._processar_tabelas_para_html(texto)

        # Processar listas
        texto = self._processar_listas_para_html(texto)

        # Processar imagens
        texto = self._processar_imagens(texto)

        # Formatações de texto
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

        # Converter múltiplas quebras de linha em uma única <br>
        texto = re.sub(r'\n{2,}', '<br><br>', texto)
        texto = texto.replace('\n', '<br>')

        # Remover <br> redundantes ao redor de tabelas
        texto = re.sub(r'(<br>)+(<table)', r'\2', texto)
        texto = re.sub(r'(</table>)(<br>)+', r'\1', texto)

        return texto

    def _processar_imagens(self, texto: str) -> str:
        """Processa placeholders de imagem [IMG:caminho:escala]."""
        pattern = r'\[IMG:(.+?):([0-9.]+)\]'

        def replace_image(match):
            caminho = match.group(1)
            escala = float(match.group(2))
            if os.path.exists(caminho):
                # Converter para file:// URL
                caminho_url = caminho.replace('\\', '/')
                width = int(400 * escala)
                return f'<br><img src="file:///{caminho_url}" style="max-width:{width}px; display:block; margin:10px auto;"><br>'
            return ''

        return re.sub(pattern, replace_image, texto)

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

            html_lines = ['<table>']

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
                    cell_html = self._processar_formatacao_celula(cell)
                    if is_header:
                        html_lines.append(f'<th>{cell_html}</th>')
                    else:
                        html_lines.append(f'<td>{cell_html}</td>')
                html_lines.append('</tr>')

            html_lines.append('</table>')
            return ''.join(html_lines)

        return table_pattern.sub(convert_table, texto)

    def _processar_formatacao_celula(self, cell_text: str) -> str:
        """Processa formatações de uma célula de tabela."""
        result = cell_text

        # Processar cor de fundo
        color_pattern = re.compile(r'\[COR:#([a-fA-F0-9]{6})\](.*?)\[/COR\]', re.DOTALL)
        color_match = color_pattern.search(result)
        if color_match:
            cell_color = color_match.group(1)
            inner_text = color_match.group(2)
            result = f'<span style="background-color:#{cell_color};">{inner_text}</span>'
            result = color_pattern.sub(result, cell_text)

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
                    result.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                result.append(f'<li>{itemize_match.group(2)}</li>')
                continue

            arabic_match = arabic_pattern.match(line)
            if arabic_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li>{arabic_match.group(2)}</li>')
                continue

            alpha_lower_match = alpha_lower_pattern.match(line)
            if alpha_lower_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="list-style-type:lower-alpha;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li>{alpha_lower_match.group(2)}</li>')
                continue

            alpha_upper_match = alpha_upper_pattern.match(line)
            if alpha_upper_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="list-style-type:upper-alpha;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li>{alpha_upper_match.group(2)}</li>')
                continue

            roman_lower_match = roman_lower_pattern.match(line)
            if roman_lower_match and roman_lower_match.group(1).islower():
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="list-style-type:lower-roman;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li>{roman_lower_match.group(2)}</li>')
                continue

            roman_upper_match = roman_upper_pattern.match(line)
            if roman_upper_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    result.append('<ol style="list-style-type:upper-roman;">')
                    in_list = True
                    list_type = 'ol'
                result.append(f'<li>{roman_upper_match.group(2)}</li>')
                continue

            if line.strip() and in_list:
                close_list()

            result.append(line)

        close_list()
        # Juntar sem newlines para evitar <br> extras
        return ''.join(result)

    def _on_edit_clicked(self):
        """Handler para botão de editar."""
        self.edit_requested.emit(self.questao_data)
        self.accept()

    def _on_create_variant_clicked(self):
        """Handler para botão de criar variante."""
        self.create_variant_requested.emit(self.questao_data)
        self.accept()

    def _on_view_variant(self, codigo: str):
        """Handler para ver uma variante."""
        from src.controllers.questao_controller_orm import QuestaoControllerORM

        # Buscar dados completos da variante
        variant_data = QuestaoControllerORM.buscar_questao(codigo)
        if variant_data:
            # Formatar dados para preview
            formatted_data = {
                'id': variant_data.get('codigo'),
                'codigo': variant_data.get('codigo'),
                'uuid': variant_data.get('uuid'),
                'titulo': variant_data.get('titulo'),
                'tipo': variant_data.get('tipo'),
                'enunciado': variant_data.get('enunciado', ''),
                'ano': variant_data.get('ano'),
                'fonte': variant_data.get('fonte'),
                'dificuldade': variant_data.get('dificuldade'),
                'observacoes': variant_data.get('observacoes'),
                'alternativas': variant_data.get('alternativas', []),
                'tags': variant_data.get('tags', []),
            }

            # Extrair resolução do resposta dict
            resposta = variant_data.get('resposta')
            if resposta:
                if resposta.get('resolucao'):
                    formatted_data['resolucao'] = resposta.get('resolucao')
                elif resposta.get('gabarito_discursivo'):
                    formatted_data['resolucao'] = resposta.get('gabarito_discursivo')

            # Abrir preview da variante em nova janela
            variant_preview = QuestaoPreview(formatted_data, parent=self.parent())
            variant_preview.edit_requested.connect(self._forward_edit_request)
            variant_preview.create_variant_requested.connect(self._forward_create_variant_request)
            self.accept()  # Fechar este preview
            variant_preview.exec()

    def _forward_edit_request(self, questao_data):
        """Reencaminha requisição de edição."""
        self.edit_requested.emit(questao_data)

    def _forward_create_variant_request(self, questao_data):
        """Reencaminha requisição de criar variante."""
        self.create_variant_requested.emit(questao_data)


logger.info("QuestaoPreview carregado")
